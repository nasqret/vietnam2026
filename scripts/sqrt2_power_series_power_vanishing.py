"""CV005: construct actual power tables and prove vanishing below the exponent.

The input zero-order-one premise is separate from power execution. An ordinary
HA induction applies the actual universal antidiagonal vanishing proof to each
executed convolution. No vanishing property is part of NatPowerTrace. This
justifies finite coefficient support in the power index, not exp/log limits.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_series_power_trace import (
    ROOT,P,B,U,Scope,introduce,eliminate,witness,field,apply,specialize,
    canonical,json_hash,_inert_metrics,named,forall,exists,row,trace,
    definition_registry as power_registry,series_power_trace_source_pins,
    CONVOLUTION_ARCHIVE,CONVOLUTION_ANCESTORS,read_archive,
)

SCHEMA = "sqrt2-power-series-power-vanishing-v1"
V = ("vb","vc")
W = ("wb","wc")
DEFINITION_SOURCE = "forall i a. Lt(i,k) -> BetaZeroExtend(b,c,L,i,a) -> a=0"
DEFINITION_SHA256 = "a73a162e36dfe5372fcd31c30305a99cc4d4472218ce6d3e4669c75048b70dae"
INPUT_ZERO = "NatZeroBefore(ab,ac,L,1)"
VANISHING_SOURCE = forall(P+B,INPUT_ZERO+" -> "+forall(("k","K")+U,
    trace(B,"K")+" -> Le(k,K) -> "+row(B,"k",U)+" -> NatZeroBefore(ub,uc,H,k)"))
VANISHING_SHA256 = "777389241e6c413f59c2e215f74c439a42f84ceaa7514e9b4ca90a6db3ce9980"
NAMED_SOURCE = forall(P+("K",),INPUT_ZERO+" -> "+exists(B,
    trace(B,"K")+" /\\ ("+forall(("k",)+U,"Le(k,K) -> "+row(B,"k",U)+" -> NatZeroBefore(ub,uc,H,k)")+")"))
TARGET_SHA256 = "db647ab11de25c9cae8ffd94e24655fd15cc955113f9e4a7f12ee383e21e224d"
POWER_ARCHIVE = dict(case="CV004",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-series-power-trace-v2/generation-process.json.gz",
    bytes=22358,sha256="0c0cae4c78b8caf790b913bd729a222446ea33725bdc75374924451ff67f6966",
    raw_bytes=408553,raw_sha256="1bfa09555974b7c1fe0a71f8b4f53991e61610374874a487d171053ffa3976be",
    bundle_bytes=246245,bundle_sha256="2d6398dce2762252fbd18ade9897b03bd7b4d6c5502424ccb3f734712e9e789d",
    nodes=121,root=120,target_ast_sha256="d39fa99bbfda29fc077a02cf8d23cc3a5d36c8f829bb9b76988a537042145777")
VANISHING_ARCHIVE = dict(case="CV001",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-vanishing-v3/generation-process.json.gz",
    bytes=9622,sha256="555071d9f8c3c30a7c37aa078fbf6fe0ff49de7bf972c1ca880e0fdcf6e248d7",
    raw_bytes=110174,raw_sha256="dfcd706134bfd9af4a29e140d7a8145e6afce52bab5b2d3cd83f58d3105861f2",
    bundle_bytes=58402,bundle_sha256="93d3871e7c7f06fc5974b61bec48616a7a7f13e6f919bf7dbf34570624e918b6",
    nodes=28,root=27,target_ast_sha256="b5ca16c60cf9aff317a93603448843e717d17228380fb7c1a1287e31f12e5e22")
ARITHMETIC_ENDPOINTS = {
    "zero_add":(0,"forall a. 0+a=a"),
    "add_succ_left":(1,"forall a b. (S a)+b=S(a+b)"),
    "le_refl":(13,"forall a. Le(a,a)"),
    "le_trans":(14,"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)"),
    "zero_le":(24,"forall a. Le(0,a)"),
    "le_succ":(34,"forall a b. Le(a,b) -> Le(a,S b)"),
    "lt_not_le":(40,"forall a b. Lt(a,b) -> Le(b,a) -> false"),
    "beta_at_unique":(88,"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d"),
}
VANISHING_DEPENDENCIES = tuple(ARITHMETIC_ENDPOINTS)+("prefix_entry","CV001")
ROOT_DEPENDENCIES = ("CV004","vanishing")


class PowerVanishingError(ValueError):
    """Changed exact assertion, conservative alias, actual proof bytes or cap."""


def definition_registry():
    import json
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(power_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    name,identifier,parameters = "NatZeroBefore","ND0408",("b","c","L","k")
    if any(d["id"]==identifier or d["name"]==name for d in parent) or name in registry or identifier in {d.stable_id for d in registry.values()}:
        raise PowerVanishingError("local zero-prefix alias collides with an existing definition")
    formula = parse_named(DEFINITION_SOURCE,parameters,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise PowerVanishingError("zero-prefix exact expansion changed")
    text = pretty_formula(formula,list(parameters))
    d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
        summary="All zero-extended entries below k vanish; separate from the execution relation.",
        category="irrationality_formal_series",conceptual_dependencies=("Lt","BetaZeroExtend"))
    if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
        raise PowerVanishingError("zero-prefix expansion failed exact roundtrip")
    registry[name] = d
    return MappingProxyType(registry)


def frozen_series_power_vanishing_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PowerVanishingError("CV005 exact zero-order power construction target changed")
    return target


def source_contract():
    return dict(code="CV005",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,input_vanishes_below_one_required=True,output_trace_supplied=False,
        arbitrary_exponent_and_width=True,all_rows_through_requested_exponent=True,
        all_padded_coefficients_below_exponent_zero=True,execution_contains_vanishing=False,
        new_definition_ids=["ND0408"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",rational_coefficients=False,
        formal_derivative=False,exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def series_power_vanishing_source_pins():
    result = series_power_trace_source_pins()
    expected = {"scripts/sqrt2_power_series_power_trace.py":"557d393791fb527361bcffb4977b0e0bad591f98a426e12d1da461643cc39422",
        POWER_ARCHIVE["path"]:POWER_ARCHIVE["sha256"],VANISHING_ARCHIVE["path"]:VANISHING_ARCHIVE["sha256"]}
    for name in (*expected,"scripts/sqrt2_power_series_power_vanishing.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PowerVanishingError("power-vanishing source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _vanishing_body(target,registry):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import (AndElimL,AndElimR,BotElim,CongS,EqSubst,EqSym,EqTrans,Ind,OrElim)
    from peano_lab.kernel.terms import Succ,Zero
    def base(s):
        return BotElim(apply(specialize(s,"lt_not_le",s.term("i"),Zero()),
            s.hyp("index"),specialize(s,"zero_le",s.term("i"))))
    def step(s):
        def inside(t):
            def decoded(u):
                k,K = u.terms(("k","K"))
                current = field(u.hyp("step"),1,3)
                equations = tuple(apply(specialize(u,"beta_at_unique",*u.terms(B[2*j:2*j+2]),Succ(k),u.term(U[j]),u.term(W[j])),
                    field(u.hyp("row"),j,2),field(current,j,2)) for j in range(2))
                motive = parse_named("BetaAt(code_slot,uc,i,a)",u.variable("code_slot").variables,registry)
                decoded_entry = EqSubst(motive,equations[0],AndElimR(u.hyp("inside")))
                motive = parse_named("BetaAt(wb,scale_slot,i,a)",u.variable("scale_slot").variables,registry)
                decoded_entry = EqSubst(motive,equations[1],decoded_entry)
                coefficient = apply(specialize(u,"prefix_entry",*u.terms(("ab","ac","L")),*u.terms(V),u.term("H"),
                    *u.terms(W),u.term("H"),*u.terms(("i","a"))),
                    field(u.hyp("step"),2,3),AndElimL(u.hyp("inside")),decoded_entry)
                def summed(v):
                    k,K = v.terms(("k","K"))
                    previous_bound = apply(specialize(v,"le_trans",k,Succ(k),K),
                        apply(specialize(v,"le_succ",k,k),specialize(v,"le_refl",k)),v.hyp("bound"))
                    previous_zero = apply(specialize(v,"IH",v.term("K"),*v.terms(V)),
                        v.hyp("trace"),previous_bound,field(v.hyp("step"),0,3))
                    one_add = EqTrans(specialize(v,"add_succ_left",Zero(),k),CongS(specialize(v,"zero_add",k)))
                    motive = parse_named("Lt(i,bound_slot)",v.variable("bound_slot").variables,registry)
                    index = EqSubst(motive,EqSym(one_add),v.hyp("index"))
                    return apply(specialize(v,"CV001",*v.terms(("ab","ac","L")),*v.terms(V),v.term("H"),
                        Succ(Zero()),k,v.term("i"),*v.terms(("db","dc","a"))),
                        v.hyp("zero"),previous_zero,index,AndElimL(v.hyp("sum")),AndElimR(v.hyp("sum")))
                return eliminate(u,coefficient,("db","dc"),"sum",summed)
            actual_step = apply(instantiate(AndElimR(t.hyp("trace")),t.term("k")),t.hyp("bound"))
            return eliminate(t,actual_step,V+W,"step",decoded)
        return OrElim(s.hyp("padded"),inside(s.hypothesis("inside")),AndElimR(s.hypothesis("outside").hyp("outside")))
    motive = target
    for _ in range(8):
        motive = motive.body
    motive = motive.right.body
    def induction(s):
        def parameters(t,finish):
            return introduce(t,("K",)+U,("trace","bound","row"),lambda u:
                introduce(u,("i","a"),("index","padded"),finish))
        base_proof = parameters(s,base)
        step_proof = introduce(s,("k",),("IH",),lambda t:parameters(t,step))
        return Ind(motive,base_proof,step_proof)
    return introduce(Scope(),(),VANISHING_DEPENDENCIES,lambda s:
        introduce(s,P+B,("zero",),induction))


def _root_body():
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro
    def chosen(s):
        def all_rows(t):
            proof = apply(specialize(t,"vanishing",*t.terms(P+B)),t.hyp("zero"))
            return apply(instantiate(proof,*t.terms(("k","K")+U)),t.hyp("trace"),t.hyp("bound"),t.hyp("row"))
        all_rows_proof = introduce(s,("k",)+U,("bound","row"),all_rows)
        return witness(s.terms(B),AndIntro(s.hyp("trace"),all_rows_proof))
    return introduce(Scope(),(),ROOT_DEPENDENCIES,lambda s:
        introduce(s,P+("K",),("zero",),lambda t:
            eliminate(t,specialize(t,"CV004",*t.terms(P+("K",))),B,"trace",chosen)))


@dataclass(frozen=True)
class SeriesPowerVanishingCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_series_power_vanishing(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from sqrt2_power_convolution_vanishing import frozen_convolution_vanishing_target
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise PowerVanishingError("expected unchanged BinaryDAGLimits")
    before = series_power_vanishing_source_pins()
    registry,target = definition_registry(),frozen_series_power_vanishing_target()
    vanishing = parse_named(VANISHING_SOURCE,registry=registry)
    if json_hash(encode_formula(vanishing))!=VANISHING_SHA256:
        raise PowerVanishingError("all-indices power vanishing invariant changed")
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    for pin in (CONVOLUTION_ARCHIVE,POWER_ARCHIVE,VANISHING_ARCHIVE):
        old_rows = read_archive(pin)
        remap = {}
        for old,r in enumerate(old_rows):
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise PowerVanishingError("actual archive ordered dependency mismatch")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if type(r[0]) is not int or r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise PowerVanishingError("merged actual archive body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        endpoints[pin["case"]] = remap[pin["root"]]
        if pin["case"]=="CV003":
            for name,(old,source) in ARITHMETIC_ENDPOINTS.items():
                local = CONVOLUTION_ANCESTORS.index(old)
                if old_rows[local][1]!=encode_formula(parse_named(source,registry=registry)):
                    raise PowerVanishingError("actual arithmetic differs from independently frozen source")
                endpoints[name] = remap[local]
            endpoints["prefix_entry"] = remap[122]
            expected = "forall ab ac L bb bc M cb cc N i a. NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N) -> Lt(i,N) -> BetaAt(cb,cc,i,a) -> NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,a)"
            if old_rows[122][1]!=encode_formula(parse_named(expected,registry=registry)):
                raise PowerVanishingError("actual convolution entry theorem changed")
        if pin["case"]=="CV001" and old_rows[pin["root"]][1]!=encode_formula(frozen_convolution_vanishing_target()):
            raise PowerVanishingError("actual antidiagonal vanishing theorem changed")
        del old_rows,remap
        gc.collect()
    ancestor_count = len(rows)
    for name,formula,dependencies,body in (
        ("vanishing",vanishing,VANISHING_DEPENDENCIES,_vanishing_body(vanishing,registry)),
        ("CV005",target,ROOT_DEPENDENCIES,_root_body()),
    ):
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise PowerVanishingError("power-vanishing aggregate ordinary-body/node bound exceeded")
        _row_preflight(formula,body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formula),[endpoints[d] for d in dependencies],encode_proof(body)])
    reachable,pending = set(),[len(rows)-1]
    while pending:
        old = pending.pop()
        if old not in reachable:
            reachable.add(old)
            pending.extend(rows[old][2])
    retained = tuple(sorted(reachable))
    remap = {old:new for new,old in enumerate(retained)}
    ancestors = tuple(old for old in retained if old<ancestor_count)
    ancestor_total = sum(_inert_metrics(rows[old][3],limits)[0] for old in ancestors)
    rows = [[rows[old][0],rows[old][1],[remap[d] for d in rows[old][2]],rows[old][3]] for old in retained]
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise PowerVanishingError("power-vanishing canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise PowerVanishingError("decoded power-vanishing target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or series_power_vanishing_source_pins()!=before:
        raise PowerVanishingError("power-vanishing target or source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,actual_power_rows_constructed=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        power_archive=dict(POWER_ARCHIVE),convolution_archive=dict(CONVOLUTION_ARCHIVE),vanishing_archive=dict(VANISHING_ARCHIVE),
        invariant_statement_ast_sha256=VANISHING_SHA256,new_induction_count=1,
        ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,new_axioms=[],
        external_certificate_references=[],independent_lean_checked=False)
    return SeriesPowerVanishingCertificate(target,bundle,payload,receipt,deepest,provenance)
