"""CV038: construct geometric weights and prove their power interpretation.

At every t,N construct W,p with terminal one, adjacent W[j]=t*W[j+1],
Pow(t,N,p), W[0]=p and W[j]*q=p for every actual Pow(t,j,q), j<=N.
No division or nonzero-multiplier premise is used.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_horner_weighted_sum import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as weighted_registry,horner_weighted_sum_source_pins,
)
from sqrt2_power_exponential_weights import HELPER_SOURCES as SCALE_HELPERS,ENDPOINT_SOURCES as WEIGHT_ENDPOINTS
from sqrt2_power_weight_factorials import (
    definition_registry as power_registry,weight_factorials_source_pins,
    ENDPOINT_SOURCES as POWER_ENDPOINTS,WEIGHTS_ARCHIVE,
)
from sqrt2_power_normalized_composition import FACTORIAL_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive
from sqrt2_power_convolution_unit import _subst

SCHEMA = "sqrt2-power-geometric-weights-v1"
O,C,W = ("ob","oc"),("cb","cc"),("wb","wc")


def table(codes,length="N"):
    return "NatGeometricWeightTable("+",".join(("t",length)+codes)+")"


INVARIANT = "forall j w q. Le(j,N) -> BetaAt(wb,wc,j,w) -> Pow(t,j,q) -> w*q=p"
NAMED_SOURCE = "forall t N. exists wb wc p. "+table(W)+" /\\ (Pow(t,N,p) /\\ (BetaAt(wb,wc,0,p) /\\ ("+INVARIANT+")))"
TARGET_SHA256 = "917e753656a45bbae99c1856843859780ffcc5d52d3d25e45991093293a278be"
HELPER_SOURCES = {
    "shuffle":"forall w q t. w*(q*t)=(t*w)*q",
    "extend":"forall t N ob oc. "+table(O)+" -> exists wb wc. "+table(W,"S N"),
    "weights_exists":"forall t N. exists wb wc. "+table(W),
    "invariant":"forall t N wb wc p. "+table(W)+" -> BetaAt(wb,wc,0,p) -> "+INVARIANT,
}
HELPER_TARGET_SHA256 = {
    "shuffle":"abafb5ee4f53fbdf9563ee79fd3df8b379c36830b2748f79a3a5f78a2a2c31be",
    "extend":"576d73a51eb5986fbe62b62a15c55429e6bd78806fcb45a058333b3db93b326b",
    "weights_exists":"c55f60af28565496b70fdf1044086322309edfacd0546aabc883abed41220409",
    "invariant":"c1a5273e13b7ba825ff72341bda7b18ede213f72ec46cfdc2d9abe3607025bbd",
}
ARCHIVES = (WEIGHTS_ARCHIVE,FACTORIAL_ARCHIVE)
ENDPOINT_SOURCES = {name:WEIGHT_ENDPOINTS[name] for name in (
    "combination_exists","beta_exists","beta_unique","beta_extend","le_refl","le_succ",
    "succ_le_succ","le_of_succ_le_succ","le_eq_or_lt","zero_le","lt_not_le","mul_one","one_mul","mul_comm","mul_assoc")}
ENDPOINT_SOURCES.update({name:POWER_ENDPOINTS[name] for name in ("power_exists","power_zero","power_step","le_trans")})
ENDPOINT_SOURCES.update({name:SCALE_HELPERS[name] for name in ("scaled_extension","scale_adjacent")})
ENDPOINT_OWNERS = {name:"CV022" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:"CV030" for name in ("power_exists","power_zero","power_step")})
HELPER_DEPENDENCIES = {
    "shuffle":("mul_assoc","mul_comm"),
    "extend":("combination_exists","beta_extend","scaled_extension","beta_exists","beta_unique","le_refl","le_of_succ_le_succ","le_eq_or_lt","succ_le_succ","scale_adjacent"),
    "weights_exists":("beta_extend","zero_le","lt_not_le","extend"),
    "invariant":("beta_unique","power_zero","mul_one","power_step","beta_exists","le_refl","le_succ","le_trans","shuffle"),
    "CV038":("weights_exists","beta_exists","power_exists","invariant","le_refl","one_mul"),
}


class GeometricWeightsError(ValueError):
    """Changed geometric computation, actual power relation or proof data."""


def definition_registry():
    result = dict(weighted_registry())
    for name,d in power_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise GeometricWeightsError("geometric weight/power definition mismatch")
        result[name] = d
    return MappingProxyType(result)


def frozen_geometric_weights_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=2 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise GeometricWeightsError("CV038 exact geometric weight construction changed")
    return target


def source_contract():
    return dict(code="CV038",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_geometric_weights_constructed=True,actual_power_constructed=True,
        initial_weight_is_power_proved=True,all_in_range_weight_power_products_proved=True,
        zero_multiplier_allowed=True,new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",weighted_term_prefix_constructed=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def geometric_weights_source_pins():
    result = horner_weighted_sum_source_pins()
    for name,pin in weight_factorials_source_pins().items():
        if name in result and result[name]!=pin:
            raise GeometricWeightsError("source pin disagreement")
        result[name] = pin
    expected = {"scripts/sqrt2_power_horner_weighted_sum.py":"4fd1200a0283f2385ce0836f585452d6bede2baefaf0223e48e2f1edb2fef0ec",
        "scripts/sqrt2_power_normalized_composition.py":"d2444ad39a22c50a6afbeb5f3ec3b67527c25f2c5985877ec4604dad08790d23",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_geometric_weights.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise GeometricWeightsError("geometric weight source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _shuffle(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.terms import Mul
    return introduce(s,("w","q","t"),(),lambda u:_chain(
        specialize(u,"mul_comm",u.term("w"),Mul(u.term("q"),u.term("t"))),
        specialize(u,"mul_assoc",*u.terms(("q","t","w"))),
        specialize(u,"mul_comm",u.term("q"),Mul(u.term("t"),u.term("w")))))


def _extend(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,CongMul,CongS,EqRefl,EqSym,EqTrans,OrElim
    from peano_lab.kernel.terms import Succ,Zero
    def scaled(u,index,x,y,bound,old,new):
        return apply(specialize(u,"scaled_extension",u.term("t"),*u.terms(O+C+W),Succ(u.term("N")),index,x,y),
            u.hyp("scaling"),AndElimR(u.hyp("extension")),bound,old,new)
    def extended(t):
        def adjacent(u):
            def last(v):
                N,a,b = v.terms(("N","a","b"))
                first = _subst(v,registry,"BetaAt(wb,wc,slot,a)",v.hyp("last"),v.hyp("first"))
                second = _subst(v,registry,"BetaAt(wb,wc,slot,b)",CongS(v.hyp("last")),v.hyp("second"))
                ae = scaled(v,N,Succ(Zero()),a,specialize(v,"le_refl",Succ(N)),AndElimL(v.hyp("old")),first)
                be = apply(specialize(v,"beta_unique",*v.terms(W),Succ(N),b,Succ(Zero())),second,AndElimL(v.hyp("extension")))
                return EqTrans(ae,CongMul(EqRefl(v.term("t")),EqSym(be)))
            def earlier(v):
                def chosen(w):
                    j,N,x,y,a,b = w.terms(("j","N","x","y","a","b"))
                    next_bound = apply(specialize(w,"succ_le_succ",Succ(j),N),w.hyp("earlier"))
                    ae = scaled(w,j,x,a,w.hyp("bound"),w.hyp("value_x"),w.hyp("first"))
                    be = scaled(w,Succ(j),y,b,next_bound,w.hyp("value_y"),w.hyp("second"))
                    old = apply(instantiate(AndElimR(w.hyp("old")),j,x,y),w.hyp("earlier"),w.hyp("value_x"),w.hyp("value_y"))
                    return apply(specialize(w,"scale_adjacent",w.term("t"),w.term("t"),x,y,a,b),old,ae,be)
                return eliminate(v,specialize(v,"beta_exists",*v.terms(O+("j",))),("x",),"value_x",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(O),Succ(w.term("j"))),("y",),"value_y",chosen))
            lower = apply(specialize(u,"le_of_succ_le_succ",*u.terms(("j","N"))),u.hyp("bound"))
            cases = apply(specialize(u,"le_eq_or_lt",*u.terms(("j","N"))),lower)
            return OrElim(cases,last(u.hypothesis("last")),earlier(u.hypothesis("earlier")))
        graph = AndIntro(AndElimL(t.hyp("extension")),introduce(t,("j","a","b"),("bound","first","second"),adjacent))
        return witness(t.terms(W),graph)
    return introduce(s,("t","N")+O,("old",),lambda t:
        eliminate(t,specialize(t,"combination_exists",t.term("t"),Zero(),*t.terms(O+O),Succ(t.term("N"))),C,"scaling",lambda u:
            eliminate(u,specialize(u,"beta_extend",Succ(u.term("N")),*u.terms(C),Succ(Zero())),W,"extension",extended)))


def _weights_exists(s,target):
    from peano_lab.kernel.proofs import AndElimL,AndIntro,BotElim,Ind
    from peano_lab.kernel.terms import Succ,Zero
    def base(t):
        def chosen(u):
            empty = introduce(u,("j","a","b"),("bound","first","second"),lambda v:
                BotElim(apply(specialize(v,"lt_not_le",v.term("j"),Zero()),v.hyp("bound"),specialize(v,"zero_le",v.term("j")))))
            return witness(u.terms(W),AndIntro(AndElimL(u.hyp("extension")),empty))
        return eliminate(t,specialize(t,"beta_extend",Zero(),Zero(),Zero(),Succ(Zero())),W,"extension",chosen)
    def successor(t):
        return eliminate(t,t.hyp("IH"),O,"old",lambda u:apply(specialize(u,"extend",*u.terms(("t","N")+O)),u.hyp("old")))
    return introduce(s,("t",),(),lambda t:Ind(target.body.body,base(t),introduce(t,("N",),("IH",),successor)))


def _invariant(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Succ,Zero
    def base(t):
        wp = apply(specialize(t,"beta_unique",*t.terms(W),Zero(),*t.terms(("w","p"))),t.hyp("weight"),t.hyp("initial"))
        q1 = apply(specialize(t,"power_zero",t.term("t"),Zero(),t.term("q")),EqRefl(Zero()),t.hyp("power"))
        return _chain(CongMul(wp,q1),specialize(t,"mul_one",t.term("p")))
    def successor(t):
        def chosen(u):
            j,N,a,w = u.terms(("j","N","a","w"))
            earlier = apply(specialize(u,"le_trans",j,Succ(j),N),apply(specialize(u,"le_succ",j,j),specialize(u,"le_refl",j)),u.hyp("bound"))
            previous = apply(specialize(u,"IH",a,u.term("q0")),earlier,u.hyp("old_weight"),AndElimL(u.hyp("power_data")))
            adjacent = apply(instantiate(AndElimR(u.hyp("weights")),j,a,w),u.hyp("bound"),u.hyp("old_weight"),u.hyp("weight"))
            return _chain(CongMul(EqRefl(w),AndElimR(u.hyp("power_data"))),specialize(u,"shuffle",w,*u.terms(("q0","t"))),
                CongMul(EqSym(adjacent),EqRefl(u.term("q0"))),previous)
        power = apply(specialize(t,"power_step",*t.terms(("t","j")),Succ(t.term("j")),t.term("q")),EqRefl(Succ(t.term("j"))),t.hyp("power"))
        return eliminate(t,power,("q0",),"power_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(W+("j",))),("a",),"old_weight",chosen))
    motive = target
    for _ in range(5):
        motive = motive.body
    motive = motive.right.right.body
    return introduce(s,("t","N")+W+("p",),("weights","initial"),lambda t:Ind(motive,
        introduce(t,("w","q"),("bound","weight","power"),base),
        introduce(t,("j",),("IH",),lambda u:introduce(u,("w","q"),("bound","weight","power"),successor))))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        invariant = apply(specialize(t,"invariant",*t.terms(("t","N")+W+("w0",))),t.hyp("weights"),t.hyp("initial"))
        terminal = apply(instantiate(invariant,t.term("N"),Succ(Zero()),t.term("p")),specialize(t,"le_refl",t.term("N")),AndElimL(t.hyp("weights")),t.hyp("power"))
        equal = _chain(EqSym(terminal),specialize(t,"one_mul",t.term("p")))
        initial = _subst(t,registry,"BetaAt(wb,wc,0,slot)",equal,t.hyp("initial"))
        normalized = apply(specialize(t,"invariant",*t.terms(("t","N")+W+("p",))),t.hyp("weights"),initial)
        return witness(t.terms(W+("p",)),conjunction(t.hyp("weights"),t.hyp("power"),initial,normalized))
    return introduce(s,("t","N"),(),lambda t:
        eliminate(t,specialize(t,"weights_exists",*t.terms(("t","N"))),W,"weights",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(W),Zero()),("w0",),"initial",lambda v:
                eliminate(v,specialize(v,"power_exists",*v.terms(("t","N"))),("p",),"power",chosen))))


def prove_geometric_weights(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"shuffle":_shuffle,"extend":lambda s:_extend(s,registry),
        "weights_exists":lambda s:_weights_exists(s,parse_named(HELPER_SOURCES["weights_exists"],registry=registry)),
        "invariant":lambda s:_invariant(s,parse_named(HELPER_SOURCES["invariant"],registry=registry)),"CV038":lambda s:_root(s,registry)}
    return assemble_mixed_certificate(code="CV038",target=frozen_geometric_weights_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,
        pins=geometric_weights_source_pins,contract=source_contract(),limits=limits,new_induction_count=2)
