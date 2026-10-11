"""CV007: construct both Euler prefixes and prove the natural Cauchy product rule.

E(A)[i]=i*A[i]. The root constructs all derivative prefixes and three actual
convolution coefficients, then proves i*(A*B)[i]=(EA*B)[i]+(A*EB)[i]. No real
analysis, subtraction, rational division, or derivative-product law is an axiom.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_natural_convolution import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,
    canonical,json_hash,_inert_metrics,ANCESTOR_IDS as CONVOLUTION_ANCESTORS,
    definition_registry as convolution_registry,
)
from sqrt2_power_sum_linearity import (
    sum_linearity_source_pins,definition_registry as linearity_registry,LINEARITY_SOURCE,
)
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_quadratic_product_exists import read_archive

SCHEMA = "sqrt2-power-euler-product-v1"
P = ("ab","ac","L","bb","bc","M")
D = ("db","dc","eb","ec")


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def coefficient(left,right,index,value):
    return "NatConvolutionCoefficient("+",".join(left+right+(index,value))+")"


def euler(old,new,length):
    return "NatEulerPrefix("+",".join(old+new+(length,))+")"


A,B,EA,EB = ("ab","ac","L"),("bb","bc","M"),("db","dc","L"),("eb","ec","M")
EULER_A = euler(A[:2],EA[:2],"L")
EULER_B = euler(B[:2],EB[:2],"M")
DEFINITION_SOURCE = "forall i a. Lt(i,L) -> BetaAt(ab,ac,i,a) -> BetaAt(db,dc,i,i*a)"
DEFINITION_SHA256 = "d39ccc26711b0b424958737f123cb6acbcfa5970992c39adb153f777564d2771"
NAMED_SOURCE = forall(P+("i",),"exists "+" ".join(D+("p","q","r"))+". "+
    EULER_A+" /\\ ("+EULER_B+" /\\ ("+coefficient(A,B,"i","p")+" /\\ ("+
    coefficient(EA,B,"i","q")+" /\\ ("+coefficient(A,EB,"i","r")+" /\\ i*p=q+r))))")
TARGET_SHA256 = "f8bff474361b2be3a4a2a9c81b30cdb9c317dd510ffdaf1ac64fa5762046cbea"
HELPER_SOURCES = {
    "euler_exists":"forall ab ac L. exists db dc. NatEulerPrefix(ab,ac,db,dc,L)",
    "euler_padding":"forall ab ac db dc L i a. NatEulerPrefix(ab,ac,db,dc,L) -> BetaZeroExtend(ab,ac,L,i,a) -> BetaZeroExtend(db,dc,L,i,i*a)",
    "product_rule":forall(P+D+("i","p","q","r"),EULER_A+" -> "+EULER_B+" -> "+
        coefficient(A,B,"i","p")+" -> "+coefficient(EA,B,"i","q")+" -> "+coefficient(A,EB,"i","r")+" -> i*p=q+r"),
}
HELPER_TARGET_SHA256 = {
    "euler_exists":"12e112ba31e3916343b765b47ce09141f7d9fd859906ae4fc070982c2a9b2577",
    "euler_padding":"87496727b88094b11093bd2a2b4b05921fd2e7be6c157d4193637289fe7796d7",
    "product_rule":"ed6e9fe4520db920860f551ea01006a27c654f9109de49a93c988a43469352c6",
}
LINEARITY_ARCHIVE = dict(case="CV006",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-sum-linearity-v1/generation-process.json.gz",
    bytes=19607,sha256="63770ed644139fffa6b913e01951f4f9dca38cea8fc36148739319ebc2ecc836",
    raw_bytes=320274,raw_sha256="264db6c0765c0142f3c5d1c6e304ef88ea4de2a8ef378d4a084fc590d9176951",
    bundle_bytes=192535,bundle_sha256="87db349766e9779113c3e954f52700942c6f15137bb7082e87497ce8c65d5c10",
    nodes=109,root=108,target_ast_sha256="bcf6a93be452d1bf0a424cda787eca7580644608eb69a236c5d1c99c3acea02a")
ENDPOINT_SOURCES = {
    "mul_comm":(6,"forall a b. a*b=b*a"),
    "mul_assoc":(8,"forall a b c. (a*b)*c=a*(b*c)"),
    "one_mul":(9,"forall a. 1*a=a"),
    "add_mul":(11,"forall a b c. (a+b)*c=a*c+b*c"),
    "zero_le":(24,"forall a. Le(0,a)"),
    "le_of_succ_le_succ":(33,"forall a b. Le(S a,S b) -> Le(a,b)"),
    "le_eq_or_lt":(37,"forall a b. Le(a,b) -> a=b \\/ Lt(a,b)"),
    "lt_not_le":(40,"forall a b. Lt(a,b) -> Le(b,a) -> false"),
    "beta_at_exists":(87,"forall b c i. exists a. BetaAt(b,c,i,a)"),
    "beta_at_unique":(88,"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d"),
    "beta_prefix_extend":(116,"forall N b c v. exists eb ec. BetaAt(eb,ec,N,v) /\\ (forall j a. Lt(j,N) -> BetaAt(b,c,j,a) -> BetaAt(eb,ec,j,a))"),
    "term_unique":(162,"forall ab ac L bb bc M i j t s. PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,t) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,i,j,s) -> t=s"),
    "diagonal_entry":(168,"forall ab ac L bb bc M I db dc N i a. PolynomialDiagonalPrefix(ab,ac,L,bb,bc,M,I,db,dc,N) -> Lt(i,N) -> BetaAt(db,dc,i,a) -> PolynomialDiagonalTerm(ab,ac,L,bb,bc,M,I,i,a)"),
}
HELPER_DEPENDENCIES = {
    "euler_exists":("zero_le","lt_not_le","le_of_succ_le_succ","le_eq_or_lt","beta_at_exists","beta_at_unique","beta_prefix_extend"),
    "euler_padding":(),
    "product_rule":("mul_comm","mul_assoc","one_mul","add_mul","diagonal_entry","term_unique","linearity","euler_padding"),
    "CV007":("euler_exists","coefficient_exists","product_rule"),
}


class EulerProductError(ValueError):
    """Changed exact computation, actual ancestor, target or resource cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(convolution_registry())
    for name,d in linearity_registry().items():
        if name in registry and (registry[name].template_formula!=d.template_formula or registry[name].stable_id!=d.stable_id):
            raise EulerProductError("shared definition disagreement")
        registry[name] = d
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    name,identifier,parameters = "NatEulerPrefix","ND0410",("ab","ac","db","dc","L")
    if name in registry or any(d["name"]==name or d["id"]==identifier for d in parent):
        raise EulerProductError("Euler computation alias collision")
    formula = parse_named(DEFINITION_SOURCE,parameters,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise EulerProductError("Euler computation exact expansion changed")
    text = pretty_formula(formula,list(parameters))
    d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
        summary="Actual coefficientwise multiplication by the index; no product rule or analytic derivative assertion.",
        category="irrationality_formal_series",conceptual_dependencies=("Lt","BetaAt"))
    if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
        raise EulerProductError("Euler computation failed exact expansion roundtrip")
    registry[name] = d
    return MappingProxyType(registry)


def frozen_euler_product_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise EulerProductError("CV007 unconditional Euler product target changed")
    return target


def source_contract():
    return dict(code="CV007",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,arbitrary_input_lengths_and_coefficient_index=True,
        both_euler_prefixes_constructed=True,all_three_coefficients_constructed=True,
        coefficient_order="ascending_series",operator="E(A)[i]=i*A[i]",
        new_definition_ids=["ND0410"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",ordinary_shifted_derivative=False,
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def euler_product_source_pins():
    result = sum_linearity_source_pins()
    expected = {"scripts/sqrt2_power_sum_linearity.py":"5a9131119953036d5bb1c7cb2b08e26bcc4fa63fd31a8c0cbc77409f17358bc0",
        "scripts/sqrt2_power_series_power_trace.py":"557d393791fb527361bcffb4977b0e0bad591f98a426e12d1da461643cc39422",
        "scripts/sqrt2_power_quadratic_product_exists.py":"c20c38bfceb78fa16c236925024a43c12624b2df23937bb1c1e9f54393d49017",
        CONVOLUTION_ARCHIVE["path"]:CONVOLUTION_ARCHIVE["sha256"],LINEARITY_ARCHIVE["path"]:LINEARITY_ARCHIVE["sha256"]}
    for name in (*expected,"scripts/sqrt2_power_euler_product.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise EulerProductError("Euler product source or actual proof archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _euler_exists(s,target,registry):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,CongMul,EqRefl,EqSubst,EqSym,Ind,OrElim
    from peano_lab.kernel.terms import Mul,Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("i","a"),("bound","input"),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("i"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("i"))))))
    def step(t):
        def old(u):
            def value(v):
                def extended(w):
                    def entry(x):
                        def last(y):
                            def subst(source,equality,proof):
                                motive = parse_named(source,y.variable("slot").variables,registry)
                                return EqSubst(motive,equality,proof)
                            at_end = subst("BetaAt(ab,ac,slot,a)",y.hyp("last"),y.hyp("input"))
                            same = apply(specialize(y,"beta_at_unique",*y.terms(("ab","ac","L","v","a"))),y.hyp("value"),at_end)
                            output = subst("BetaAt(db,dc,L,slot)",CongMul(EqRefl(y.term("L")),same),AndElimL(y.hyp("extension")))
                            return subst("BetaAt(db,dc,slot,slot*a)",EqSym(y.hyp("last")),output)
                        def earlier(y):
                            old_value = apply(specialize(y,"old",*y.terms(("i","a"))),y.hyp("earlier"),y.hyp("input"))
                            return apply(instantiate(AndElimR(y.hyp("extension")),y.term("i"),Mul(y.term("i"),y.term("a"))),y.hyp("earlier"),old_value)
                        lower = apply(specialize(x,"le_of_succ_le_succ",*x.terms(("i","L"))),x.hyp("bound"))
                        cases = apply(specialize(x,"le_eq_or_lt",*x.terms(("i","L"))),lower)
                        return OrElim(cases,last(x.hypothesis("last")),earlier(x.hypothesis("earlier")))
                    return witness(w.terms(("db","dc")),introduce(w,("i","a"),("bound","input"),entry))
                extension = specialize(v,"beta_prefix_extend",*v.terms(("L","ob","oc")),Mul(v.term("L"),v.term("v")))
                return eliminate(v,extension,("db","dc"),"extension",extended)
            return eliminate(u,specialize(u,"beta_at_exists",*u.terms(("ab","ac","L"))),("v",),"value",value)
        return eliminate(t,t.hyp("IH"),("ob","oc"),"old",old)
    motive = target.body.body.body
    return introduce(s,("ab","ac"),(),lambda t:Ind(motive,base(t),introduce(t,("L",),("IH",),step)))


def _euler_padding(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndIntro,AndElimL,AndElimR,CongMul,EqRefl,EqTrans,OrIntroL,OrIntroR,OrElim
    def finish(t):
        left,right = t.hypothesis("inside"),t.hypothesis("outside")
        computed = apply(specialize(left,"euler",*left.terms(("i","a"))),AndElimL(left.hyp("inside")),AndElimR(left.hyp("inside")))
        zero = EqTrans(CongMul(EqRefl(right.term("i")),AndElimR(right.hyp("outside"))),instantiate(Axiom("PA5"),right.term("i")))
        return OrElim(t.hyp("padded"),OrIntroL(AndIntro(AndElimL(left.hyp("inside")),computed)),OrIntroR(AndIntro(AndElimL(right.hyp("outside")),zero)))
    return introduce(s,("ab","ac","db","dc","L","i","a"),("euler","padded"),finish)


def _product_rule(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    from sqrt2_power_quadratic_trace_exists import conjunction
    def finish(t):
        def pointwise(u):
            def original(v):
                i,j,k,a,b = v.terms(("i","j","k","a","b"))
                x,y,z = v.terms(("x","y","z"))
                original_term = v.hyp("term")
                pad_a,pad_b = field(original_term,1,4),field(original_term,2,4)
                ea = apply(specialize(v,"euler_padding",*v.terms(("ab","ac","db","dc","L")),j,a),v.hyp("euler_a"),pad_a)
                eb = apply(specialize(v,"euler_padding",*v.terms(("bb","bc","eb","ec","M")),k,b),v.hyp("euler_b"),pad_b)
                left_value,right_value = Mul(Mul(j,a),b),Mul(a,Mul(k,b))
                left_constructed = witness((k,Mul(j,a),b),conjunction(field(original_term,0,4),ea,pad_b,EqRefl(left_value)))
                right_constructed = witness((k,a,Mul(k,b)),conjunction(field(original_term,0,4),pad_a,eb,EqRefl(right_value)))
                def diagonal(inputs,codes,label,entry,value):
                    return apply(specialize(v,"diagonal_entry",*v.terms(inputs),i,*v.terms(codes),Succ(i),j,value),
                        AndElimL(v.hyp(label)),v.hyp("bound"),v.hyp(entry))
                left_actual = diagonal(EA+B,("yb","yc"),"left_product","left_entry",x)
                right_actual = diagonal(A+EB,("zb","zc"),"right_product","right_entry",y)
                left_equal = apply(specialize(v,"term_unique",*v.terms(EA+B),i,j,x,left_value),left_actual,left_constructed)
                right_equal = apply(specialize(v,"term_unique",*v.terms(A+EB),i,j,y,right_value),right_actual,right_constructed)
                exchange = _chain(EqSym(specialize(v,"mul_assoc",k,a,b)),CongMul(specialize(v,"mul_comm",k,a),EqRefl(b)),specialize(v,"mul_assoc",a,k,b))
                return _chain(CongMul(EqRefl(i),field(original_term,3,4)),
                    CongMul(EqSym(field(original_term,0,4)),EqRefl(Mul(a,b))),
                    specialize(v,"add_mul",j,k,Mul(a,b)),
                    CongAdd(EqSym(specialize(v,"mul_assoc",j,a,b)),exchange),
                    CongAdd(EqSym(left_equal),EqSym(right_equal)),
                    CongAdd(EqSym(specialize(v,"one_mul",x)),EqSym(specialize(v,"one_mul",y))))
            actual = apply(specialize(u,"diagonal_entry",*u.terms(P+("i","xb","xc")),Succ(u.term("i")),*u.terms(("j","z"))),
                AndElimL(u.hyp("product")),u.hyp("bound"),u.hyp("original_entry"))
            return eliminate(u,actual,("k","a","b"),"term",original)
        points = introduce(t,("j","x","y","z"),("bound","left_entry","right_entry","original_entry"),pointwise)
        one = Succ(Zero())
        identity = apply(specialize(t,"linearity",one,one,t.term("i"),*t.terms(("yb","yc","zb","zc","xb","xc")),
            Succ(t.term("i")),*t.terms(("q","r","p"))),
            AndElimR(t.hyp("left_product")),AndElimR(t.hyp("right_product")),AndElimR(t.hyp("product")),points)
        return _chain(identity,CongAdd(specialize(t,"one_mul",t.term("q")),specialize(t,"one_mul",t.term("r"))))
    return introduce(s,P+D+("i","p","q","r"),("euler_a","euler_b","source_p","source_q","source_r"),lambda t:
        eliminate(t,t.hyp("source_p"),("xb","xc"),"product",lambda u:
            eliminate(u,u.hyp("source_q"),("yb","yc"),"left_product",lambda v:
                eliminate(v,v.hyp("source_r"),("zb","zc"),"right_product",finish))))


def _root(s):
    from sqrt2_power_quadratic_trace_exists import conjunction
    def all_values(t):
        identity = apply(specialize(t,"product_rule",*t.terms(P+D+("i","p","q","r"))),
            *(t.hyp(name) for name in ("euler_a","euler_b","product","left_product","right_product")))
        return witness(t.terms(D+("p","q","r")),conjunction(
            *(t.hyp(name) for name in ("euler_a","euler_b","product","left_product","right_product")),identity))
    def coefficients(t,position):
        if position==3:
            return all_values(t)
        inputs,value,label = ((A+B,"p","product"),(EA+B,"q","left_product"),(A+EB,"r","right_product"))[position]
        source = specialize(t,"coefficient_exists",*t.terms(inputs),t.term("i"))
        return eliminate(t,source,(value,),label,lambda u:coefficients(u,position+1))
    return introduce(s,P+("i",),(),lambda t:
        eliminate(t,specialize(t,"euler_exists",*t.terms(A)),D[:2],"euler_a",lambda u:
            eliminate(u,specialize(u,"euler_exists",*u.terms(B)),D[2:],"euler_b",lambda v:coefficients(v,0))))


@dataclass(frozen=True)
class EulerProductCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_euler_product(*,limits=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise EulerProductError("expected unchanged BinaryDAGLimits")
    before = euler_product_source_pins()
    registry,target = definition_registry(),frozen_euler_product_target()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise EulerProductError("Euler product exact helper target changed")
    formulas["CV007"] = target
    rows,keys,endpoints = [],{},{}
    total,deepest = 0,0
    for pin in (CONVOLUTION_ARCHIVE,LINEARITY_ARCHIVE):
        original = read_archive(pin)
        remap = {}
        for old,r in enumerate(original):
            if len(r)!=4 or len(r[2])!=len(set(r[2])) or any(type(d) is not int or not 0<=d<old for d in r[2]):
                raise EulerProductError("actual ancestor ordered dependencies changed")
            linked = [r[0],r[1],[remap[d] for d in r[2]],r[3]]
            key = canonical(linked)
            if key not in keys:
                count,depth = _inert_metrics(r[3],limits)
                total,deepest = total+count,max(deepest,depth)
                if type(r[0]) is not int or r[0]<8*count+16 or total>limits.max_total_body_nodes or len(rows)+1>=limits.max_nodes:
                    raise EulerProductError("merged Euler ancestor body/node/fuel bound exceeded")
                keys[key] = len(rows)
                rows.append(linked)
            remap[old] = keys[key]
        if pin["case"]=="CV003":
            for name,(old,source) in ENDPOINT_SOURCES.items():
                local = CONVOLUTION_ANCESTORS.index(old)
                if original[local][1]!=encode_formula(parse_named(source,registry=registry)):
                    raise EulerProductError("actual Euler ancestor differs from exact endpoint source")
                endpoints[name] = remap[local]
            endpoints["coefficient_exists"] = remap[120]
            source = "forall ab ac L bb bc M i. exists n. NatConvolutionCoefficient(ab,ac,L,bb,bc,M,i,n)"
            if original[120][1]!=encode_formula(parse_named(source,registry=registry)):
                raise EulerProductError("actual natural coefficient-existence endpoint changed")
        else:
            if original[107][1]!=encode_formula(parse_named(LINEARITY_SOURCE,registry=registry)):
                raise EulerProductError("actual all-lengths sum linearity endpoint changed")
            endpoints["linearity"] = remap[107]
        del original,remap
        gc.collect()
    ancestor_count = len(rows)
    factories = {"euler_exists":lambda s:_euler_exists(s,formulas["euler_exists"],registry),
        "euler_padding":_euler_padding,"product_rule":_product_rule,"CV007":_root}
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise EulerProductError("Euler product aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in dependencies],encode_proof(body)])
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
        raise EulerProductError("Euler product canonical payload bound exceeded")
    del rows,keys,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise EulerProductError("decoded Euler product target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or euler_product_source_pins()!=before:
        raise EulerProductError("Euler product target/source changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,coefficientwise_euler_product_rule=True,
        actual_ancestor_nodes=len(ancestors),actual_ancestor_body_nodes=ancestor_total,
        merged_rows_only_exact_byte_deduplication=True,ordered_dependency_remapping_only=True,
        convolution_archive=dict(CONVOLUTION_ARCHIVE),linearity_archive=dict(LINEARITY_ARCHIVE),
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),new_induction_count=1,
        ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,new_axioms=[],
        external_certificate_references=[],independent_lean_checked=False)
    return EulerProductCertificate(target,bundle,payload,receipt,deepest,provenance)
