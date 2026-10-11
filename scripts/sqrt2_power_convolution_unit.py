"""CV016: the actual truncated unit is an identity below its width.

Construct the unit and the padded input coefficient. An actual antidiagonal
has that value at zero and zero everywhere else. Finite sum witnesses, not
an assumed unit or polynomial evaluation law, identify its total.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256

from sqrt2_power_series_power_trace import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,_inert_metrics,definition_registry,series_power_trace_source_pins,
    CONVOLUTION_ARCHIVE,read_archive,HELPER_SOURCES as POWER_HELPERS,
)
from sqrt2_power_series_power_vanishing import POWER_ARCHIVE
from sqrt2_power_convolution_associative import COMM_ARCHIVE
from sqrt2_power_triple_row_sum import ZERO_TAIL_ARCHIVE
from sqrt2_power_convolution_commutative import HELPER_SOURCES as COMM_HELPERS
from sqrt2_power_sum_zero_tail import NAMED_SOURCE as ZERO_TAIL_SOURCE
from sqrt2_power_euler_product import coefficient

SCHEMA = "sqrt2-power-convolution-unit-v1"
P = ("ab","ac","L","H","i")
A,U = ("ab","ac","L"),("ub","uc","H")
UNIT = "NatUnitPrefix(ub,uc,H)"
PAD = "BetaZeroExtend(ab,ac,L,i,a)"
NAMED_SOURCE = "forall "+" ".join(P)+". Lt(i,H) -> exists ub uc a. "+UNIT+" /\\ ("+PAD+" /\\ "+coefficient(U,A,"i","a")+")"
TARGET_SHA256 = "80e61d585bc00d1ae1a6ea2c87fb652ee553927823efe339412d1d7e39c7b5d4"
HELPER_SOURCES = {
    "unit_entry":"forall ub uc H i a. "+UNIT+" -> Lt(i,H) -> BetaAt(ub,uc,i,a) -> NatUnitCoefficient(i,a)",
    "unit_zero":"forall ub uc H. "+UNIT+" -> Lt(0,H) -> BetaZeroExtend(ub,uc,H,0,1)",
    "unit_positive":"forall ub uc H j a. "+UNIT+" -> ~j=0 -> BetaZeroExtend(ub,uc,H,j,a) -> a=0",
    "unit_term":"forall ab ac L H ub uc i j t. "+UNIT+" -> ~j=0 -> PolynomialDiagonalTerm(ub,uc,H,ab,ac,L,i,j,t) -> t=0",
    "unit_coefficient":"forall "+" ".join(P+("ub","uc","a"))+". "+UNIT+" -> Lt(i,H) -> "+PAD+" -> "+coefficient(U,A,"i","a"),
}
HELPER_TARGET_SHA256 = {
    "unit_entry":"41d8ad3332507be90512e3fc8a2892b2b49afba817e09ba962f0db2336cffed5",
    "unit_zero":"a1ea50f12e7a4b726bc9b085499390fa333be7f501cd1b13bf37b4a9abe9ca4c",
    "unit_positive":"1d1e01468aa510b3610add8cf1a2e8c8005974a203978c723d04f6e098742c12",
    "unit_term":"9d78c62cd3f2358a50e83542a6db62acdf8c64674a159abe2ce51fe42697ec9a",
    "unit_coefficient":"c5111a5ed603e6788383af4ab9c346379a84d31864593b3cb9f4ae08d89c7346",
}
ARCHIVES = (CONVOLUTION_ARCHIVE,POWER_ARCHIVE,COMM_ARCHIVE,ZERO_TAIL_ARCHIVE)
ENDPOINT_SOURCES = {
    "zero_add":"forall a. 0+a=a",
    "add_succ_left":"forall a b. S a+b=S(a+b)",
    "one_mul":"forall a. 1*a=a",
    "mul_zero_left":"forall a. 0*a=0",
    "succ_ne_zero":"forall a. ~S a=0",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "zero_le":"forall a. Le(0,a)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "padding_exists":"forall b c L i. exists a. BetaZeroExtend(b,c,L,i,a)",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "sum_unique":"forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m",
    "term_unique":"forall ab ac L bb bc M i j t s. PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,s) -> t=s",
    "diagonal_entry":"forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)",
    "coefficient_exists":"forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)",
    "unit_exists":POWER_HELPERS["unit_exists"],
    "sum_one":COMM_HELPERS["sum_one"],
    "zero_tail":ZERO_TAIL_SOURCE,
}
HELPER_DEPENDENCIES = {
    "unit_entry":("beta_unique",),
    "unit_zero":("beta_exists","unit_entry","succ_ne_zero"),
    "unit_positive":("unit_entry",),
    "unit_term":("unit_positive","mul_zero_left"),
    "unit_coefficient":("coefficient_exists","beta_exists","zero_le","succ_le_succ","le_trans","unit_zero",
        "zero_add","one_mul","term_unique","diagonal_entry","sum_exists","sum_one","add_succ_left","succ_ne_zero","unit_term","zero_tail","sum_unique"),
    "CV016":("unit_exists","padding_exists","unit_coefficient"),
}


class ConvolutionUnitError(ValueError):
    """Changed unit computation, actual dependency, target, or resource cap."""


def frozen_convolution_unit_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionUnitError("CV016 exact constructed unit target changed")
    return target


def source_contract():
    return dict(code="CV016",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,coefficient_index_below_unit_width_required=True,
        actual_unit_and_padded_coefficient_constructed=True,arbitrary_input_length=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",exp_composition_recurrence=False,
        analytic_limit_claim=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def convolution_unit_source_pins():
    result = series_power_trace_source_pins()
    expected = {
        "scripts/sqrt2_power_series_power_trace.py":"557d393791fb527361bcffb4977b0e0bad591f98a426e12d1da461643cc39422",
        "scripts/sqrt2_power_series_power_vanishing.py":"ea3e1d648fd35f5430d0e19c442bc06031b849c570ddd4b7315522eba468edab",
        "scripts/sqrt2_power_convolution_associative.py":"a7a442ad853eeb7c1eb0cbd15b552eb9e7213419d44ed86e1314a7e2f1a1c931",
        "scripts/sqrt2_power_triple_row_sum.py":"d0ee57d361f2f714862761de9416595e4520c1abd2597986a3cbef2e39dab345",
        "scripts/sqrt2_power_convolution_commutative.py":"d1d4ce7c0e78c03ba5961710b048fe11bcb3dd481afd2e79d5cc2b418b0412a3",
        "scripts/sqrt2_power_sum_zero_tail.py":"a4112bbf650aa6dfedf3204463a88d4d82ec3ab9f55948ad54c9423208f7d223",
        "scripts/sqrt2_power_euler_product.py":"c26512518de941c9f8c54bfe682732d601158748f25955166b3ea6d8290afa10",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_convolution_unit.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionUnitError("unit source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _subst(s,registry,source,equality,proof):
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import EqSubst
    return EqSubst(parse_named(source,s.variable("slot").variables,registry),equality,proof)


def _unit_entry(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    def decoded(t):
        equal = apply(specialize(t,"beta_unique",*t.terms(("ub","uc","i","v","a"))),AndElimL(t.hyp("value")),t.hyp("input"))
        return _subst(t,registry,"NatUnitCoefficient(i,slot)",equal,AndElimR(t.hyp("value")))
    return introduce(s,("ub","uc","H","i","a"),("unit","bound","input"),lambda t:
        eliminate(t,apply(specialize(t,"unit",t.term("i")),t.hyp("bound")),("v",),"value",decoded))


def _unit_zero(s,registry):
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR,BotElim,EqSym,OrElim,OrIntroL
    from peano_lab.kernel.terms import Zero
    def decoded(t):
        value = apply(specialize(t,"unit_entry",*t.terms(U),Zero(),t.term("a")),t.hyp("unit"),t.hyp("bound"),t.hyp("value"))
        left,right = t.hypothesis("at_zero"),t.hypothesis("positive")
        first = OrIntroL(AndIntro(left.hyp("bound"),_subst(left,registry,"BetaAt(ub,uc,0,slot)",AndElimR(left.hyp("at_zero")),left.hyp("value"))))
        second = eliminate(right,right.hyp("positive"),("k",),"data",lambda u:
            BotElim(apply(specialize(u,"succ_ne_zero",u.term("k")),EqSym(AndElimL(u.hyp("data"))))))
        return OrElim(value,first,second)
    return introduce(s,U,("unit","bound"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(U[:2]),Zero()),("a",),"value",decoded))


def _unit_positive(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,OrElim
    def finish(t):
        inside,outside = t.hypothesis("inside"),t.hypothesis("outside")
        value = apply(specialize(inside,"unit_entry",*inside.terms(U+("j","a"))),
            inside.hyp("unit"),AndElimL(inside.hyp("inside")),AndElimR(inside.hyp("inside")))
        left,right = inside.hypothesis("at_zero"),inside.hypothesis("positive")
        first = BotElim(apply(left.hyp("nonzero"),AndElimL(left.hyp("at_zero"))))
        second = eliminate(right,right.hyp("positive"),("k",),"data",lambda u:AndElimR(u.hyp("data")))
        return OrElim(t.hyp("padding"),OrElim(value,first,second),AndElimR(outside.hyp("outside")))
    return introduce(s,U+("j","a"),("unit","nonzero","padding"),finish)


def _unit_term(s):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqTrans
    def decoded(t):
        zero = apply(specialize(t,"unit_positive",*t.terms(U+("j","x"))),t.hyp("unit"),t.hyp("nonzero"),field(t.hyp("data"),1,4))
        return EqTrans(field(t.hyp("data"),3,4),EqTrans(CongMul(zero,EqRefl(t.term("y"))),specialize(t,"mul_zero_left",t.term("y"))))
    return introduce(s,("ab","ac","L","H","ub","uc","i","j","t"),("unit","nonzero","cell"),lambda t:
        eliminate(t,t.hyp("cell"),("k","x","y"),"data",decoded))


def _one_plus(s,value):
    from peano_lab.kernel.proofs import CongS,EqTrans
    from peano_lab.kernel.terms import Zero
    return EqTrans(specialize(s,"add_succ_left",Zero(),value),CongS(specialize(s,"zero_add",value)))


def _unit_coefficient(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl,EqSym,OrIntroL
    from peano_lab.kernel.terms import Add,Succ,Zero
    one = Succ(Zero())
    def first_value(t):
        i,a,x = t.terms(("i","a","x"))
        small = apply(specialize(t,"succ_le_succ",Zero(),i),specialize(t,"zero_le",i))
        unit_bound = apply(specialize(t,"le_trans",one,Succ(i),t.term("H")),small,t.hyp("bound"))
        unit_value = apply(specialize(t,"unit_zero",*t.terms(U)),t.hyp("unit"),unit_bound)
        first_cell = witness((i,one,a),conjunction(specialize(t,"zero_add",i),unit_value,t.hyp("padding"),EqSym(specialize(t,"one_mul",a))))
        actual = apply(specialize(t,"diagonal_entry",*t.terms(U+A+("i","xb","xc")),Succ(i),Zero(),x),
            AndElimL(t.hyp("diagonal")),small,t.hyp("first"))
        equal = apply(specialize(t,"term_unique",*t.terms(U+A+("i",)),Zero(),x,a),actual,first_cell)
        return _subst(t,registry,"BetaAt(xb,xc,0,slot)",equal,t.hyp("first"))
    def total(t):
        def sum_ready(u):
            first = first_value(u)
            same = apply(specialize(u,"sum_one",*u.terms(("xb","xc","v","a"))),u.hyp("single"),first)
            single = _subst(u,registry,"Sum(xb,xc,1,slot)",same,u.hyp("single"))
            def tail(v):
                def at(w):
                    h,y = w.terms(("h","y"))
                    plus = _one_plus(w,h)
                    small = apply(specialize(w,"succ_le_succ",Succ(h),w.term("i")),w.hyp("tail_bound"))
                    bound = _subst(w,registry,"Lt(slot,S i)",EqSym(plus),small)
                    nonzero = _subst(w,registry,"~slot=0",EqSym(plus),specialize(w,"succ_ne_zero",h))
                    actual = apply(specialize(w,"diagonal_entry",*w.terms(U+A+("i","xb","xc")),Succ(w.term("i")),Add(one,h),y),
                        AndElimL(w.hyp("diagonal")),bound,w.hyp("tail_value"))
                    zero = apply(specialize(w,"unit_term",*w.terms(("ab","ac","L","H","ub","uc","i")),Add(one,h),y),
                        w.hyp("unit"),nonzero,actual)
                    return _subst(w,registry,"BetaAt(xb,xc,1+h,slot)",zero,w.hyp("tail_value"))
                return eliminate(v,specialize(v,"beta_exists",*v.terms(("xb","xc")),Add(one,v.term("h"))),("y",),"tail_value",at)
            zeros = introduce(u,("h",),("tail_bound",),tail)
            extended = apply(specialize(u,"zero_tail",*u.terms(("xb","xc")),one,*u.terms(("i","a"))),single,zeros)
            summed = _subst(u,registry,"Sum(xb,xc,slot,a)",_one_plus(u,u.term("i")),extended)
            equal = apply(specialize(u,"sum_unique",*u.terms(("xb","xc")),Succ(u.term("i")),*u.terms(("n","a"))),AndElimR(u.hyp("diagonal")),summed)
            return _subst(u,registry,coefficient(U,A,"i","slot"),equal,u.hyp("coefficient"))
        return eliminate(t,specialize(t,"sum_exists",*t.terms(("xb","xc")),one),("v",),"single",sum_ready)
    def diagonal(t):
        return eliminate(t,specialize(t,"beta_exists",*t.terms(("xb","xc")),Zero()),("x",),"first",total)
    return introduce(s,P+("ub","uc","a"),("unit","bound","padding"),lambda t:
        eliminate(t,specialize(t,"coefficient_exists",*t.terms(U+A+("i",))),("n",),"coefficient",lambda u:
            eliminate(u,u.hyp("coefficient"),("xb","xc"),"diagonal",diagonal)))


def _root(s):
    def finish(t):
        value = apply(specialize(t,"unit_coefficient",*t.terms(P+("ub","uc","a"))),t.hyp("unit"),t.hyp("bound"),t.hyp("padding"))
        return witness(t.terms(("ub","uc","a")),conjunction(t.hyp("unit"),t.hyp("padding"),value))
    return introduce(s,P,("bound",),lambda t:
        eliminate(t,specialize(t,"unit_exists",t.term("H")),U[:2],"unit",lambda u:
            eliminate(u,specialize(u,"padding_exists",*u.terms(A+("i",))),("a",),"padding",finish)))


@dataclass(frozen=True)
class FiniteSeriesCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def assemble_actual_certificate(*,code,target,registry,helper_sources,helper_hashes,
        endpoint_sources,archives,dependencies,factories,pins,contract,limits=None,
        new_induction_count=0):
    """Untrusted bookkeeping only; replay every retained ordinary proof body.

    Exact formulas select bodies from authenticated archives, not theorem names.
    Full canonical row bytes alone deduplicate; ordered dependencies are remapped.
    No supplied metadata or prior checker receipt substitutes for replay.
    """
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise ConvolutionUnitError("expected unchanged BinaryDAGLimits")
    before = pins()
    formulas = {name:parse_named(source,registry=registry) for name,source in helper_sources.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=helper_hashes:
        raise ConvolutionUnitError("exact finite-series helper target changed")
    formulas[code] = target
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    for pin in archives:
        original = read_archive(pin)
        remap = {}
        for old,r in enumerate(original):
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise ConvolutionUnitError("actual ancestor ordered dependencies changed")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if type(r[0]) is not int or r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise ConvolutionUnitError("merged ancestor body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        for name,source in endpoint_sources.items():
            formula = encode_formula(parse_named(source,registry=registry))
            matches = [i for i,r in enumerate(original) if r[1]==formula]
            if len(matches)>1:
                raise ConvolutionUnitError("ambiguous actual endpoint: "+name)
            if matches:
                if name in endpoints and endpoints[name]!=remap[matches[0]]:
                    raise ConvolutionUnitError("shared actual endpoint bodies disagree")
                endpoints[name] = remap[matches[0]]
        del original,remap
        gc.collect()
    if endpoints.keys()!=endpoint_sources.keys():
        raise ConvolutionUnitError("missing actual finite-series ancestor endpoint: "+str(endpoint_sources.keys()-endpoints.keys()))
    ancestor_count = len(rows)
    for name,deps in dependencies.items():
        body = introduce(Scope(),(),deps,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise ConvolutionUnitError("finite-series aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in deps],encode_proof(body)])
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
    helper_indices = {name:remap[endpoints[name]] for name in dependencies}
    rows = [[rows[old][0],rows[old][1],[remap[d] for d in rows[old][2]],rows[old][3]] for old in retained]
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise ConvolutionUnitError("finite-series canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise ConvolutionUnitError("decoded finite-series target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or pins()!=before:
        raise ConvolutionUnitError("finite-series target/source changed during replay")
    provenance = dict(contract,source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        actual_archives=[dict(pin) for pin in archives],
        helper_statement_ast_sha256=dict(helper_hashes),helper_bundle_indices=helper_indices,
        new_induction_count=new_induction_count,ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return FiniteSeriesCertificate(target,bundle,payload,receipt,deepest,provenance)


def prove_convolution_unit(*,limits=None):
    registry = definition_registry()
    factories = {"unit_entry":lambda s:_unit_entry(s,registry),
        "unit_zero":lambda s:_unit_zero(s,registry),"unit_positive":_unit_positive,
        "unit_term":_unit_term,"unit_coefficient":lambda s:_unit_coefficient(s,registry),"CV016":_root}
    return assemble_actual_certificate(code="CV016",target=frozen_convolution_unit_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=convolution_unit_source_pins,
        contract=source_contract(),limits=limits)
