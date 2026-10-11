"""CV024: denominator-cleared Euler equation for an actual finite composition.

With a zero constant input, construct terminal-one weights and the actual
finite composition at width N. Prove d*(i*C[i])=(EA*C)[i] for i<N. This
is finite natural arithmetic, not yet a factorial or analytic interpretation.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_weighted_series_scaling import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,definition_registry as scaling_registry,
    weighted_series_scaling_source_pins,COMPOSITION_ARCHIVE,
    HELPER_SOURCES as SCALING_HELPERS,scaling,
)
from sqrt2_power_finite_composition_euler import (
    NAMED_SOURCE as COMPOSITION_SOURCE,HELPER_SOURCES as COMPOSITION_HELPERS,
    ENDPOINT_SOURCES as COMPOSITION_ENDPOINTS,coefficient,
)
from sqrt2_power_exponential_weights import (
    definition_registry as weights_registry,exponential_weights_source_pins,
    NAMED_SOURCE as WEIGHTS_SOURCE,positive,
)
from sqrt2_power_series_power_vanishing import (
    definition_registry as vanishing_registry,series_power_vanishing_source_pins,
    VANISHING_SOURCE,INPUT_ZERO,
)
from sqrt2_power_convolution_unit import assemble_actual_certificate

SCHEMA = "sqrt2-power-denominator-euler-v1"
A = ("ab","ac","L")
W,Z = ("wb","wc"),("yb","yc")
D = ("db","dc")
EA = D+("L",)
P = ("pb","pc","qb","qc")
Q,R = ("tb","tc","vb","vc"),("rb","rc","sb","sc")
F,G = ("fb","fc"),("gb","gc")
OUTPUTS = W+D+P+Z+Q+R


def forall(names,source):
    return "forall "+" ".join(names)+". "+source


def row(codes,index,values):
    return "NatPowerRow("+",".join(codes+(index,)+values)+")"


def trace(weights,acc,length,width="N"):
    return "NatWeightedSeriesTrace("+",".join((width,)+weights+P+acc+(length,))+")"


WEIGHTS = "NatExpWeightTable(d,N,wb,wc)"
SHIFT = "NatShiftedEulerPrefix(wb,wc,yb,yc,N)"
EULER = "NatEulerPrefix(ab,ac,db,dc,L)"
POWER = "NatPowerTrace("+",".join(A+("N",)+P+("N",))+")"
INVARIANT = forall(F+("i","p","v"),row(Q,"S N",F)+" -> Lt(i,N) -> BetaAt(fb,fc,i,p) -> "+coefficient(EA,F+("N",),"i","v")+" -> d*(i*p)=v")
PROPERTIES = (WEIGHTS,"("+positive(W)+")",EULER,POWER,SHIFT,trace(W,Q,"S N"),trace(Z,R,"N"),"("+INVARIANT+")")


def joined(parts):
    result = parts[-1]
    for part in reversed(parts[:-1]):
        result = part+" /\\ ("+result+")"
    return result


NAMED_SOURCE = forall(A+("d","N"),INPUT_ZERO+" -> exists "+" ".join(OUTPUTS)+". "+joined(PROPERTIES))
TARGET_SHA256 = "b3b638e846a53d3cee1e16e8f927226ab00da021924e9c98b2978fc3a534989f"
TERMINAL_PARAMS = A+("d","N")+W+P+Z+Q+R+F+G+("i","p","r")
TERMINAL_PREMISES = (INPUT_ZERO,WEIGHTS,POWER,SHIFT,trace(W,Q,"S N"),trace(Z,R,"N"),row(Q,"S N",F),row(R,"N",G),"Lt(i,N)","BetaAt(fb,fc,i,p)","BetaAt(gb,gc,i,r)")
HELPER_SOURCES = {
    "trace_restrict":forall(("H",)+W+P+Q+("N",),trace(W,Q,"S N","H")+" -> "+trace(W,Q,"N","H")),
    "shift_scale":forall(("d","N")+W+Z,WEIGHTS+" -> "+SHIFT+" -> "+scaling(Z,W,"N")),
    "terminal_scale":forall(TERMINAL_PARAMS," -> ".join(TERMINAL_PREMISES+("p=d*r",))),
    "coefficient_scale":forall(("d",)+D+("L",)+G+F+("N","i","u","v"),
        scaling(G,F,"N")+" -> "+coefficient(EA,G+("N",),"i","u")+" -> "+coefficient(EA,F+("N",),"i","v")+" -> v=d*u"),
}
HELPER_TARGET_SHA256 = {
    "trace_restrict":"d2bf93e83de87c9220a498ad91c93476bdc967df864f92e8e8509b759d194299",
    "shift_scale":"200170bcc59a8d5dbdec77160fb337557f3f942bbb70e0865eddf8ae1e4ea75a",
    "terminal_scale":"a2065ebac7a949f0a428a66ab0e6d00d5e02941d0979fae556fee5f5e9b63890",
    "coefficient_scale":"923b6f5870ec99540c97face38145af0630bb5b0696f1052f0430db45e75529e",
}
SCALING_ARCHIVE = dict(case="CV023",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-weighted-series-scaling-v1/generation-process.json.gz",
    bytes=25469,sha256="ef524557ab571bd9e5e6e0b99b7d5f15ecfce85099d89aa9bbf69baa5002a1af",
    raw_bytes=457020,raw_sha256="b2c05905dc1b7f5d73e42f729bfc2377b7bb554404b579cf84950fcebd2178ce",
    bundle_bytes=269143,bundle_sha256="3bebdb7ac4f793a5bf43e6e100c0a1286483ea73b7fb8a87d482df3f8422e108",
    nodes=116,root=115,target_ast_sha256="942e7e78560841ddb311dc397deeb9086050bd51b7d759f6926caddefd3d230d")
WEIGHTS_ARCHIVE = dict(case="CV022",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exponential-weights-v1/generation-process.json.gz",
    bytes=20252,sha256="a87619923985c88f1c822641495e8643a21e348d760223d273eced922c9e493c",
    raw_bytes=296689,raw_sha256="063dd5b87d8f1780bca63c4c80cca17dbbaf4581a72ebbb72886354779349c23",
    bundle_bytes=175040,bundle_sha256="e94cd7dab31d292ec52a9fff9ca85a05f17b5ba0aac7c396fa8c25c449b7b998",
    nodes=108,root=107,target_ast_sha256="67f4d5cffffb0e5b5dd1f559eb6b6d8cd2dbb5ac23bdeb79d580326b4cf5a880")
VANISHING_ARCHIVE = dict(case="CV005",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-series-power-vanishing-v1/generation-process.json.gz",
    bytes=25522,sha256="907a1b91ae784f724dd56058e66c3f396b22e516aee9992a7edc94d6449ce748",
    raw_bytes=512248,raw_sha256="a074b3d5f4373c2b2f25f6f39b2fdc9801a3796d10ee21f7b476a0c3f26e7684",
    bundle_bytes=309480,bundle_sha256="364445bf362ce8746ce876026d69f22d8df264856ff4afda7b32a6940e196c0e",
    nodes=131,root=130,target_ast_sha256="db647ab11de25c9cae8ffd94e24655fd15cc955113f9e4a7f12ee383e21e224d")
ARCHIVES = (COMPOSITION_ARCHIVE,SCALING_ARCHIVE,WEIGHTS_ARCHIVE,VANISHING_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:COMPOSITION_ENDPOINTS[name] for name in ("one_mul","mul_zero_left","mul_comm","mul_assoc","le_refl","le_succ","beta_exists","beta_unique","row_decode","coefficient_exists","coefficient_swap","coefficient_linearity")},
    "weighted_graph":COMPOSITION_HELPERS["weighted_graph"],
    "weighted_value":COMPOSITION_HELPERS["weighted_value"],
    "fold_scale":SCALING_HELPERS["fold_scale"],
    "vanishing":VANISHING_SOURCE,
    "composition_exists":COMPOSITION_SOURCE,
    "weights_exists":WEIGHTS_SOURCE,
}
HELPER_DEPENDENCIES = {
    "trace_restrict":("le_succ",),
    "shift_scale":("beta_exists","beta_unique","one_mul","mul_zero_left","mul_assoc","mul_comm"),
    "terminal_scale":("row_decode","beta_exists","vanishing","le_refl","weighted_graph","weighted_value","shift_scale","trace_restrict","fold_scale","one_mul"),
    "coefficient_scale":("coefficient_swap","coefficient_linearity","one_mul","mul_zero_left"),
    "CV024":("weights_exists","composition_exists","row_decode","coefficient_exists","terminal_scale","coefficient_scale","one_mul","mul_zero_left"),
}


class DenominatorEulerError(ValueError):
    """Changed input support, exact computation, source, or actual proof body."""


def definition_registry():
    result = dict(scaling_registry())
    for supplied in (weights_registry(),vanishing_registry()):
        for name,d in supplied.items():
            if name in result and (result[name].template_formula!=d.template_formula or result[name].stable_id!=d.stable_id):
                raise DenominatorEulerError("shared conservative definition mismatch")
            result[name] = d
    return MappingProxyType(result)


def frozen_denominator_euler_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise DenominatorEulerError("CV024 exact denominator-cleared finite composition target changed")
    return target


def source_contract():
    return dict(code="CV024",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,input_vanishes_below_one_required=True,actual_weights_and_composition_constructed=True,
        denominator_cleared_euler_equation=True,all_coefficients_below_N=True,
        output_weight_nonvanishing_requires_nonzero_d=True,zero_d_allowed=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",inner_atanh_coefficients=False,
        factorial_quotient_interpretation=False,exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def denominator_euler_source_pins():
    result = weighted_series_scaling_source_pins()
    for supplied in (exponential_weights_source_pins(),series_power_vanishing_source_pins()):
        for name,pin in supplied.items():
            if name in result and result[name]!=pin:
                raise DenominatorEulerError("source dependency disagreement")
            result[name] = pin
    expected = {
        "scripts/sqrt2_power_weighted_series_scaling.py":"135debe011a281d6a3332f45d4c9be1c72e71bcc94d18aae37a3c3102e9d09d4",
        "scripts/sqrt2_power_exponential_weights.py":"f9e1c356636cffd2d244cd01974999b32e835f864bfdfbef4ded8e2ea26e6085",
        "scripts/sqrt2_power_series_power_vanishing.py":"ea3e1d648fd35f5430d0e19c442bc06031b849c570ddd4b7315522eba468edab",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_denominator_euler.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise DenominatorEulerError("denominator-Euler source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _trace_restrict(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro
    from peano_lab.kernel.terms import Succ
    def finish(t):
        def step(u):
            bound = apply(specialize(u,"le_succ",Succ(u.term("k")),u.term("N")),u.hyp("bound"))
            return apply(instantiate(AndElimR(u.hyp("trace")),u.term("k")),bound)
        return AndIntro(AndElimL(t.hyp("trace")),introduce(t,("k",),("bound",),step))
    return introduce(s,("H",)+W+P+Q+("N",),("trace",),finish)


def _shift_scale(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimR,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def decoded(t):
        i,d,a,b,c,e = t.terms(("i","d","a","b","c","e"))
        adjacent = apply(instantiate(AndElimR(t.hyp("weights")),i,c,e),t.hyp("index"),t.hyp("third"),t.hyp("next"))
        derived = apply(specialize(t,"shift",i,e),t.hyp("index"),t.hyp("next"))
        unique = apply(specialize(t,"beta_unique",*t.terms(Z),i,a,Mul(Succ(i),e)),t.hyp("first"),derived)
        return _chain(specialize(t,"one_mul",c),adjacent,
            CongMul(specialize(t,"mul_comm",Succ(i),d),EqRefl(e)),specialize(t,"mul_assoc",d,Succ(i),e),
            CongMul(EqRefl(d),EqSym(unique)),EqSym(instantiate(Axiom("PA3"),Mul(d,a))),
            CongAdd(EqRefl(Mul(d,a)),EqSym(specialize(t,"mul_zero_left",b))))
    return introduce(s,("d","N")+W+Z,("weights","shift"),lambda t:
        introduce(t,("i","a","b","c"),("index","first","second","third"),lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(W),Succ(u.term("i"))),("e",),"next",decoded)))


def _terminal_scale(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndIntro,CongAdd,EqRefl,OrIntroL
    from peano_lab.kernel.terms import Mul,Succ,Zero
    T,O = ("ub","uc"),("ob","oc")
    premises = ("zero","weights","power","shift","qtrace","rtrace","row_q","row_r","index","first","second")
    def chosen(t):
        N,i,d,p,r,a,b = t.terms(("N","i","d","p","r","a","b"))
        vanishing = apply(specialize(t,"vanishing",*t.terms(A),N,*t.terms(P)),t.hyp("zero"))
        zeros = apply(instantiate(vanishing,N,N,*t.terms(T)),t.hyp("power"),specialize(t,"le_refl",N),t.hyp("power_row"))
        a0 = apply(instantiate(zeros,i,a),t.hyp("index"),OrIntroL(AndIntro(t.hyp("index"),t.hyp("power_value"))))
        graph = apply(specialize(t,"weighted_graph",N,*t.terms(W+P+Q),Succ(N),N,*t.terms(T+O+F),Succ(Zero())),
            t.hyp("qtrace"),specialize(t,"le_refl",Succ(N)),t.hyp("power_row"),t.hyp("old_row"),t.hyp("row_q"),AndElimL(t.hyp("weights")))
        pvalue = apply(specialize(t,"weighted_value",*t.terms(O+T+F),N,Succ(Zero()),i,b,a,p),
            graph,t.hyp("index"),t.hyp("old_value"),t.hyp("power_value"),t.hyp("first"))
        pb = _chain(pvalue,CongAdd(EqRefl(b),specialize(t,"one_mul",a)),CongAdd(EqRefl(b),a0),instantiate(Axiom("PA3"),b))
        relation = apply(specialize(t,"shift_scale",*t.terms(("d","N")+W+Z)),t.hyp("weights"),t.hyp("shift"))
        restricted = apply(specialize(t,"trace_restrict",N,*t.terms(W+P+Q),N),t.hyp("qtrace"))
        br = apply(specialize(t,"fold_scale",N,*t.terms(P+W+Z+Q+R),d,N,N,*t.terms(O+G),i,b,r),
            relation,restricted,t.hyp("rtrace"),specialize(t,"le_refl",N),t.hyp("old_row"),t.hyp("row_r"),t.hyp("index"),t.hyp("old_value"),t.hyp("second"))
        return _chain(pb,br)
    return introduce(s,TERMINAL_PARAMS,premises,lambda t:
        eliminate(t,specialize(t,"row_decode",*t.terms(P+("N",))),T,"power_row",lambda u:
            eliminate(u,specialize(u,"row_decode",*u.terms(Q+("N",))),O,"old_row",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(T+("i",))),("a",),"power_value",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(O+("i",))),("b",),"old_value",chosen)))))


def _coefficient_scale(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        d,N,i,u,v = t.terms(("d","N","i","u","v"))
        first = apply(specialize(t,"coefficient_swap",*t.terms(EA+G),N,i,u),t.hyp("first"))
        second = apply(specialize(t,"coefficient_swap",*t.terms(EA+F),N,i,v),t.hyp("second"))
        relation = apply(specialize(t,"coefficient_linearity",d,Zero(),Succ(Zero()),*t.terms(G+G+F),N,*t.terms(EA),i,u,u,v),
            t.hyp("graph"),first,first,second)
        return _chain(EqSym(specialize(t,"one_mul",v)),relation,
            CongAdd(EqRefl(Mul(d,u)),specialize(t,"mul_zero_left",u)),instantiate(Axiom("PA3"),Mul(d,u)))
    return introduce(s,("d",)+D+("L",)+G+F+("N","i","u","v"),("graph","first","second"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def chosen(t):
        def coefficient_entry(u):
            def computed(v):
                def graph(w):
                    def point(x):
                        scalar = apply(specialize(x,"terminal_scale",*x.terms(A+("d","N")+W+P+Z+Q+R+F+G+("j","c","a"))),
                            x.hyp("zero"),AndElimL(x.hyp("weights_data")),field(x.hyp("composition"),1,6),field(x.hyp("composition"),2,6),
                            field(x.hyp("composition"),3,6),field(x.hyp("composition"),4,6),x.hyp("row_q"),x.hyp("row_r"),
                            x.hyp("index_j"),x.hyp("third"),x.hyp("first"))
                        da = Mul(x.term("d"),x.term("a"))
                        return _chain(specialize(x,"one_mul",x.term("c")),scalar,EqSym(instantiate(Axiom("PA3"),da)),
                            CongAdd(EqRefl(da),EqSym(specialize(x,"mul_zero_left",x.term("b")))))
                    return introduce(w,("j","a","b","c"),("index_j","first","second","third"),point)
                relation = graph(v)
                scaled = apply(specialize(v,"coefficient_scale",*v.terms(("d",)+EA+G+F+("N","i","u","v"))),relation,v.hyp("derived_coefficient"),v.hyp("coefficient"))
                chain = apply(instantiate(field(v.hyp("composition"),5,6),*v.terms(F+G+("i","p","u"))),v.hyp("row_q"),v.hyp("row_r"),v.hyp("index"),v.hyp("entry"),v.hyp("derived_coefficient"))
                return _chain(CongMul(EqRefl(v.term("d")),chain),EqSym(scaled))
            return eliminate(u,specialize(u,"row_decode",*u.terms(R+("N",))),G,"row_r",lambda v:
                eliminate(v,specialize(v,"coefficient_exists",*v.terms(EA+G+("N","i"))),("u",),"derived_coefficient",computed))
        invariant = introduce(t,F+("i","p","v"),("row_q","index","entry","coefficient"),coefficient_entry)
        return witness(t.terms(OUTPUTS),conjunction(AndElimL(t.hyp("weights_data")),AndElimR(t.hyp("weights_data")),
            *(field(t.hyp("composition"),j,6) for j in range(5)),invariant))
    return introduce(s,A+("d","N"),("zero",),lambda t:
        eliminate(t,specialize(t,"weights_exists",*t.terms(("d","N"))),W,"weights_data",lambda u:
            eliminate(u,specialize(u,"composition_exists",*u.terms(A+("N",)+W+("N",))),D+P+Z+Q+R,"composition",chosen)))


def prove_denominator_euler(*,limits=None):
    registry = definition_registry()
    factories = {"trace_restrict":_trace_restrict,"shift_scale":_shift_scale,"terminal_scale":_terminal_scale,"coefficient_scale":_coefficient_scale,"CV024":_root}
    return assemble_actual_certificate(code="CV024",target=frozen_denominator_euler_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=denominator_euler_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
