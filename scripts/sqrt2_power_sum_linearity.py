"""CV006: constructive weighted linearity of three actual natural prefix sums.

All three sum witnesses are constructed. The explicit premise relates decoded
entries, not totals. The ordinary induction proves gamma*W=alpha*U+beta*V,
including empty sums and zero weights. This is the fold algebra needed for the
formal-series product rule, not a derivative or analytic identity by itself.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType

from sqrt2_power_natural_convolution import (
    ROOT,ARTIFACT,ARTIFACT_BYTES,ARTIFACT_SHA256,convolution_definitions,
    natural_convolution_source_pins,Scope,introduce,eliminate,witness,field,apply,
    specialize,canonical,json_hash,_inert_metrics,
)

SCHEMA = "sqrt2-power-sum-linearity-v1"
P = ("alpha","beta","gamma","ab","ac","bb","bc","cb","cc")
DEFINITION_SOURCE = (
    "forall i a b c. Lt(i,L) -> BetaAt(ab,ac,i,a) -> BetaAt(bb,bc,i,b) -> "
    "BetaAt(cb,cc,i,c) -> gamma*c=alpha*a+beta*b"
)
DEFINITION_SHA256 = "e152524c7c91ee548c3647e405bad333a65793f8ca6c6f4fc4cade9f76614cb7"
POINTWISE = "NatLinearTriple("+",".join(P+("L",))+")"
SUMS = "Sum(ab,ac,L,u) /\\ (Sum(bb,bc,L,v) /\\ (Sum(cb,cc,L,w) /\\ gamma*w=alpha*u+beta*v))"
NAMED_SOURCE = "forall "+" ".join(P+("L",))+". "+POINTWISE+" -> exists u v w. "+SUMS
TARGET_SHA256 = "bcf6a93be452d1bf0a424cda787eca7580644608eb69a236c5d1c99c3acea02a"
LINEARITY_SOURCE = "forall "+" ".join(P+("L","u","v","w"))+". Sum(ab,ac,L,u) -> Sum(bb,bc,L,v) -> Sum(cb,cc,L,w) -> "+POINTWISE+" -> gamma*w=alpha*u+beta*v"
LINEARITY_SHA256 = "2e1d0cb4148fe12a738b15fa7b2039923d4fecc0cc140e071e43ea478533def5"
ENDPOINT_SOURCES = {
    "add_comm":(2,"forall a b. a+b=b+a"),
    "add_assoc":(3,"forall a b c. (a+b)+c=a+(b+c)"),
    "mul_add":(7,"forall a b c. a*(b+c)=a*b+a*c"),
    "le_refl":(13,"forall a. Le(a,a)"),
    "le_succ":(34,"forall a b. Le(a,b) -> Le(a,S b)"),
    "sum_exists":(122,"forall b c L. exists n. Sum(b,c,L,n)"),
    "sum_zero":(125,"forall b c n. Sum(b,c,0,n) -> n=0"),
    "sum_decompose":(126,"forall b c L n. Sum(b,c,S L,n) -> exists a r. BetaAt(b,c,L,a) /\\ (Sum(b,c,L,r) /\\ n=r+a)"),
}
ANCESTOR_IDS = (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,22,23,24,25,26,27,28,29,32,33,34,
    35,36,37,39,41,42,43,44,45,46,47,48,49,50,51,52,53,55,56,57,58,59,60,63,65,66,67,68,69,70,71,72,
    76,78,79,80,81,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,
    108,109,110,111,112,113,114,115,116,121,122,125,126)
ANCESTOR_ROWS_BYTES = 165095
ANCESTOR_ROWS_SHA256 = "25f82015b4275ac3ab6b3f50429b278bed3231997731abdf6f8be18d2a844589"
LINEARITY_DEPENDENCIES = ("add_comm","add_assoc","mul_add","le_refl","le_succ","sum_zero","sum_decompose")
ROOT_DEPENDENCIES = ("sum_exists","linearity")


class SumLinearityError(ValueError):
    """Changed formula, conservative notation, actual body or unchanged cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(convolution_definitions())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    name,identifier,parameters = "NatLinearTriple","ND0409",P+("L",)
    if any(d["id"]==identifier or d["name"]==name for d in parent) or name in registry:
        raise SumLinearityError("local pointwise alias collides with an existing definition")
    formula = parse_named(DEFINITION_SOURCE,parameters,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise SumLinearityError("pointwise linearity exact expansion changed")
    text = pretty_formula(formula,list(parameters))
    d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
        summary="A pointwise weighted relation between three decoded prefixes; no sum identity.",
        category="irrationality_formal_series",conceptual_dependencies=("Lt","BetaAt"))
    if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
        raise SumLinearityError("pointwise linearity expansion failed exact roundtrip")
    registry[name] = d
    return MappingProxyType(registry)


def frozen_sum_linearity_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=10 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SumLinearityError("CV006 original constructed weighted-sum target changed")
    return target


def source_contract():
    return dict(code="CV006",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,actual_pointwise_relation_required=True,sum_values_supplied=False,
        all_three_actual_sums_constructed=True,positive_weights_required=False,empty_sum_allowed=True,
        new_definition_ids=["ND0409"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",formal_product_derivative=False,
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def sum_linearity_source_pins():
    result = natural_convolution_source_pins()
    expected = {"scripts/sqrt2_power_natural_convolution.py":"a5498a8534df2e1618419bb2a4ee382d3ebd205fd024560cca9876ab9e4eedd1",
        "scripts/sqrt2_power_quadratic_height.py":"4dbca16777efcbc535bbab885accd7ad8f6a729edafb48c525365b2c56aec51c"}
    for name in (*expected,"scripts/sqrt2_power_sum_linearity.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SumLinearityError("weighted-sum source changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def inert_sum_rows(artifact_path=ARTIFACT):
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    with Path(artifact_path).open("rb") as stream:
        raw = stream.read(ARTIFACT_BYTES+1)
    if len(raw)!=ARTIFACT_BYTES or sha256(raw).hexdigest()!=ARTIFACT_SHA256:
        raise SumLinearityError("actual finite-sum ancestor archive changed")
    archive = json.loads(raw)
    if archive[0]!="peano-lab-bundle-v1" or archive[1]!=209 or len(archive[3])!=210:
        raise SumLinearityError("actual finite-sum archive envelope changed")
    seen,pending = set(),[old for old,_ in ENDPOINT_SOURCES.values()]
    while pending:
        old = pending.pop()
        if type(old) is not int or not 0<=old<210:
            raise SumLinearityError("invalid actual finite-sum ancestor index")
        if old not in seen:
            r = archive[3][old]
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise SumLinearityError("invalid actual finite-sum ordered dependencies")
            seen.add(old)
            pending.extend(r[2])
    ids = tuple(sorted(seen))
    rows = tuple(archive[3][old] for old in ids)
    if ids!=ANCESTOR_IDS or len(canonical(rows))!=ANCESTOR_ROWS_BYTES or json_hash(rows)!=ANCESTOR_ROWS_SHA256:
        raise SumLinearityError("exact finite-sum ancestor cone changed")
    registry = definition_registry()
    for old,source in ENDPOINT_SOURCES.values():
        if archive[3][old][1]!=encode_formula(parse_named(source,registry=registry)):
            raise SumLinearityError("actual sum endpoint differs from its frozen formula")
    return ids,rows


def _linearity_body(target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _additive_equal,_chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym,EqTrans,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def base(s):
        alpha,beta,gamma = s.terms(P[:3])
        values = tuple(apply(specialize(s,"sum_zero",*s.terms(codes),s.term(value)),s.hyp(label))
            for codes,value,label in ((("ab","ac"),"u","first_sum"),(("bb","bc"),"v","second_sum"),(("cb","cc"),"w","third_sum")))
        left = EqTrans(CongMul(EqRefl(gamma),values[2]),instantiate(Axiom("PA5"),gamma))
        right = _chain(CongAdd(CongMul(EqRefl(alpha),values[0]),CongMul(EqRefl(beta),values[1])),
            CongAdd(instantiate(Axiom("PA5"),alpha),instantiate(Axiom("PA5"),beta)),instantiate(Axiom("PA3"),Zero()))
        return EqTrans(left,EqSym(right))
    def step(s):
        def finish(t):
            alpha,beta,gamma = t.terms(P[:3])
            a,r,b,q,c,z = t.terms(("a","r","b","q","c","z"))
            def restricted(u):
                bound = apply(specialize(u,"le_succ",Succ(u.term("i")),u.term("L")),u.hyp("index"))
                return apply(specialize(u,"pointwise",*u.terms(("i","x","y","h"))),
                    bound,u.hyp("left"),u.hyp("middle"),u.hyp("right"))
            prefix_relation = introduce(t,("i","x","y","h"),("index","left","middle","right"),restricted)
            previous = apply(specialize(t,"IH",r,q,z),*(field(t.hyp(label),1,3) for label in ("first","second","third")),prefix_relation)
            last = apply(specialize(t,"pointwise",t.term("L"),a,b,c),specialize(t,"le_refl",Succ(t.term("L"))),
                *(field(t.hyp(label),0,3) for label in ("first","second","third")))
            left_expanded = Add(Add(Mul(alpha,r),Mul(beta,q)),Add(Mul(alpha,a),Mul(beta,b)))
            right_expanded = Add(Add(Mul(alpha,r),Mul(alpha,a)),Add(Mul(beta,q),Mul(beta,b)))
            return _chain(CongMul(EqRefl(gamma),field(t.hyp("third"),2,3)),
                specialize(t,"mul_add",gamma,z,c),CongAdd(previous,last),
                _additive_equal(t,left_expanded,right_expanded),
                CongAdd(EqSym(specialize(t,"mul_add",alpha,r,a)),EqSym(specialize(t,"mul_add",beta,q,b))),
                CongAdd(CongMul(EqRefl(alpha),EqSym(field(t.hyp("first"),2,3))),
                        CongMul(EqRefl(beta),EqSym(field(t.hyp("second"),2,3)))))
        def decoded(t,position):
            if position==3:
                return finish(t)
            codes,value,label,variables = (
                (("ab","ac"),"u","first",("a","r")),
                (("bb","bc"),"v","second",("b","q")),
                (("cb","cc"),"w","third",("c","z")),
            )[position]
            source = apply(specialize(t,"sum_decompose",*t.terms(codes),t.term("L"),t.term(value)),t.hyp(label+"_sum"))
            return eliminate(t,source,variables,label,lambda u:decoded(u,position+1))
        return decoded(s,0)
    motive = target
    for _ in range(10):
        motive = motive.body
    def induction(s):
        parameters = ("u","v","w")
        premises = ("first_sum","second_sum","third_sum","pointwise")
        return Ind(motive,introduce(s,parameters,premises,base),
            introduce(s,("L",),("IH",),lambda t:introduce(t,parameters,premises,step)))
    return introduce(Scope(),(),LINEARITY_DEPENDENCIES,lambda s:introduce(s,P,(),induction))


def _root_body():
    from peano_lab.kernel.proofs import AndIntro
    def finish(s):
        identity = apply(specialize(s,"linearity",*s.terms(P+("L","u","v","w"))),
            s.hyp("first"),s.hyp("second"),s.hyp("third"),s.hyp("pointwise"))
        return witness(s.terms(("u","v","w")),AndIntro(s.hyp("first"),AndIntro(s.hyp("second"),AndIntro(s.hyp("third"),identity))))
    def construct(s,position):
        if position==3:
            return finish(s)
        codes,value,label = ((("ab","ac"),"u","first"),(("bb","bc"),"v","second"),(("cb","cc"),"w","third"))[position]
        return eliminate(s,specialize(s,"sum_exists",*s.terms(codes),s.term("L")),(value,),label,lambda t:construct(t,position+1))
    return introduce(Scope(),(),ROOT_DEPENDENCIES,lambda s:
        introduce(s,P+("L",),("pointwise",),lambda t:construct(t,0)))


@dataclass(frozen=True)
class SumLinearityCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_sum_linearity(*,limits=None,artifact_path=ARTIFACT):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise SumLinearityError("expected unchanged BinaryDAGLimits")
    before = sum_linearity_source_pins()
    target,registry = frozen_sum_linearity_target(),definition_registry()
    linearity = parse_named(LINEARITY_SOURCE,registry=registry)
    if json_hash(encode_formula(linearity))!=LINEARITY_SHA256:
        raise SumLinearityError("weighted-sum all-lengths invariant changed")
    ids,original = inert_sum_rows(artifact_path)
    remap = {old:new for new,old in enumerate(ids)}
    rows = [[r[0],r[1],[remap[d] for d in r[2]],r[3]] for r in original]
    endpoints = {name:remap[old] for name,(old,_) in ENDPOINT_SOURCES.items()}
    total,deepest = 0,0
    for r in rows:
        count,depth = _inert_metrics(r[3],limits)
        total,deepest = total+count,max(deepest,depth)
        if type(r[0]) is not int or r[0]<8*count+16:
            raise SumLinearityError("actual sum ancestor fuel does not cover its body")
    ancestor_total = total
    for name,formula,dependencies,body in (
        ("linearity",linearity,LINEARITY_DEPENDENCIES,_linearity_body(linearity)),
        ("CV006",target,ROOT_DEPENDENCIES,_root_body()),
    ):
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise SumLinearityError("weighted-sum aggregate ordinary-body/node bound exceeded")
        _row_preflight(formula,body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formula),[endpoints[d] for d in dependencies],encode_proof(body)])
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise SumLinearityError("weighted-sum canonical payload bound exceeded")
    del rows,original,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise SumLinearityError("weighted-sum decoded target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or sum_linearity_source_pins()!=before:
        raise SumLinearityError("weighted-sum target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,all_lengths_weighted_linearity=True,
        actual_ancestor_nodes=len(ids),actual_ancestor_body_nodes=ancestor_total,
        ancestor_original_ids=list(ids),ancestor_rows_sha256=ANCESTOR_ROWS_SHA256,
        invariant_statement_ast_sha256=LINEARITY_SHA256,new_induction_count=1,
        deterministic_additive_reassociation=True,ring_normalizer_calls=0,solver_calls=0,
        local_have_compiler_calls=0,new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return SumLinearityCertificate(target,bundle,payload,receipt,deepest,provenance)
