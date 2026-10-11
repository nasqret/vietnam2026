"""CV087: construct an actual finite outer-exp tail bounded by twice its head.

For d!=0 and x<=d, the supplied recurrence gives twice each next term <=
the current term from index one onward. Decode an actual affine tail, retain
its finite ratio predicate and construct its sum. No infinite tail is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_scaled_exp_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as exp_registry,scaled_exp_bound_source_pins,
    HELPER_SOURCES as EXP_HELPERS,ENDPOINT_SOURCES as EXP_ENDPOINTS,
)
from sqrt2_power_ratio_sum_bound import (
    definition_registry as ratio_registry,ratio_sum_bound_source_pins,NAMED_SOURCE as SUM_SOURCE,
)
from sqrt2_power_composition_majorant import BOUND_ARCHIVE
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE,ENDPOINT_SOURCES as SPLIT_ENDPOINTS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-scaled-exp-tail-v1"
T,U = ("tb","tc"),("ub","uc")
PARAMETERS = ("d","x")+T+("m","N","a")
RECURRENCE = "NatScaledExpRecurrence(d,x,tb,tc,(S m)+N)"
SLICE = "NatAffineSlice(tb,tc,S m,1,ub,uc,S N)"
RATIO = "NatRatioBoundPrefix(ub,uc,1,S N)"
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". ~d=0 -> Le(x,d) -> "+RECURRENCE+" -> BetaAt(tb,tc,S m,a) -> exists ub uc s. "+SLICE+" /\\ ("+RATIO+" /\\ (Sum(ub,uc,S N,s) /\\ Le(s,2*a)))"
TARGET_SHA256 = "d92d8780097ceaf3810aba46e31ffe2e3c8357929685f8314972342821425d8b"
HELPER_SOURCES = {
    "ratio":"forall d x j a b h. ~d=0 -> Le(x,d) -> Le(h,S j) -> ((S j)*d)*b=x*a -> Le(h*b,a)",
    "slice_entry":"forall tb tc ub uc M L i a. NatAffineSlice(tb,tc,M,1,ub,uc,L) -> Lt(i,L) -> BetaAt(ub,uc,i,a) -> BetaAt(tb,tc,M+i,a)",
    "tail_ratio":"forall d x tb tc m N ub uc. ~d=0 -> Le(x,d) -> "+RECURRENCE+" -> "+SLICE+" -> "+RATIO,
    "tail_head":"forall tb tc m N ub uc a. "+SLICE+" -> BetaAt(tb,tc,S m,a) -> BetaAt(ub,uc,0,a)",
}
HELPER_TARGET_SHA256 = {
    "ratio":"f59211984b20751147d96bb77021e6e31fd59a0ba0b4b5da54ea3a12f8108304",
    "slice_entry":"8c94f56ef5807bd02442d70ed9a139faa77486266cf7f319a43caf1394f87a88",
    "tail_ratio":"fc3b552385c493436c04164d8dbbcad25d4e4fe6fdf0f8197ec746227c5bb584",
    "tail_head":"8e1bb330878d321330a0abe228ed96a6b259fd4dcadf24cf83cd935ff46c7afb",
}
RATIO_ARCHIVE = dict(case="CV068",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-ratio-sum-bound-v1/generation-process.json.gz",
    bytes=27407,sha256="36196921c26e758ea6fbe4ab0cac6eb90f1429e5ca5c2eda90b46e30cc8e498c",
    raw_bytes=356468,raw_sha256="108dd0ceca4063a9fa3e45dc76d64cee44bb1f3cbdd3375af283df1ec0a45471",
    bundle_bytes=188250,bundle_sha256="88d9a3d159a222530ecfb17ba3316739ad965970ac80dd427f3bbd98c8e94638",
    nodes=112,root=111,target_ast_sha256="fd9dbb392a8f45725f090de43a5e13f1e269a2e0b79293eeef87a1464dcd8f28")
ARCHIVES = (BOUND_ARCHIVE,COMPOSITION_ARCHIVE,RATIO_ARCHIVE)
ENDPOINT_SOURCES = {name:EXP_ENDPOINTS[name] for name in (
    "mul_right_mono","le_trans","mul_assoc","mul_comm","one_mul","beta_exists","beta_unique",
    "zero_le","le_succ","le_of_succ_le_succ")}
ENDPOINT_SOURCES.update(mul_le_cancel=EXP_HELPERS["mul_le_cancel"],sum_ratio=SUM_SOURCE,
    slice_exists=SPLIT_ENDPOINTS["slice_exists"],
    succ_le_succ="forall a b. Le(a,b) -> Le(S a,S b)",
    add_left_mono="forall a b c. Le(a,b) -> Le(c+a,c+b)",
    add_succ_left="forall a b. S a+b=S(a+b)")
ENDPOINT_OWNERS = {name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(sum_ratio="CV068",slice_exists="CV061",succ_le_succ="CV061",add_succ_left="CV061")
HELPER_DEPENDENCIES = {
    "ratio":("mul_right_mono","le_trans","mul_assoc","mul_comm","mul_le_cancel"),
    "slice_entry":("one_mul",),
    "tail_ratio":("ratio","slice_entry","le_of_succ_le_succ","le_succ","add_left_mono","zero_le","succ_le_succ","add_succ_left","one_mul"),
    "tail_head":("slice_entry","beta_exists","beta_unique","zero_le","succ_le_succ"),
    "CV087":("slice_exists","tail_ratio","tail_head","sum_ratio"),
}


class ScaledExpTailError(ValueError):
    """Changed actual tail, recurrence horizon or necessary denominator guard."""


def definition_registry():
    result = dict(exp_registry())
    for name,d in ratio_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise ScaledExpTailError("tail conservative definition mismatch")
        if name not in result and d.stable_id in {v.stable_id for v in result.values()}:
            raise ScaledExpTailError("tail conservative definition id collision")
        result[name] = d
    return MappingProxyType(result)


def frozen_scaled_exp_tail_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ScaledExpTailError("CV087 exact finite outer-exp tail changed")
    return target


def source_contract():
    return dict(code="CV087",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,supplied_term_table_and_head_preserved=True,actual_tail_slice_and_sum_constructed=True,
        actual_tail_ratio_proved_and_retained=True,cutoff="m+1",tail_length="N+1",
        recurrence_horizon="m+1+N",argument_bound="x<=d",nonzero_denominator_required=True,
        finite_tail_bound="sum<=2*first_omitted_term",zero_argument_and_zero_tail_horizon_allowed=True,
        cutoff_zero_allowed=False,first_omitted_term_decay_claimed=False,infinite_remainder_claimed=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_limit_claim=False,
        closes_IR072=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def scaled_exp_tail_source_pins():
    result = scaled_exp_bound_source_pins()
    for name,pin in ratio_sum_bound_source_pins().items():
        if name in result and result[name]!=pin:
            raise ScaledExpTailError("tail source pin disagreement")
        result[name] = pin
    expected = {
        "scripts/sqrt2_power_scaled_exp_bound.py":"717128c4845645cca66209b12512d4de2905d6ecc4eebad8c04c197647f9ee0c",
        "scripts/sqrt2_power_ratio_sum_bound.py":"18f2cee3fa530a2e4e658c1ac097f65710b7080776714643bff400eeca14ef15",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_scaled_exp_tail.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ScaledExpTailError("finite outer-exp tail source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _ratio(s,registry):
    from peano_lab.kernel.terms import Mul,Succ
    def finish(t):
        d,x,j,a,b,h = t.terms(("d","x","j","a","b","h"))
        lower = apply(specialize(t,"mul_right_mono",h,Succ(j),d),t.hyp("index"))
        lower = apply(specialize(t,"mul_right_mono",Mul(h,d),Mul(Succ(j),d),b),lower)
        lower = _subst(t,registry,"Le((h*d)*b,slot)",t.hyp("recurrence"),lower)
        upper = apply(specialize(t,"mul_right_mono",x,d,a),t.hyp("argument"))
        bound = apply(specialize(t,"le_trans",Mul(Mul(h,d),b),Mul(x,a),Mul(d,a)),lower,upper)
        bound = _subst(t,registry,"Le(slot,d*a)",_multiplicative_equal(t,Mul(Mul(h,d),b),Mul(d,Mul(h,b))),bound)
        return apply(specialize(t,"mul_le_cancel",d,Mul(h,b),a),t.hyp("nonzero"),bound)
    return introduce(s,("d","x","j","a","b","h"),("nonzero","argument","index","recurrence"),finish)


def _slice_entry(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl
    def finish(t):
        entry = apply(specialize(t,"slice",*t.terms(("i","a"))),t.hyp("bound"),t.hyp("entry"))
        index = CongAdd(EqRefl(t.term("M")),specialize(t,"one_mul",t.term("i")))
        return _subst(t,registry,"BetaAt(tb,tc,slot,a)",index,entry)
    return introduce(s,T+U+("M","L","i","a"),("slice","bound","entry"),finish)


def _tail_ratio(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongS,EqSym
    from peano_lab.kernel.terms import Add,Succ,Zero
    one = Succ(Zero());two = Succ(one)
    def entry(t):
        m,N,i,a,b = t.terms(("m","N","i","a","b"));M = Succ(m);j = Add(M,i)
        below = apply(specialize(t,"le_of_succ_le_succ",Succ(i),N),t.hyp("bound"))
        current_bound = apply(specialize(t,"le_succ",Succ(i),N),below)
        shifted = apply(specialize(t,"add_left_mono",Succ(i),N,M),below)
        shifted = _subst(t,registry,"Le(slot,(S m)+N)",instantiate(Axiom("PA4"),M,i),shifted)
        current = apply(specialize(t,"slice_entry",*t.terms(T+U),M,Succ(N),i,a),t.hyp("slice"),current_bound,t.hyp("current"))
        following = apply(specialize(t,"slice_entry",*t.terms(T+U),M,Succ(N),Succ(i),b),t.hyp("slice"),t.hyp("bound"),t.hyp("following"))
        following = _subst(t,registry,"BetaAt(tb,tc,slot,b)",instantiate(Axiom("PA4"),M,i),following)
        equation = apply(specialize(t,"recurrence",j,a,b),shifted,current,following)
        height = apply(specialize(t,"succ_le_succ",Zero(),Add(m,i)),specialize(t,"zero_le",Add(m,i)))
        height = apply(specialize(t,"succ_le_succ",one,Succ(Add(m,i))),height)
        height = _subst(t,registry,"Le(2,slot)",EqSym(CongS(specialize(t,"add_succ_left",m,i))),height)
        result = apply(specialize(t,"ratio",*t.terms(("d","x")),j,a,b,two),t.hyp("nonzero"),t.hyp("argument"),height,equation)
        return _subst(t,registry,"Le(2*b,slot)",EqSym(specialize(t,"one_mul",a)),result)
    return introduce(s,("d","x")+T+("m","N")+U,("nonzero","argument","recurrence","slice"),lambda t:
        introduce(t,("i","a","b"),("bound","current","following"),entry))


def _tail_head(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        M,N = Succ(t.term("m")),Succ(t.term("N"));zero = Zero()
        bound = apply(specialize(t,"succ_le_succ",zero,t.term("N")),specialize(t,"zero_le",t.term("N")))
        old = apply(specialize(t,"slice_entry",*t.terms(T+U),M,N,zero,t.term("b")),t.hyp("slice"),bound,t.hyp("entry"))
        old = _subst(t,registry,"BetaAt(tb,tc,slot,b)",instantiate(Axiom("PA3"),M),old)
        same = apply(specialize(t,"beta_unique",*t.terms(T),M,*t.terms(("b","a"))),old,t.hyp("head"))
        return _subst(t,registry,"BetaAt(ub,uc,0,slot)",same,t.hyp("entry"))
    return introduce(s,T+("m","N")+U+("a",),("slice","head"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(U),Zero()),("b",),"entry",chosen))


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ,Zero
    def tail_ratio(t):
        return apply(specialize(t,"tail_ratio",*t.terms(("d","x")+T+("m","N")+U)),
            t.hyp("nonzero"),t.hyp("argument"),t.hyp("recurrence"),t.hyp("slice"))
    def summed(t):
        return witness(t.terms(U+("s",)),conjunction(t.hyp("slice"),tail_ratio(t),AndElimL(t.hyp("sum_bound")),AndElimR(t.hyp("sum_bound"))))
    def sliced(t):
        head = apply(specialize(t,"tail_head",*t.terms(T+("m","N")+U+("a",))),t.hyp("slice"),t.hyp("head"))
        result = apply(specialize(t,"sum_ratio",*t.terms(U),Succ(Zero()),Succ(t.term("N")),t.term("a")),tail_ratio(t),head)
        return eliminate(t,result,("s",),"sum_bound",summed)
    return introduce(s,PARAMETERS,("nonzero","argument","recurrence","head"),lambda t:
        eliminate(t,specialize(t,"slice_exists",*t.terms(T),Succ(t.term("m")),Succ(Zero()),Succ(t.term("N"))),U,"slice",sliced))


def prove_scaled_exp_tail(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV087",target=frozen_scaled_exp_tail_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"ratio":lambda s:_ratio(s,registry),"slice_entry":lambda s:_slice_entry(s,registry),
            "tail_ratio":lambda s:_tail_ratio(s,registry),"tail_head":lambda s:_tail_head(s,registry),"CV087":_root},
        pins=scaled_exp_tail_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
