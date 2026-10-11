"""CV015: weighted natural convolution linearity from actual pointwise data.

All three coefficients are constructed. The left inputs share a length; the
right input and coefficient index are arbitrary. Zero weights are allowed.
Actual antidiagonal functionality and CV006 prove the identity, not a ring
oracle or a definition containing the desired conclusion.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_natural_convolution import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,
    canonical,json_hash,_inert_metrics,definition_registry as convolution_registry,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_quadratic_product_exists import read_archive
from sqrt2_power_sum_linearity import (
    definition_registry as linearity_registry,sum_linearity_source_pins,LINEARITY_SOURCE,
)
from sqrt2_power_euler_product import coefficient,LINEARITY_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE

SCHEMA = "sqrt2-power-convolution-linearity-v1"
P = ("alpha","beta","gamma","ab","ac","bb","bc","cb","cc","L","db","dc","M","i")
A,B,C,D = ("ab","ac","L"),("bb","bc","L"),("cb","cc","L"),("db","dc","M")
POINTWISE = "NatLinearTriple(alpha,beta,gamma,ab,ac,bb,bc,cb,cc,L)"
ARCHIVES = (CONVOLUTION_ARCHIVE,LINEARITY_ARCHIVE)


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def pad(codes,index,value):
    return "BetaZeroExtend("+",".join(codes+(index,value))+")"


def term(left,value):
    return "PolynomialDiagonalTerm("+",".join(left+D+("i","j",value))+")"


RESULT = coefficient(A,D,"i","u")+" /\\ ("+coefficient(B,D,"i","v")+" /\\ ("+coefficient(C,D,"i","w")+" /\\ gamma*w=alpha*u+beta*v))"
NAMED_SOURCE = forall(P,POINTWISE+" -> exists u v w. "+RESULT)
TARGET_SHA256 = "454dd9464f21bb867fd39a78eebb4d9eabe59aae256c134ab0624e05d8d17f91"
HELPER_SOURCES = {
    "padded_linear":forall(P[:10]+("j","a","b","c"),POINTWISE+" -> "+pad(A,"j","a")+" -> "+pad(B,"j","b")+" -> "+pad(C,"j","c")+" -> gamma*c=alpha*a+beta*b"),
    "term_linear":forall(P+("j","x","y","z"),POINTWISE+" -> "+term(A,"x")+" -> "+term(B,"y")+" -> "+term(C,"z")+" -> gamma*z=alpha*x+beta*y"),
    "coefficient_linearity":forall(P+("u","v","w"),POINTWISE+" -> "+coefficient(A,D,"i","u")+" -> "+coefficient(B,D,"i","v")+" -> "+coefficient(C,D,"i","w")+" -> gamma*w=alpha*u+beta*v"),
}
HELPER_TARGET_SHA256 = {
    "padded_linear":"157f075b65cb9770a315b28bf1921ea2fc27bce8df2ffe1a61798279fcb59419",
    "term_linear":"6fcfeb4f2dd02c99d76672cfca127bdf2d64bb61f3eb321f872c6599ae89e983",
    "coefficient_linearity":"075c7783a5967c79de287df4f545d6658a16da2a41f6ece161e894ae65b97145",
}
ENDPOINT_SOURCES = {
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "add_mul":"forall a b c. (a+b)*c=a*c+b*c",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "padding_exists":"forall b c L i. exists a. BetaZeroExtend(b,c,L,i,a)",
    "padding_unique":"forall b c L i a d. BetaZeroExtend(b,c,L,i,a) -> BetaZeroExtend(b,c,L,i,d) -> a=d",
    "term_unique":"forall ab ac L bb bc M i j t s. PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,s) -> t=s",
    "diagonal_entry":"forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)",
    "coefficient_exists":"forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)",
    "sum_linearity":LINEARITY_SOURCE,
}
HELPER_DEPENDENCIES = {
    "padded_linear":("beta_exists","padding_unique"),
    "term_linear":("padding_exists","term_unique","padded_linear","mul_assoc","add_mul"),
    "coefficient_linearity":("diagonal_entry","term_linear","sum_linearity"),
    "CV015":("coefficient_exists","coefficient_linearity"),
}


class ConvolutionLinearityError(ValueError):
    """Changed actual premise, ancestor body, target or resource bound."""


def definition_registry():
    registry = dict(convolution_registry())
    for name,d in linearity_registry().items():
        if name in registry and (registry[name].template_formula!=d.template_formula or registry[name].stable_id!=d.stable_id):
            raise ConvolutionLinearityError("shared conservative definition mismatch")
        registry[name] = d
    return MappingProxyType(registry)


def frozen_convolution_linearity_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=14 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionLinearityError("CV015 exact weighted coefficient target changed")
    return target


def source_contract():
    return dict(code="CV015",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,actual_pointwise_relation_required=True,shared_left_input_length=True,
        arbitrary_right_input_length_and_index=True,positive_weights_required=False,
        all_three_coefficients_constructed=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def convolution_linearity_source_pins():
    result = sum_linearity_source_pins()
    expected = {
        "scripts/sqrt2_power_sum_linearity.py":"5a9131119953036d5bb1c7cb2b08e26bcc4fa63fd31a8c0cbc77409f17358bc0",
        "scripts/sqrt2_power_euler_product.py":"c26512518de941c9f8c54bfe682732d601158748f25955166b3ea6d8290afa10",
        "scripts/sqrt2_power_series_power_trace.py":"557d393791fb527361bcffb4977b0e0bad591f98a426e12d1da461643cc39422",
        "scripts/sqrt2_power_quadratic_product_exists.py":"c20c38bfceb78fa16c236925024a43c12624b2df23937bb1c1e9f54393d49017",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_convolution_linearity.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionLinearityError("coefficient-linearity source/archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _padded_linear(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndIntro,AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,EqTrans,OrElim,OrIntroL,OrIntroR
    from peano_lab.kernel.terms import Zero
    def finish(t):
        def inside(u):
            def values(v):
                alpha,beta,gamma = v.terms(P[:3])
                bound = AndElimL(v.hyp("inside"))
                ae = apply(specialize(v,"padding_unique",*v.terms(A+("j","a","a0"))),
                    v.hyp("pad_a"),OrIntroL(AndIntro(bound,v.hyp("value_a"))))
                be = apply(specialize(v,"padding_unique",*v.terms(B+("j","b","b0"))),
                    v.hyp("pad_b"),OrIntroL(AndIntro(bound,v.hyp("value_b"))))
                identity = apply(specialize(v,"pointwise",*v.terms(("j","a0","b0","c"))),
                    bound,v.hyp("value_a"),v.hyp("value_b"),AndElimR(v.hyp("inside")))
                return EqTrans(identity,EqSym(CongAdd(CongMul(EqRefl(alpha),ae),CongMul(EqRefl(beta),be))))
            return eliminate(u,specialize(u,"beta_exists",*u.terms(("ab","ac","j"))),("a0",),"value_a",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(("bb","bc","j"))),("b0",),"value_b",values))
        def outside(u):
            alpha,beta,gamma = u.terms(P[:3])
            zero_pad = OrIntroR(AndIntro(AndElimL(u.hyp("outside")),EqRefl(Zero())))
            ae = apply(specialize(u,"padding_unique",*u.terms(A+("j","a")),Zero()),u.hyp("pad_a"),zero_pad)
            be = apply(specialize(u,"padding_unique",*u.terms(B+("j","b")),Zero()),u.hyp("pad_b"),zero_pad)
            left = EqTrans(CongMul(EqRefl(gamma),AndElimR(u.hyp("outside"))),instantiate(Axiom("PA5"),gamma))
            right = _chain(CongAdd(CongMul(EqRefl(alpha),ae),CongMul(EqRefl(beta),be)),
                CongAdd(instantiate(Axiom("PA5"),alpha),instantiate(Axiom("PA5"),beta)),instantiate(Axiom("PA3"),Zero()))
            return EqTrans(left,EqSym(right))
        return OrElim(t.hyp("pad_c"),inside(t.hypothesis("inside")),outside(t.hypothesis("outside")))
    return introduce(s,P[:10]+("j","a","b","c"),("pointwise","pad_a","pad_b","pad_c"),finish)


def _term_linear(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def values(t):
        alpha,beta,gamma = t.terms(P[:3])
        k,a,b,c,d = t.terms(("k","a","b","c","d"))
        data = t.hyp("cell_c")
        ad,bd = Mul(a,d),Mul(b,d)
        def reference(value,padding):
            return witness((k,value,d),conjunction(field(data,0,4),t.hyp(padding),field(data,2,4),EqRefl(Mul(value,d))))
        xe = apply(specialize(t,"term_unique",*t.terms(A+D+("i","j","x")),ad),t.hyp("term_a"),reference(a,"pad_a"))
        ye = apply(specialize(t,"term_unique",*t.terms(B+D+("i","j","y")),bd),t.hyp("term_b"),reference(b,"pad_b"))
        point = apply(specialize(t,"padded_linear",*t.terms(P[:10]+("j","a","b","c"))),
            t.hyp("pointwise"),t.hyp("pad_a"),t.hyp("pad_b"),field(data,1,4))
        return _chain(CongMul(EqRefl(gamma),field(data,3,4)),EqSym(specialize(t,"mul_assoc",gamma,c,d)),
            CongMul(point,EqRefl(d)),specialize(t,"add_mul",Mul(alpha,a),Mul(beta,b),d),
            CongAdd(specialize(t,"mul_assoc",alpha,a,d),specialize(t,"mul_assoc",beta,b,d)),
            CongAdd(CongMul(EqRefl(alpha),EqSym(xe)),CongMul(EqRefl(beta),EqSym(ye))))
    def original(t):
        return eliminate(t,specialize(t,"padding_exists",*t.terms(A+("j",))),("a",),"pad_a",lambda u:
            eliminate(u,specialize(u,"padding_exists",*u.terms(B+("j",))),("b",),"pad_b",values))
    return introduce(s,P+("j","x","y","z"),("pointwise","term_a","term_b","term_c"),lambda t:
        eliminate(t,t.hyp("term_c"),("k","c","d"),"cell_c",original))


def _coefficient_linearity(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ
    def finish(t):
        def pointwise(u):
            def entry(inputs,codes,label,value):
                return apply(specialize(u,"diagonal_entry",*u.terms(inputs+D+("i",)+codes),Succ(u.term("i")),*u.terms(("j",value))),
                    AndElimL(u.hyp(label)),u.hyp("bound"),u.hyp(value+"_value"))
            return apply(specialize(u,"term_linear",*u.terms(P+("j","x","y","z"))),u.hyp("pointwise"),
                entry(A,("xb","xc"),"first","x"),entry(B,("yb","yc"),"second","y"),entry(C,("zb","zc"),"third","z"))
        relation = introduce(t,("j","x","y","z"),("bound","x_value","y_value","z_value"),pointwise)
        return apply(specialize(t,"sum_linearity",*t.terms(P[:3]+("xb","xc","yb","yc","zb","zc")),Succ(t.term("i")),*t.terms(("u","v","w"))),
            AndElimR(t.hyp("first")),AndElimR(t.hyp("second")),AndElimR(t.hyp("third")),relation)
    return introduce(s,P+("u","v","w"),("pointwise","source_a","source_b","source_c"),lambda t:
        eliminate(t,t.hyp("source_a"),("xb","xc"),"first",lambda u:
            eliminate(u,u.hyp("source_b"),("yb","yc"),"second",lambda v:
                eliminate(v,v.hyp("source_c"),("zb","zc"),"third",finish))))


def _root(s):
    def finish(t):
        identity = apply(specialize(t,"coefficient_linearity",*t.terms(P+("u","v","w"))),
            *(t.hyp(label) for label in ("pointwise","first","second","third")))
        return witness(t.terms(("u","v","w")),conjunction(t.hyp("first"),t.hyp("second"),t.hyp("third"),identity))
    def construct(t,position):
        if position==3:
            return finish(t)
        inputs,value,label = ((A,"u","first"),(B,"v","second"),(C,"w","third"))[position]
        return eliminate(t,specialize(t,"coefficient_exists",*t.terms(inputs+D+("i",))),(value,),label,lambda u:construct(u,position+1))
    return introduce(s,P,("pointwise",),lambda t:construct(t,0))


@dataclass(frozen=True)
class ConvolutionLinearityCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_convolution_linearity(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise ConvolutionLinearityError("expected unchanged BinaryDAGLimits")
    before = convolution_linearity_source_pins()
    registry,target = definition_registry(),frozen_convolution_linearity_target()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise ConvolutionLinearityError("exact weighted coefficient helper target changed")
    formulas["CV015"] = target
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    for pin in ARCHIVES:
        original = read_archive(pin)
        remap = {}
        for old,r in enumerate(original):
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise ConvolutionLinearityError("actual ancestor ordered dependencies changed")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if type(r[0]) is not int or r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise ConvolutionLinearityError("merged ancestor body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        for name,source in ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=registry))
            matches = [i for i,r in enumerate(original) if r[1]==formula]
            if len(matches)>1:
                raise ConvolutionLinearityError("ambiguous actual endpoint: "+name)
            if matches:
                if name in endpoints and endpoints[name]!=remap[matches[0]]:
                    raise ConvolutionLinearityError("shared actual endpoint bodies disagree")
                endpoints[name] = remap[matches[0]]
        del original,remap
        gc.collect()
    if endpoints.keys()!=ENDPOINT_SOURCES.keys():
        raise ConvolutionLinearityError("missing actual weighted coefficient ancestor endpoint")
    ancestor_count = len(rows)
    factories = {"padded_linear":_padded_linear,"term_linear":_term_linear,
        "coefficient_linearity":_coefficient_linearity,"CV015":_root}
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise ConvolutionLinearityError("weighted coefficient aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in dependencies],encode_proof(body)])
    reached,pending = set(),[len(rows)-1]
    while pending:
        old = pending.pop()
        if old not in reached:
            reached.add(old)
            pending.extend(rows[old][2])
    retained = tuple(sorted(reached))
    remap = {old:new for new,old in enumerate(retained)}
    ancestors = tuple(old for old in retained if old<ancestor_count)
    ancestor_total = sum(_inert_metrics(rows[old][3],limits)[0] for old in ancestors)
    helper_indices = {name:remap[endpoints[name]] for name in HELPER_DEPENDENCIES}
    rows = [[rows[old][0],rows[old][1],[remap[d] for d in rows[old][2]],rows[old][3]] for old in retained]
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise ConvolutionLinearityError("weighted coefficient canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise ConvolutionLinearityError("decoded weighted coefficient target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or convolution_linearity_source_pins()!=before:
        raise ConvolutionLinearityError("weighted coefficient target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,actual_weighted_convolution_linearity=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        actual_archives=[dict(pin) for pin in ARCHIVES],
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),helper_bundle_indices=helper_indices,
        new_induction_count=0,ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return ConvolutionLinearityCertificate(target,bundle,payload,receipt,deepest,provenance)
