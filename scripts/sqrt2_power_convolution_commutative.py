"""CV010: construct equal natural Cauchy coefficients in both input orders.

Actual finite sums are reversed by induction using the checked prefix/tail
splitting law. The antidiagonal witnesses then supply a genuine reversal
between A*B and B*A. No commutativity claim is hidden in a definition.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_sum_splitting import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,_inert_metrics,read_archive,definition_registry as affine_registry,
    sum_splitting_source_pins,HELPER_SOURCES as SPLIT_HELPERS,_subst,_identity_index,
)
from sqrt2_power_natural_fubini import HELPER_SOURCES as FUBINI_HELPERS
from sqrt2_power_natural_convolution import definition_registry as convolution_registry
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_euler_product import coefficient

SCHEMA = "sqrt2-power-convolution-commutative-v1"
SPLIT_ARCHIVE = dict(case="CV009",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-sum-splitting-v1/generation-process.json.gz",
    bytes=22430,sha256="1cc42e1decde87ddd252e9ea68933af976d365d4f79d7134c8df4e4174e1a6e6",
    raw_bytes=401585,raw_sha256="e2e5fdc7ebfc74147c82478b0f38a496ad29aca79092b34316f17a705b5abb35",
    bundle_bytes=240857,bundle_sha256="10d2619e1cb26a945cb18471091aaa96331b1718c28ce736a669c001fbaa26ed",
    nodes=120,root=119,target_ast_sha256="2aa07f3f9d93b14be669dd9bcca9eb51364030fe16587b130f508419e396c462")
P = ("ab","ac","L","bb","bc","M")
A,B = P[:3],P[3:]
NAMED_SOURCE = "forall "+" ".join(P+("i",))+". exists n. "+coefficient(A,B,"i","n")+" /\\ "+coefficient(B,A,"i","n")
TARGET_SHA256 = "3e62febc17b41a970070ca88e057e05ef7888d821a65f9019ac15bfb8fc5a825"
HELPER_SOURCES = {
    "sum_one":"forall b c u a. Sum(b,c,1,u) -> BetaAt(b,c,0,a) -> u=a",
    "head_tail":"forall ab ac N u a v. Sum(ab,ac,S N,u) -> BetaAt(ab,ac,0,a) -> NatAffineSum(ab,ac,1,1,N,v) -> u=a+v",
    "reverse":"forall N ab ac bb bc u v. Sum(ab,ac,S N,u) -> Sum(bb,bc,S N,v) -> "
        "(forall j k a b. j+k=N -> BetaAt(ab,ac,j,a) -> BetaAt(bb,bc,k,b) -> a=b) -> u=v",
    "commute":"forall "+" ".join(P+("i","n","m"))+". "+coefficient(A,B,"i","n")+" -> "+coefficient(B,A,"i","m")+" -> n=m",
}
HELPER_TARGET_SHA256 = {
    "sum_one":"5fa45e265006dd0fd3c61836a0cb9809bd07f58de925806d89f46fe1af077211",
    "head_tail":"8bab0b51e89c7eccedb5120c900dd7bcfbd68f8d7e8d559d7f50e85945da6807",
    "reverse":"4d2a6b6ff0620ef491bb6f34d310a12495840eda05fd543918af97edeb8188a8",
    "commute":"d5cf2cfd7c99736d25271c2f447954bcadbba805404655ec8e4cbd863ecc85ed",
}
ENDPOINT_SOURCES = {
    "zero_add":"forall a. 0+a=a",
    "add_succ_left":"forall a b. S a+b=S (a+b)",
    "add_comm":"forall a b. a+b=b+a",
    "one_mul":"forall a. 1*a=a",
    "mul_comm":"forall a b. a*b=b*a",
    "add_left_cancel":"forall a b c. a+b=a+c -> b=c",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "sum_zero":"forall b c n. Sum(b,c,0,n) -> n=0",
    "sum_decompose":"forall b c N n. Sum(b,c,S N,n) -> exists a r. BetaAt(b,c,N,a) /\\ (Sum(b,c,N,r) /\\ n=r+a)",
    "slice_exists":FUBINI_HELPERS["slice_exists"],
    **SPLIT_HELPERS,
    "term_unique":"forall ab ac L bb bc M i j t s. PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,s) -> t=s",
    "diagonal_entry":"forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)",
    "coefficient_exists":"forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)",
}
HELPER_DEPENDENCIES = {
    "sum_one":("sum_decompose","sum_zero","beta_unique","zero_add"),
    "head_tail":("sum_exists","sum_one","raw_as_affine","concatenate","zero_add","one_mul","add_succ_left"),
    "reverse":("sum_one","head_tail","sum_decompose","sum_exists","slice_exists","beta_exists","zero_add","one_mul","add_succ_left","add_comm"),
    "commute":("reverse","diagonal_entry","term_unique","add_left_cancel","add_comm","mul_comm"),
    "CV010":("coefficient_exists","commute"),
}


class ConvolutionCommutativeError(ValueError):
    """Changed exact coefficient relation, actual body or resource ceiling."""


def definition_registry():
    registry = dict(affine_registry())
    for name,d in convolution_registry().items():
        if name in registry and (registry[name].stable_id!=d.stable_id or registry[name].template_formula!=d.template_formula):
            raise ConvolutionCommutativeError("convolution/affine shared definitions disagree")
        registry[name] = d
    return MappingProxyType(registry)


def frozen_convolution_commutative_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionCommutativeError("CV010 exact unconditional commutative target changed")
    return target


def source_contract():
    return dict(code="CV010",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,both_coefficients_constructed=True,arbitrary_input_lengths_and_index=True,
        coefficient_order="ascending_series",new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        natural_convolution_associativity=False,exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def convolution_commutative_source_pins():
    result = sum_splitting_source_pins()
    expected = {"scripts/sqrt2_power_sum_splitting.py":"aa629a6c5eddabbd880ccf615b0bc897fa77da7965c1a37b056016a9611c3c3c",
        SPLIT_ARCHIVE["path"]:SPLIT_ARCHIVE["sha256"]}
    for name in (*expected,"scripts/sqrt2_power_convolution_commutative.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionCommutativeError("commutative coefficient source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _one_add(s,value):
    from peano_lab.kernel.proofs import CongS,EqTrans
    from peano_lab.kernel.terms import Zero
    return EqTrans(specialize(s,"add_succ_left",Zero(),value),CongS(specialize(s,"zero_add",value)))


def _sum_one(s):
    from peano_lab.kernel.proofs import CongAdd,EqTrans
    from peano_lab.kernel.terms import Zero
    def finish(t):
        zero = apply(specialize(t,"sum_zero",*t.terms(("b","c","r"))),field(t.hyp("data"),1,3))
        same = apply(specialize(t,"beta_unique",*t.terms(("b","c")),Zero(),*t.terms(("v","a"))),field(t.hyp("data"),0,3),t.hyp("first"))
        return EqTrans(field(t.hyp("data"),2,3),EqTrans(CongAdd(zero,same),specialize(t,"zero_add",t.term("a"))))
    return introduce(s,("b","c","u","a"),("sum","first"),lambda t:
        eliminate(t,apply(specialize(t,"sum_decompose",*t.terms(("b","c")),Zero(),t.term("u")),t.hyp("sum")),("v","r"),"data",finish))


def _head_tail(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym,EqTrans
    from peano_lab.kernel.terms import Succ,Zero
    def finish(t):
        one = Succ(Zero())
        prefix = apply(specialize(t,"raw_as_affine",*t.terms(("ab","ac")),one,t.term("r")),t.hyp("first_sum"))
        whole = apply(specialize(t,"raw_as_affine",*t.terms(("ab","ac")),Succ(t.term("N")),t.term("u")),t.hyp("whole"))
        whole = _subst(t,registry,"NatAffineSum(ab,ac,0,1,slot,u)",EqSym(_one_add(t,t.term("N"))),whole)
        tail = _subst(t,registry,"NatAffineSum(ab,ac,slot,1,N,v)",EqSym(_identity_index(t,one)),t.hyp("tail"))
        split = apply(specialize(t,"concatenate",*t.terms(("N","ab","ac")),Zero(),one,one,*t.terms(("r","v","u"))),prefix,tail,whole)
        first = apply(specialize(t,"sum_one",*t.terms(("ab","ac","r","a"))),t.hyp("first_sum"),t.hyp("first"))
        return EqTrans(split,CongAdd(first,EqRefl(t.term("v"))))
    return introduce(s,("ab","ac","N","u","a","v"),("whole","first","tail"),lambda t:
        eliminate(t,specialize(t,"sum_exists",*t.terms(("ab","ac")),Succ(Zero())),("r",),"first_sum",finish))


def _reverse(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,Axiom,CongAdd,CongS,EqRefl,EqSym,EqTrans,ExistsIntro,Ind
    from peano_lab.kernel.terms import Add,Succ,Zero
    parameters,premises = ("ab","ac","bb","bc","u","v"),("first_sum","second_sum","pointwise")
    def base(t):
        def first(u):
            def second(v):
                left = apply(specialize(v,"sum_one",*v.terms(("ab","ac","u","a"))),v.hyp("first_sum"),v.hyp("first"))
                right = apply(specialize(v,"sum_one",*v.terms(("bb","bc","v","b"))),v.hyp("second_sum"),v.hyp("second"))
                same = apply(specialize(v,"pointwise",Zero(),Zero(),*v.terms(("a","b"))),instantiate(Axiom("PA3"),Zero()),v.hyp("first"),v.hyp("second"))
                return EqTrans(left,EqTrans(same,EqSym(right)))
            return eliminate(u,specialize(u,"beta_exists",*u.terms(("bb","bc")),Zero()),("b",),"second",second)
        return eliminate(t,specialize(t,"beta_exists",*t.terms(("ab","ac")),Zero()),("a",),"first",first)
    def step(t):
        def decomposed(u):
            def tail(v):
                def tail_sum(w):
                    def second_first(x):
                        def pointwise(y):
                            equation = EqTrans(instantiate(Axiom("PA4"),*y.terms(("j","k"))),CongS(y.hyp("index")))
                            bound = ExistsIntro(y.term("j"),equation)
                            decoded = apply(specialize(y,"tail",*y.terms(("k","y"))),bound,y.hyp("y_entry"))
                            shifted = EqTrans(CongAdd(EqRefl(Succ(Zero())),specialize(y,"one_mul",y.term("k"))),_one_add(y,y.term("k")))
                            actual = _subst(y,registry,"BetaAt(bb,bc,slot,y)",shifted,decoded)
                            return apply(specialize(y,"pointwise",y.term("j"),Succ(y.term("k")),*y.terms(("x","y"))),equation,y.hyp("x_entry"),actual)
                        reverse_tail = introduce(x,("j","k","x","y"),("index","x_entry","y_entry"),pointwise)
                        ih = apply(specialize(x,"IH",*x.terms(("ab","ac","db","dc","r","w"))),field(x.hyp("decomposed"),1,3),x.hyp("tail_sum"),reverse_tail)
                        last = apply(specialize(x,"pointwise",Succ(x.term("N")),Zero(),*x.terms(("a","b"))),instantiate(Axiom("PA3"),Succ(x.term("N"))),field(x.hyp("decomposed"),0,3),x.hyp("second_first"))
                        actual_tail = witness(x.terms(("db","dc")),AndIntro(x.hyp("tail"),x.hyp("tail_sum")))
                        second = apply(specialize(x,"head_tail",*x.terms(("bb","bc")),Succ(x.term("N")),*x.terms(("v","b","w"))),x.hyp("second_sum"),x.hyp("second_first"),actual_tail)
                        return EqTrans(field(x.hyp("decomposed"),2,3),EqTrans(CongAdd(ih,last),
                            EqTrans(specialize(x,"add_comm",*x.terms(("w","b"))),EqSym(second))))
                    return eliminate(w,specialize(w,"beta_exists",*w.terms(("bb","bc")),Zero()),("b",),"second_first",second_first)
                return eliminate(v,specialize(v,"sum_exists",*v.terms(("db","dc")),Succ(v.term("N"))),("w",),"tail_sum",tail_sum)
            one = Succ(Zero())
            return eliminate(u,specialize(u,"slice_exists",*u.terms(("bb","bc")),one,one,Succ(u.term("N"))),("db","dc"),"tail",tail)
        source = apply(specialize(t,"sum_decompose",*t.terms(("ab","ac")),Succ(t.term("N")),t.term("u")),t.hyp("first_sum"))
        return eliminate(t,source,("a","r"),"decomposed",decomposed)
    return Ind(target.body,introduce(s,parameters,premises,base),introduce(s,("N",),("IH",),lambda t:introduce(t,parameters,premises,step)))


def _commute(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,Axiom,CongS,EqSym,EqTrans,ExistsIntro
    from peano_lab.kernel.terms import Succ
    def finish(t):
        def pointwise(u):
            def decoded(v):
                complement = apply(specialize(v,"add_left_cancel",*v.terms(("j","r","k"))),EqTrans(field(v.hyp("term"),0,4),EqSym(v.hyp("index"))))
                right = _subst(v,registry,"BetaZeroExtend(bb,bc,M,slot,y)",complement,field(v.hyp("term"),2,4))
                opposite = EqTrans(specialize(v,"add_comm",*v.terms(("k","j"))),v.hyp("index"))
                product = EqTrans(field(v.hyp("term"),3,4),specialize(v,"mul_comm",*v.terms(("x","y"))))
                swapped = witness(v.terms(("j","y","x")),conjunction(opposite,right,field(v.hyp("term"),1,4),product))
                bound = ExistsIntro(v.term("j"),EqTrans(instantiate(Axiom("PA4"),*v.terms(("j","k"))),CongS(v.hyp("index"))))
                actual = apply(specialize(v,"diagonal_entry",*v.terms(B+A+("i","eb","ec")),Succ(v.term("i")),*v.terms(("k","b"))),AndElimL(v.hyp("second")),bound,v.hyp("b_entry"))
                same = apply(specialize(v,"term_unique",*v.terms(B+A+("i","k","b","a"))),actual,swapped)
                return EqSym(same)
            opposite = EqTrans(specialize(u,"add_comm",*u.terms(("k","j"))),u.hyp("index"))
            bound = ExistsIntro(u.term("k"),EqTrans(instantiate(Axiom("PA4"),*u.terms(("k","j"))),CongS(opposite)))
            actual = apply(specialize(u,"diagonal_entry",*u.terms(P+("i","db","dc")),Succ(u.term("i")),*u.terms(("j","a"))),AndElimL(u.hyp("first")),bound,u.hyp("a_entry"))
            return eliminate(u,actual,("r","x","y"),"term",decoded)
        point = introduce(t,("j","k","a","b"),("index","a_entry","b_entry"),pointwise)
        return apply(specialize(t,"reverse",*t.terms(("i","db","dc","eb","ec","n","m"))),AndElimR(t.hyp("first")),AndElimR(t.hyp("second")),point)
    return introduce(s,P+("i","n","m"),("left","right"),lambda t:
        eliminate(t,t.hyp("left"),("db","dc"),"first",lambda u:
            eliminate(u,u.hyp("right"),("eb","ec"),"second",finish)))


def _root(s,registry):
    from peano_lab.kernel.proofs import AndIntro,EqSym
    def finish(t):
        equality = apply(specialize(t,"commute",*t.terms(P+("i","n","m"))),t.hyp("left"),t.hyp("right"))
        right = _subst(t,registry,coefficient(B,A,"i","slot"),EqSym(equality),t.hyp("right"))
        return witness((t.term("n"),),AndIntro(t.hyp("left"),right))
    return introduce(s,P+("i",),(),lambda t:
        eliminate(t,specialize(t,"coefficient_exists",*t.terms(P+("i",))),("n",),"left",lambda u:
            eliminate(u,specialize(u,"coefficient_exists",*u.terms(B+A+("i",))),("m",),"right",finish)))


@dataclass(frozen=True)
class ConvolutionCommutativeCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_convolution_commutative(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise ConvolutionCommutativeError("expected unchanged BinaryDAGLimits")
    before = convolution_commutative_source_pins()
    registry,target = definition_registry(),frozen_convolution_commutative_target()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise ConvolutionCommutativeError("exact reversal/commutative helper target changed")
    formulas["CV010"] = target
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    for pin in (CONVOLUTION_ARCHIVE,SPLIT_ARCHIVE):
        original = read_archive(pin)
        remap = {}
        for old,r in enumerate(original):
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise ConvolutionCommutativeError("actual ancestor ordered dependencies changed")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise ConvolutionCommutativeError("merged ancestor body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        for name,source in ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=registry))
            matches = [i for i,r in enumerate(original) if r[1]==formula]
            if len(matches)>1:
                raise ConvolutionCommutativeError("ambiguous actual endpoint: "+name)
            if matches:
                if name in endpoints and endpoints[name]!=remap[matches[0]]:
                    raise ConvolutionCommutativeError("shared actual endpoint bodies disagree")
                endpoints[name] = remap[matches[0]]
        del original,remap
        gc.collect()
    if endpoints.keys()!=ENDPOINT_SOURCES.keys():
        raise ConvolutionCommutativeError("missing actual ancestor endpoint")
    ancestor_count = len(rows)
    factories = {"sum_one":_sum_one,"head_tail":lambda s:_head_tail(s,registry),
        "reverse":lambda s:_reverse(s,formulas["reverse"],registry),"commute":lambda s:_commute(s,registry),"CV010":lambda s:_root(s,registry)}
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise ConvolutionCommutativeError("commutative aggregate body/node bound exceeded")
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
        raise ConvolutionCommutativeError("commutative canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise ConvolutionCommutativeError("decoded commutative coefficient target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or convolution_commutative_source_pins()!=before:
        raise ConvolutionCommutativeError("commutative target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,coefficientwise_natural_commutativity=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        convolution_archive=dict(CONVOLUTION_ARCHIVE),split_archive=dict(SPLIT_ARCHIVE),
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),helper_bundle_indices=helper_indices,
        new_induction_count=1,ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return ConvolutionCommutativeCertificate(target,bundle,payload,receipt,deepest,provenance)
