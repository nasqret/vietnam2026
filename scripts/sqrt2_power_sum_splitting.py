"""CV009: construct exact prefix, tail and whole sums, and prove splitting.

An internal all-strides lemma splits an actual affine sum at an arbitrary
natural length. The root specializes it to an ordinary beta prefix and its
genuine shifted tail. No splitting law is included in the definitions.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256

from sqrt2_power_natural_fubini import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,_inert_metrics,read_archive,definition_registry,
    natural_fubini_source_pins,HELPER_SOURCES as FUBINI_HELPERS,_subst,
)

SCHEMA = "sqrt2-power-sum-splitting-v1"
FUBINI_ARCHIVE = dict(case="CV008",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-natural-fubini-v1/generation-process.json.gz",
    bytes=25252,sha256="cf167b60b4b98cc0ca3ddd91e6b393e97b0a971b3c2fcac7dac8420adc4a14d5",
    raw_bytes=502316,raw_sha256="6435967f6240e0641577a241002f4828c3c00aa2dd75ec1f4fac71242ab52b50",
    bundle_bytes=303172,bundle_sha256="ee2157fd318e4de4909bf579ec1f3bae6efe8a8d4b56e9b75e938df87d5c2450",
    nodes=126,root=125,target_ast_sha256="144c71f1f4627b2ab6b53db389f1fc57d00868e5daf3716c01c6858aa379fec7")
NAMED_SOURCE = (
    "forall ab ac m n. exists x y z. Sum(ab,ac,m,x) /\\ (NatAffineSum(ab,ac,m,1,n,y) /\\ "
    "(Sum(ab,ac,m+n,z) /\\ z=x+y))"
)
TARGET_SHA256 = "2aa07f3f9d93b14be669dd9bcca9eb51364030fe16587b130f508419e396c462"
HELPER_SOURCES = {
    "raw_as_affine":"forall ab ac L x. Sum(ab,ac,L,x) -> NatAffineSum(ab,ac,0,1,L,x)",
    "concatenate":"forall n ab ac o t m x y z. NatAffineSum(ab,ac,o,t,m,x) -> "
        "NatAffineSum(ab,ac,o+t*m,t,n,y) -> NatAffineSum(ab,ac,o,t,m+n,z) -> z=x+y",
}
HELPER_TARGET_SHA256 = {
    "raw_as_affine":"15b863a118c762454a6b1eb758eba28b3ab681aafa0a76876b1b7e4e90647332",
    "concatenate":"0c4bc3a279beafd601157c6b90b0b1be74897362af0b038bf39ac25fc3ea594e",
}
ENDPOINT_SOURCES = {
    "zero_add":"forall a. 0+a=a",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "one_mul":"forall a. 1*a=a",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    **{name:FUBINI_HELPERS[name] for name in ("slice_sum_exists","slice_sum_unique","slice_sum_zero","slice_sum_step")},
}
HELPER_DEPENDENCIES = {
    "raw_as_affine":("zero_add","one_mul"),
    "concatenate":("slice_sum_unique","slice_sum_zero","slice_sum_step","beta_unique","mul_add","add_assoc"),
    "CV009":("sum_exists","slice_sum_exists","raw_as_affine","concatenate","zero_add","one_mul"),
}


class SumSplittingError(ValueError):
    """Changed exact sum statement, actual ancestor or resource ceiling."""


def frozen_sum_splitting_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=4 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SumSplittingError("CV009 exact unconditional sum-splitting target changed")
    return target


def source_contract():
    return dict(code="CV009",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_three_sum_values_constructed=True,actual_shifted_tail=True,
        arbitrary_split_lengths=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        natural_convolution_associativity=False,exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def sum_splitting_source_pins():
    result = natural_fubini_source_pins()
    expected = {"scripts/sqrt2_power_natural_fubini.py":"d5cc2e21ccbe1f266cad6b535db62601f8e8ba1aa3209a7f89d794285e3805ac",
        FUBINI_ARCHIVE["path"]:FUBINI_ARCHIVE["sha256"]}
    for name in (*expected,"scripts/sqrt2_power_sum_splitting.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SumSplittingError("sum-splitting source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _identity_index(s,value):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqTrans
    from peano_lab.kernel.terms import Zero
    return EqTrans(CongAdd(EqRefl(Zero()),specialize(s,"one_mul",value)),specialize(s,"zero_add",value))


def _raw_as_affine(s,registry):
    from peano_lab.kernel.proofs import AndIntro,EqSym
    def body(t):
        def entry(u):
            return _subst(u,registry,"BetaAt(ab,ac,slot,a)",EqSym(_identity_index(u,u.term("i"))),u.hyp("entry"))
        return witness(t.terms(("ab","ac")),AndIntro(introduce(t,("i","a"),("bound","entry"),entry),t.hyp("sum")))
    return introduce(s,("ab","ac","L","x"),("sum",),body)


def _concatenate(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym,EqTrans,Ind
    from peano_lab.kernel.terms import Add,Mul
    parameters,premises = ("ab","ac","o","t","m","x","y","z"),("prefix","tail","whole")
    def base(t):
        length = instantiate(Axiom("PA3"),t.term("m"))
        whole = _subst(t,registry,"NatAffineSum(ab,ac,o,t,slot,z)",length,t.hyp("whole"))
        same = apply(specialize(t,"slice_sum_unique",*t.terms(("ab","ac","o","t","m","z","x"))),whole,t.hyp("prefix"))
        tail_origin = Add(t.term("o"),Mul(t.term("t"),t.term("m")))
        zero = apply(specialize(t,"slice_sum_zero",*t.terms(("ab","ac")),tail_origin,*t.terms(("t","y"))),t.hyp("tail"))
        right = EqTrans(CongAdd(EqRefl(t.term("x")),zero),instantiate(Axiom("PA3"),t.term("x")))
        return EqTrans(same,EqSym(right))
    def step(t):
        def whole_decoded(u):
            def tail_decoded(v):
                o,tv,m,n = v.terms(("o","t","m","n"))
                tail_index = Add(Add(o,Mul(tv,m)),Mul(tv,n))
                coordinate = EqTrans(CongAdd(EqRefl(o),specialize(v,"mul_add",tv,m,n)),EqSym(specialize(v,"add_assoc",o,Mul(tv,m),Mul(tv,n))))
                moved = _subst(v,registry,"BetaAt(ab,ac,slot,a)",coordinate,field(v.hyp("whole_data"),0,3))
                same = apply(specialize(v,"beta_unique",*v.terms(("ab","ac")),tail_index,*v.terms(("a","b"))),moved,field(v.hyp("tail_data"),0,3))
                ih = apply(specialize(v,"IH",*v.terms(("ab","ac","o","t","m","x","q","r"))),v.hyp("prefix"),field(v.hyp("tail_data"),1,3),field(v.hyp("whole_data"),1,3))
                return EqTrans(field(v.hyp("whole_data"),2,3),EqTrans(CongAdd(ih,same),
                    EqTrans(specialize(v,"add_assoc",*v.terms(("x","q","b"))),CongAdd(EqRefl(v.term("x")),EqSym(field(v.hyp("tail_data"),2,3))))))
            origin = Add(u.term("o"),Mul(u.term("t"),u.term("m")))
            tail = apply(specialize(u,"slice_sum_step",*u.terms(("ab","ac")),origin,*u.terms(("t","n","y"))),u.hyp("tail"))
            return eliminate(u,tail,("b","q"),"tail_data",tail_decoded)
        length = instantiate(Axiom("PA4"),*t.terms(("m","n")))
        whole = _subst(t,registry,"NatAffineSum(ab,ac,o,t,slot,z)",length,t.hyp("whole"))
        decomposed = apply(specialize(t,"slice_sum_step",*t.terms(("ab","ac","o","t")),Add(t.term("m"),t.term("n")),t.term("z")),whole)
        return eliminate(t,decomposed,("a","r"),"whole_data",whole_decoded)
    return Ind(target.body,introduce(s,parameters,premises,base),introduce(s,("n",),("IH",),lambda t:introduce(t,parameters,premises,step)))


def _root(s,registry):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Add,Succ,Zero
    def finish(t):
        prefix = apply(specialize(t,"raw_as_affine",*t.terms(("ab","ac","m","x"))),t.hyp("prefix"))
        whole = apply(specialize(t,"raw_as_affine",*t.terms(("ab","ac")),Add(t.term("m"),t.term("n")),t.term("z")),t.hyp("whole"))
        tail = _subst(t,registry,"NatAffineSum(ab,ac,slot,1,n,y)",EqSym(_identity_index(t,t.term("m"))),t.hyp("tail"))
        equality = apply(specialize(t,"concatenate",*t.terms(("n","ab","ac")),Zero(),Succ(Zero()),*t.terms(("m","x","y","z"))),prefix,tail,whole)
        return witness(t.terms(("x","y","z")),conjunction(t.hyp("prefix"),t.hyp("tail"),t.hyp("whole"),equality))
    def construct(t,position):
        if position==3:
            return finish(t)
        proof,variables,label = (
            (lambda:specialize(t,"sum_exists",*t.terms(("ab","ac","m"))),("x",),"prefix"),
            (lambda:specialize(t,"slice_sum_exists",*t.terms(("ab","ac","m")),Succ(Zero()),t.term("n")),("y",),"tail"),
            (lambda:specialize(t,"sum_exists",*t.terms(("ab","ac")),Add(t.term("m"),t.term("n"))),("z",),"whole"),
        )[position]
        return eliminate(t,proof(),variables,label,lambda u:construct(u,position+1))
    return introduce(s,("ab","ac","m","n"),(),lambda t:construct(t,0))


@dataclass(frozen=True)
class SumSplittingCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_sum_splitting(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise SumSplittingError("expected unchanged BinaryDAGLimits")
    before = sum_splitting_source_pins()
    target,registry = frozen_sum_splitting_target(),definition_registry()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise SumSplittingError("exact affine concatenation helper formula changed")
    formulas["CV009"] = target
    original = read_archive(FUBINI_ARCHIVE)
    endpoints = {}
    for name,source in ENDPOINT_SOURCES.items():
        formula = encode_formula(parse_named(source,registry=registry))
        matches = [i for i,row in enumerate(original) if row[1]==formula]
        if len(matches)!=1:
            raise SumSplittingError("actual full-body endpoint is missing or ambiguous: "+name)
        endpoints[name] = matches[0]
    reached,pending = set(),list(endpoints.values())
    while pending:
        old = pending.pop()
        if old not in reached:
            row = original[old]
            if len(row)!=4 or len(row[2])!=len(set(row[2])) or any(type(d) is not int or not 0<=d<old for d in row[2]):
                raise SumSplittingError("actual ancestor ordered dependencies changed")
            reached.add(old)
            pending.extend(row[2])
    ids = tuple(sorted(reached))
    remap = {old:new for new,old in enumerate(ids)}
    rows = [[original[old][0],original[old][1],[remap[d] for d in original[old][2]],original[old][3]] for old in ids]
    endpoint_original_ids = dict(endpoints)
    endpoints = {name:remap[old] for name,old in endpoints.items()}
    total,deepest = 0,0
    for row in rows:
        count,depth = _inert_metrics(row[3],limits)
        total,deepest = total+count,max(deepest,depth)
        if row[0]<8*count+16:
            raise SumSplittingError("actual ancestor fuel does not cover its ordinary body")
    ancestor_total = total
    factories = {"raw_as_affine":lambda s:_raw_as_affine(s,registry),
        "concatenate":lambda s:_concatenate(s,formulas["concatenate"],registry),"CV009":lambda s:_root(s,registry)}
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise SumSplittingError("sum-splitting aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in dependencies],encode_proof(body)])
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise SumSplittingError("sum-splitting canonical payload bound exceeded")
    del rows,original,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise SumSplittingError("decoded sum-splitting target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or sum_splitting_source_pins()!=before:
        raise SumSplittingError("sum-splitting target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,all_affine_sums_concatenate=True,
        actual_ancestor_nodes=len(ids),actual_ancestor_body_nodes=ancestor_total,
        ancestor_original_ids=list(ids),endpoint_original_ids=endpoint_original_ids,
        ordered_dependency_remapping_only=True,actual_archive=dict(FUBINI_ARCHIVE),
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),
        helper_bundle_indices={name:endpoints[name] for name in HELPER_DEPENDENCIES},new_induction_count=1,
        ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,new_axioms=[],
        external_certificate_references=[],independent_lean_checked=False)
    return SumSplittingCertificate(target,bundle,payload,receipt,deepest,provenance)
