"""CV004: construct every finite truncated natural-series power trace.

Rows are actual beta-coded coefficient tables. Row zero is the truncated unit;
each successor is an actually executed natural convolution with the input.
The definition contains neither below-degree vanishing nor differentiation,
coefficient bounds or an exponential/logarithmic correctness assertion.
"""
from dataclasses import dataclass
import gc
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType

from sqrt2_power_natural_convolution import (
    natural_convolution_source_pins, definition_registry as convolution_registry,
    ANCESTOR_IDS as CONVOLUTION_ANCESTORS, ENDPOINT_IDS as CONVOLUTION_ENDPOINTS,
)
from sqrt2_power_quadratic_trace_exists import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,_inert_metrics,
)
from sqrt2_power_quadratic_product_exists import read_archive

SCHEMA = "sqrt2-power-series-power-trace-v1"
P = ("ab","ac","L","H")
B = ("pb","pc","qb","qc")
E = ("eb","ec","fb","fc")
U = ("ub","uc")
V = ("vb","vc")


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def exists(names,source):
    return "exists "+" ".join(names)+". "+source


def named(name,*terms):
    return name+"("+",".join(terms)+")"


def row(codes,index,values):
    return named("NatPowerRow",*codes,index,*values)


def trace(codes,length):
    return named("NatPowerTrace",*P,*codes,length)


def conv(first,second):
    return named("NatConvolutionPrefix","ab","ac","L",*first,"H",*second,"H")


def preserved(old,new,length):
    values = ("rb","rc")
    return forall(("i",)+values,"Lt(i,"+length+") -> "+row(old,"i",values)+" -> "+row(new,"i",values))


DEFINITION_ROWS = (
    (403,"NatUnitCoefficient",("i","a"),"(i=0 /\\ a=1) \\/ (exists k. i=S k /\\ a=0)",(),"9de9afd59064f17d83da4a56b113aa9d484be168da2c5da15e23b840a637004b"),
    (404,"NatUnitPrefix",U+("H",),"forall i. Lt(i,H) -> exists a. BetaAt(ub,uc,i,a) /\\ NatUnitCoefficient(i,a)",
     ("Lt","BetaAt","NatUnitCoefficient"),"acda0b4b000e70bc5427ffd9d06295194d662e055280e393e1e1a3128bc909d2"),
    (405,"NatPowerRow",B+("k",)+U,"BetaAt(pb,pc,k,ub) /\\ BetaAt(qb,qc,k,uc)",("BetaAt",),"d2f747498f7a91d3fb74caf408c6858018f02a1ad48a0817ff3acb6aeb23f777"),
    (406,"NatPowerStep",P+B+("k",),exists(U+V,row(B,"k",U)+" /\\ ("+row(B,"S k",V)+" /\\ "+conv(U,V)+")"),
     ("NatPowerRow","NatConvolutionPrefix"),"9abfe2cc82633d5ec8da40b65c1ac315c2e74a0177161053caa3bdeeec64e272"),
    (407,"NatPowerTrace",P+B+("K",),
     "("+exists(U,row(B,"0",U)+" /\\ NatUnitPrefix(ub,uc,H)")+") /\\ ("+
        forall(("k",),"Lt(k,K) -> "+named("NatPowerStep",*P,*B,"k"))+")",
     ("NatPowerRow","NatUnitPrefix","Lt","NatPowerStep"),"1cfb89ad0d4da7d0b256954d10b11ab884b559def2c51f75ea8d6df36d321b1e"),
)
NAMED_SOURCE = forall(P+("K",),exists(B,trace(B,"K")))
TARGET_SHA256 = "d39fa99bbfda29fc077a02cf8d23cc3a5d36c8f829bb9b76988a537042145777"
HELPER_SOURCES = {
    "unit_value": "forall i. exists a. NatUnitCoefficient(i,a)",
    "unit_exists": "forall H. exists ub uc. NatUnitPrefix(ub,uc,H)",
    "decode": forall(B+("k",),exists(U,row(B,"k",U))),
    "extend": forall(B+("K",)+U,exists(E,row(E,"K",U)+" /\\ ("+preserved(B,E,"K")+")")),
    "transport": forall(P+B+E+("K",),"("+preserved(B,E,"S K")+") -> "+trace(B,"K")+" -> "+trace(E,"K")),
    "successor": forall(P+B+("K",),trace(B,"K")+" -> "+exists(E,trace(E,"S K"))),
}
HELPER_TARGET_SHA256 = {
    "unit_value":"26dbe74709c49e0796df29d62a50ce2d6f7d62ce5f4f925febe384cec9c45acd",
    "unit_exists":"8d4d017d4bc55fde8a82b77e26fc39a39e970738f696e9f1a961794c367117d6",
    "decode":"dc89afd64ef2c3d7882bb913d370ba0adc55a1b70afd4b67c50ad1f9ef96b1ce",
    "extend":"c67f9e2d12bf886f89a5b8d472c5e4239c58be5217e439d80ab56881848c64ae",
    "transport":"13d047fde3e30d163ddb043a9f60ab765f629f31d3e44c2b019caae6add2edd2",
    "successor":"4c401f4cde9e426f8f7bcb430bdc9932b20e188bb38d2e99e27e81a540ebd99f",
}
HELPER_DEPENDENCIES = {
    "unit_value": ("zero_or_succ",),
    "unit_exists": ("zero_le","lt_not_le","le_of_succ_le_succ","le_eq_or_lt","beta_prefix_extend","unit_value"),
    "decode": ("beta_at_exists",),
    "extend": ("beta_prefix_extend",),
    "transport": ("zero_le","succ_le_succ","le_succ"),
    "successor": ("le_refl","le_of_succ_le_succ","le_eq_or_lt","decode","extend","transport","convolution_exists"),
    "CV004": ("zero_le","lt_not_le","unit_exists","extend","successor"),
}
CONVOLUTION_ARCHIVE = dict(case="CV003",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-natural-convolution-v1/generation-process.json.gz",
    bytes=22806,sha256="c3e7a722a1aa1a1c55cd5a716741ea2557aca747ebc455e613f583da02d8f77c",
    raw_bytes=439844,raw_sha256="0489ae06013474e9667a9c18b508fe1224b77c07702d7c556e8f4e9c9fae6ac3",
    bundle_bytes=267044,bundle_sha256="ce973e6781fe1dd61db9e92cb368d4a86875740fa2a5cf0c744884a56486588b",
    nodes=126,root=125,target_ast_sha256="b5ad2ef80b9ae8fd100f25b2a128eac7af5d8d58a783e89d2aab7f5bf9c4b0d8")
EXTRA_ENDPOINTS = {
    "zero_or_succ":(19,"forall n. n=0 \\/ exists k. n=S k"),
    "succ_le_succ":(32,"forall a b. Le(a,b) -> Le(S a,S b)"),
    "le_succ":(34,"forall a b. Le(a,b) -> Le(a,S b)"),
}


class PowerTraceError(ValueError):
    """Changed actual proof bytes, frozen statement, definition or fixed cap."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    import json
    registry = dict(convolution_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids = {d["id"] for d in parent}|{d.stable_id for d in registry.values()}|{f"ND{i:04d}" for i in range(382,403)}
    names = {d["name"] for d in parent}|set(registry)|{"NatExpAtanhRecurrence"}
    for number,name,parameters,source,dependencies,digest in DEFINITION_ROWS:
        identifier = f"ND{number:04d}"
        if identifier in ids or name in names or not set(dependencies)<=registry.keys():
            raise PowerTraceError("power definition collision or forward dependency")
        formula = parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula))!=digest:
            raise PowerTraceError("power definition exact expansion changed")
        text = pretty_formula(formula,list(parameters))
        d = _definition(stable_id=identifier,name=name,parameters=parameters,template_source=text,
            summary="Actual finite truncated natural-series power execution, not a promised algebraic or analytic property.",
            category="irrationality_formal_series",conceptual_dependencies=dependencies)
        if d.template_formula!=formula or parse_formula_in_context(text,list(parameters))!=formula:
            raise PowerTraceError("power definition failed exact expansion roundtrip")
        registry[name] = d
        ids.add(identifier)
        names.add(name)
    return MappingProxyType(registry)


def frozen_series_power_trace_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PowerTraceError("CV004 original unconditional power-trace target changed")
    return target


def source_contract():
    return dict(code="CV004",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,arbitrary_exponent_and_width=True,starts_at_truncated_unit=True,
        actual_natural_convolution_steps=True,output_trace_supplied=False,zero_constant_required=False,
        new_definition_ids=["ND0403","ND0404","ND0405","ND0406","ND0407"],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",below_degree_vanishing=False,
        rational_coefficients=False,formal_derivative=False,exp_composition_recurrence=False,
        analytic_limit_claim=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def series_power_trace_source_pins():
    result = natural_convolution_source_pins()
    expected = {"scripts/sqrt2_power_natural_convolution.py":"a5498a8534df2e1618419bb2a4ee382d3ebd205fd024560cca9876ab9e4eedd1",
        "scripts/sqrt2_power_quadratic_product_exists.py":"c20c38bfceb78fa16c236925024a43c12624b2df23937bb1c1e9f54393d49017",
        CONVOLUTION_ARCHIVE["path"]:CONVOLUTION_ARCHIVE["sha256"]}
    for name in (*expected,"scripts/sqrt2_power_series_power_trace.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PowerTraceError("power producer source/archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _unit_value(s):
    from peano_lab.kernel.proofs import AndIntro,EqRefl,ExistsIntro,OrIntroL,OrIntroR,OrElim
    from peano_lab.kernel.terms import Succ,Zero
    def finish(t):
        left = t.hypothesis("zero")
        right = t.hypothesis("successor")
        return OrElim(specialize(t,"zero_or_succ",t.term("i")),
            ExistsIntro(Succ(Zero()),OrIntroL(AndIntro(left.hyp("zero"),EqRefl(Succ(Zero()))))),
            eliminate(right,right.hyp("successor"),("k",),"index",lambda u:
                ExistsIntro(Zero(),OrIntroR(ExistsIntro(u.term("k"),AndIntro(u.hyp("index"),EqRefl(Zero())))))))
    return introduce(s,("i",),(),finish)


def _unit_exists(s,target,registry):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import (AndIntro,AndElimL,AndElimR,BotElim,EqSubst,EqSym,ExistsIntro,Ind,OrElim)
    from peano_lab.kernel.terms import Zero
    def base(t):
        return witness((Zero(),Zero()),introduce(t,("i",),("bound",),lambda u:
            BotElim(apply(specialize(u,"lt_not_le",u.term("i"),Zero()),u.hyp("bound"),specialize(u,"zero_le",u.term("i"))))))
    def step(t):
        def old(u):
            def value(v):
                def extension(w):
                    def entry(x):
                        def last(y):
                            def transport(source,proof):
                                motive = parse_named(source,y.variable("index_slot").variables,registry)
                                return EqSubst(motive,EqSym(y.hyp("last")),proof)
                            decoded = transport("BetaAt(ub,uc,index_slot,a)",AndElimL(y.hyp("extension")))
                            value = transport("NatUnitCoefficient(index_slot,a)",y.hyp("value"))
                            return ExistsIntro(y.term("a"),AndIntro(decoded,value))
                        def earlier(y):
                            def chosen(z):
                                decoded = apply(instantiate(AndElimR(z.hyp("extension")),*z.terms(("i","v"))),
                                    z.hyp("earlier"),AndElimL(z.hyp("old_value")))
                                return ExistsIntro(z.term("v"),AndIntro(decoded,AndElimR(z.hyp("old_value"))))
                            return eliminate(y,apply(specialize(y,"old_prefix",y.term("i")),y.hyp("earlier")),("v",),"old_value",chosen)
                        bound = apply(specialize(x,"le_of_succ_le_succ",*x.terms(("i","H"))),x.hyp("bound"))
                        cases = apply(specialize(x,"le_eq_or_lt",*x.terms(("i","H"))),bound)
                        return OrElim(cases,last(x.hypothesis("last")),earlier(x.hypothesis("earlier")))
                    return witness(w.terms(U),introduce(w,("i",),("bound",),entry))
                return eliminate(v,specialize(v,"beta_prefix_extend",*v.terms(("H","ob","oc","a"))),U,"extension",extension)
            return eliminate(u,specialize(u,"unit_value",u.term("H")),("a",),"value",value)
        return eliminate(t,t.hyp("IH"),("ob","oc"),"old_prefix",old)
    return Ind(target.body,base(s),introduce(s,("H",),("IH",),step))


def _decode(s):
    from peano_lab.kernel.proofs import AndIntro
    return introduce(s,B+("k",),(),lambda t:
        eliminate(t,specialize(t,"beta_at_exists",*t.terms(B[:2]),t.term("k")),("ub",),"left",lambda u:
            eliminate(u,specialize(u,"beta_at_exists",*u.terms(B[2:]),u.term("k")),("uc",),"right",lambda v:
                witness(v.terms(U),AndIntro(v.hyp("left"),v.hyp("right"))))))


def _extend(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR
    def result(t):
        # The preservation binders use fresh names: the appended row witnesses
        # are still in scope, so do not shadow them in the source bookkeeping.
        def renamed_transport(u):
            return AndIntro(*(apply(instantiate(AndElimR(u.hyp(label)),u.term("i"),u.term(value)),
                u.hyp("bound"),field(u.hyp("old"),component,2))
                for component,(label,value) in enumerate((("left","rb"),("right","rc")))))
        return witness(t.terms(E),AndIntro(
            AndIntro(AndElimL(t.hyp("left")),AndElimL(t.hyp("right"))),
            introduce(t,("i","rb","rc"),("bound","old"),renamed_transport)))
    return introduce(s,B+("K",)+U,(),lambda t:
        eliminate(t,specialize(t,"beta_prefix_extend",t.term("K"),*t.terms(B[:2]),t.term("ub")),E[:2],"left",lambda u:
            eliminate(u,specialize(u,"beta_prefix_extend",u.term("K"),*u.terms(B[2:]),u.term("uc")),E[2:],"right",result)))


def _transport(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ,Zero
    def finish(t):
        def initial(u):
            bound = apply(specialize(u,"succ_le_succ",Zero(),u.term("K")),specialize(u,"zero_le",u.term("K")))
            decoded = apply(specialize(u,"preserved",Zero(),*u.terms(U)),bound,AndElimL(u.hyp("initial")))
            return witness(u.terms(U),AndIntro(decoded,AndElimR(u.hyp("initial"))))
        first = eliminate(t,AndElimL(t.hyp("trace")),U,"initial",initial)
        def step(u):
            def decoded(v):
                k,K = v.terms(("k","K"))
                left_bound = apply(specialize(v,"le_succ",Succ(k),K),v.hyp("bound"))
                right_bound = apply(specialize(v,"succ_le_succ",Succ(k),K),v.hyp("bound"))
                left = apply(specialize(v,"preserved",k,*v.terms(U)),left_bound,field(v.hyp("step"),0,3))
                right = apply(specialize(v,"preserved",Succ(k),*v.terms(V)),right_bound,field(v.hyp("step"),1,3))
                return witness(v.terms(U+V),conjunction(left,right,field(v.hyp("step"),2,3)))
            old = apply(instantiate(AndElimR(u.hyp("trace")),u.term("k")),u.hyp("bound"))
            return eliminate(u,old,U+V,"step",decoded)
        return AndIntro(first,introduce(t,("k",),("bound",),step))
    return introduce(s,P+B+E+("K",),("preserved","trace"),finish)


def _successor(s,registry):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR,EqSubst,EqSym,OrElim
    from peano_lab.kernel.terms import Succ
    def old(t):
        def multiplied(u):
            def extended(v):
                def transformed(w):
                    return apply(specialize(w,"transport",*w.terms(P+B+E+("K",))),
                        AndElimR(w.hyp("extension")),w.hyp("trace"))
                def step(w):
                    def last(x):
                        left = apply(instantiate(AndElimR(x.hyp("extension")),x.term("K"),*x.terms(U)),
                            specialize(x,"le_refl",Succ(x.term("K"))),x.hyp("old"))
                        body = witness(x.terms(U+V),conjunction(left,AndElimL(x.hyp("extension")),x.hyp("product")))
                        motive = parse_named(named("NatPowerStep",*P,*E,"index_slot"),x.variable("index_slot").variables,registry)
                        return EqSubst(motive,EqSym(x.hyp("last")),body)
                    def earlier(x):
                        return apply(instantiate(AndElimR(transformed(x)),x.term("k")),x.hyp("earlier"))
                    lower = apply(specialize(w,"le_of_succ_le_succ",*w.terms(("k","K"))),w.hyp("bound"))
                    cases = apply(specialize(w,"le_eq_or_lt",*w.terms(("k","K"))),lower)
                    return OrElim(cases,last(w.hypothesis("last")),earlier(w.hypothesis("earlier")))
                return witness(v.terms(E),AndIntro(AndElimL(transformed(v)),introduce(v,("k",),("bound",),step)))
            extension = specialize(u,"extend",*u.terms(B),Succ(u.term("K")),*u.terms(V))
            return eliminate(u,extension,E,"extension",extended)
        product = specialize(t,"convolution_exists",*t.terms(("ab","ac","L")),*t.terms(U),t.term("H"),t.term("H"))
        return eliminate(t,product,V,"product",multiplied)
    return introduce(s,P+B+("K",),("trace",),lambda t:
        eliminate(t,specialize(t,"decode",*t.terms(B+("K",))),U,"old",old))


def _root(s,target):
    from peano_lab.kernel.proofs import AndIntro,AndElimL,BotElim,Ind
    from peano_lab.kernel.terms import Zero
    def base(t):
        def unit(u):
            def extended(v):
                initial = witness(v.terms(U),AndIntro(AndElimL(v.hyp("extension")),v.hyp("unit")))
                empty = introduce(v,("k",),("bound",),lambda w:
                    BotElim(apply(specialize(w,"lt_not_le",w.term("k"),Zero()),w.hyp("bound"),specialize(w,"zero_le",w.term("k")))))
                return witness(v.terms(E),AndIntro(initial,empty))
            extension = specialize(u,"extend",Zero(),Zero(),Zero(),Zero(),Zero(),*u.terms(U))
            return eliminate(u,extension,E,"extension",extended)
        return eliminate(t,specialize(t,"unit_exists",t.term("H")),U,"unit",unit)
    def step(t):
        return eliminate(t,t.hyp("IH"),B,"trace",lambda u:
            apply(specialize(u,"successor",*u.terms(P+B+("K",))),u.hyp("trace")))
    motive = target
    for _ in range(5):
        motive = motive.body
    return introduce(s,P,(),lambda t:Ind(motive,base(t),introduce(t,("K",),("IH",),step)))


@dataclass(frozen=True)
class SeriesPowerTraceCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_series_power_trace(*,limits=None,archive_path=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits = BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise PowerTraceError("expected unchanged BinaryDAGLimits")
    before = series_power_trace_source_pins()
    registry,target = definition_registry(),frozen_series_power_trace_target()
    formulas = {name:parse_named(source,registry=registry) for name,source in HELPER_SOURCES.items()}
    if {name:json_hash(encode_formula(f)) for name,f in formulas.items()}!=HELPER_TARGET_SHA256:
        raise PowerTraceError("power-trace internal target changed")
    formulas["CV004"] = target
    rows = read_archive(CONVOLUTION_ARCHIVE,archive_path)
    endpoints = {name:CONVOLUTION_ANCESTORS.index(old) for name,old in CONVOLUTION_ENDPOINTS.items()}
    for name,(old,source) in EXTRA_ENDPOINTS.items():
        index = CONVOLUTION_ANCESTORS.index(old)
        if rows[index][1]!=encode_formula(parse_named(source,registry=registry)):
            raise PowerTraceError("actual power-trace ancestor differs from exact source")
        endpoints[name] = index
    endpoints["convolution_exists"] = 123
    expected = "forall ab ac L bb bc M N. exists cb cc. NatConvolutionPrefix(ab,ac,L,bb,bc,M,cb,cc,N)"
    if rows[123][1]!=encode_formula(parse_named(expected,registry=registry)):
        raise PowerTraceError("actual arbitrary natural convolution existence changed")
    total,deepest = 0,0
    for i,r in enumerate(rows):
        count,depth = _inert_metrics(r[3],limits)
        total,deepest = total+count,max(deepest,depth)
        if any(type(d) is not int or not 0<=d<i for d in r[2]) or type(r[0]) is not int or r[0]<8*count+16:
            raise PowerTraceError("actual power-trace ancestor dependency/fuel mismatch")
    ancestor_total = total
    factories = {
        "unit_value":_unit_value,"unit_exists":lambda s:_unit_exists(s,formulas["unit_exists"],registry),
        "decode":_decode,"extend":_extend,"transport":_transport,
        "successor":lambda s:_successor(s,registry),"CV004":lambda s:_root(s,target),
    }
    for name,dependencies in HELPER_DEPENDENCIES.items():
        body = introduce(Scope(),(),dependencies,factories[name])
        count,depth = _body_metrics(body,limits)
        total,deepest = total+count,max(deepest,depth)
        if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
            raise PowerTraceError("power-trace aggregate body/node bound exceeded")
        _row_preflight(formulas[name],body,limits)
        endpoints[name] = len(rows)
        rows.append([8*count+16,encode_formula(formulas[name]),[endpoints[d] for d in dependencies],encode_proof(body)])
    # The historical convolution root also proves uniqueness, which this
    # existence theorem does not use. Canonical bundles reject unreachable
    # nodes. Retain every actual reachable body, remapping only the ordered
    # dependency indices; neither a theorem name nor a receipt replaces it.
    reachable,pending = set(),[len(rows)-1]
    while pending:
        old = pending.pop()
        if old not in reachable:
            reachable.add(old)
            pending.extend(rows[old][2])
    retained = tuple(sorted(reachable))
    remap = {old:new for new,old in enumerate(retained)}
    ancestor_ids = tuple(old for old in retained if old<126)
    ancestor_total = sum(_inert_metrics(rows[old][3],limits)[0] for old in ancestor_ids)
    discarded = tuple(old for old in range(len(rows)) if old not in reachable)
    rows = [[rows[old][0],rows[old][1],[remap[d] for d in rows[old][2]],rows[old][3]] for old in retained]
    payload = canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise PowerTraceError("power-trace canonical payload bound exceeded")
    del rows,body
    gc.collect()
    bundle,decoded = decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise PowerTraceError("decoded power-trace target differs")
    receipt = check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or series_power_trace_source_pins()!=before:
        raise PowerTraceError("power-trace source/target changed during replay")
    provenance = dict(source_contract(),source_pins=before,original_HA_checked=True,
        canonical_bytes_replayed=True,empty_context=True,actual_power_rows_constructed=True,
        actual_ancestor_nodes=len(ancestor_ids),actual_ancestor_body_nodes=ancestor_total,
        retained_source_ancestor_ids=list(ancestor_ids),discarded_unreachable_ids=list(discarded),
        ordered_dependency_remapping_only=True,convolution_archive=dict(CONVOLUTION_ARCHIVE),
        helper_statement_ast_sha256=dict(HELPER_TARGET_SHA256),new_induction_count=2,
        ring_normalizer_calls=0,solver_calls=0,local_have_compiler_calls=0,new_axioms=[],
        external_certificate_references=[],independent_lean_checked=False)
    return SeriesPowerTraceCertificate(target,bundle,payload,receipt,deepest,provenance)
