"""CV068: finite geometric domination from actual consecutive-term bounds.

If (r+1)*a[i+1]<=r*a[i] throughout a supplied finite prefix, construct its
actual sum s and prove s<=(r+1)*a[0]. Empty prefixes and r=0 are included.
The ratio predicate is separate from the sum computation; no limits appear.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_factorial_majorant import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as base_registry,factorial_majorant_source_pins,
)
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE
from sqrt2_power_convolution_commutative import ENDPOINT_SOURCES as SUM_ENDPOINTS,HELPER_SOURCES as SUM_HELPERS
from sqrt2_power_periodic_convolution import COMM_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-ratio-sum-bound-v1"
A = ("ab","ac")
FIXED = A+("r","N","a0")
DEFINITIONS = (
    ("ND0441","NatRatioBoundPrefix",("ab","ac","r","N"),
     "forall i a b. Lt(S i,N) -> BetaAt(ab,ac,i,a) -> BetaAt(ab,ac,S i,b) -> Le((S r)*b,r*a)",
     ("Lt","BetaAt","Le"),"972cff0deb8ca5ff626e65af29a6c4e2b282afa28ad4417bed00db01bcf72e3e"),
)
RATIO = "NatRatioBoundPrefix(ab,ac,r,N)"
ALL_PREFIXES = "forall k y z. Le(S k,N) -> Sum(ab,ac,S k,y) -> BetaAt(ab,ac,k,z) -> Le(y+r*z,(S r)*a0)"
NAMED_SOURCE = "forall "+" ".join(FIXED)+". "+RATIO+" -> BetaAt(ab,ac,0,a0) -> exists s. Sum(ab,ac,N,s) /\\ Le(s,(S r)*a0)"
TARGET_SHA256 = "fd9dbb392a8f45725f090de43a5e13f1e269a2e0b79293eeef87a1464dcd8f28"
HELPER_SOURCES = {
    "all_prefixes":"forall "+" ".join(FIXED)+". "+RATIO+" -> BetaAt(ab,ac,0,a0) -> "+ALL_PREFIXES,
    "all_values":"forall "+" ".join(FIXED+("s",))+". "+RATIO+" -> BetaAt(ab,ac,0,a0) -> Sum(ab,ac,N,s) -> Le(s,(S r)*a0)",
}
HELPER_TARGET_SHA256 = {
    "all_prefixes":"6a233902b9ec713e92cc9ba8a5579e3face01437a9a979bf85f01a545244c66e",
    "all_values":"b6e203f41ee49e194ae78f5e506e553b846172d6717a22a6247e063b7e7677b9",
}
ARCHIVES = (COMPOSITION_ARCHIVE,COMM_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:SUM_ENDPOINTS[name] for name in ("sum_exists","sum_zero","sum_decompose","beta_exists","beta_unique","mul_comm","add_comm")},
    "sum_one":SUM_HELPERS["sum_one"],
    "mul_succ_left":"forall a b. (S a)*b=a*b+b",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "zero_le":"forall a. Le(0,a)",
    "zero_or_succ":"forall n. n=0 \\/ exists k. n=S k",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["sum_one"] = "CV010"
HELPER_DEPENDENCIES = {
    "all_prefixes":("sum_one","beta_unique","mul_succ_left","add_comm","le_refl","sum_decompose","beta_exists","le_succ","le_trans","add_assoc","add_left_mono"),
    "all_values":("zero_or_succ","sum_zero","zero_le","beta_exists","all_prefixes","le_refl","add_comm","le_trans"),
    "CV068":("sum_exists","all_values"),
}


class RatioSumBoundError(ValueError):
    """Changed consecutive-term relation or actual finite-sum statement."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    result = dict(base_registry())
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids = {d["id"] for d in parent}|{d.stable_id for d in result.values()}
    names = {d["name"] for d in parent}|set(result)
    for identifier,name,params,source,deps,digest in DEFINITIONS:
        if identifier in ids or name in names or not set(deps)<=result.keys():
            raise RatioSumBoundError("ratio-prefix definition collision or forward dependency")
        formula = parse_named(source,params,result)
        if json_hash(encode_formula(formula))!=digest:
            raise RatioSumBoundError("ratio-prefix conservative expansion changed")
        text = pretty_formula(formula,list(params))
        d = _definition(stable_id=identifier,name=name,parameters=params,template_source=text,
            summary="Separate adjacent-entry bound; it contains no sum or convergence assertion.",
            category="irrationality_formal_series",conceptual_dependencies=deps)
        if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula:
            raise RatioSumBoundError("ratio-prefix definition failed exact conservative roundtrip")
        result[name] = d;ids.add(identifier);names.add(name)
    return MappingProxyType(result)


def frozen_ratio_sum_bound_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise RatioSumBoundError("CV068 exact finite ratio sum bound target changed")
    return target


def source_contract():
    return dict(code="CV068",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,explicit_consecutive_ratio_bounds_required=True,actual_head_required=True,
        actual_sum_constructed=True,empty_prefix_and_zero_ratio_allowed=True,
        inequality="s<=(r+1)*a0",supplied_sum_helper=True,retained_prefix_surplus="sum+r*last<=(r+1)*a0",
        new_definition_ids=["ND0441"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_limit_claim=False,finite_exp_sum_bound_claimed=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def ratio_sum_bound_source_pins():
    result = factorial_majorant_source_pins()
    expected = {"scripts/sqrt2_power_factorial_majorant.py":"e5b825cb23ce9312c2b05c9e9ef51529415440a3810c467d3b912d5ff0593a8a",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_ratio_sum_bound.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise RatioSumBoundError("ratio sum source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _all_prefixes(s,target,registry):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def base(t):
        y,z,r,a0 = t.terms(("y","z","r","a0"))
        ya = apply(specialize(t,"sum_one",*t.terms(A),y,a0),t.hyp("sum"),t.hyp("head"))
        za = apply(specialize(t,"beta_unique",*t.terms(A),Zero(),z,a0),t.hyp("last"),t.hyp("head"))
        equal = _chain(CongAdd(ya,CongMul(EqRefl(r),za)),specialize(t,"add_comm",a0,Mul(r,a0)),EqSym(specialize(t,"mul_succ_left",r,a0)))
        return _subst(t,registry,"Le(y+r*z,slot)",equal,specialize(t,"le_refl",Add(y,Mul(r,z))))
    def successor(t):
        def chosen(u):
            k,N,y,z,r,a0,b,c,x = u.terms(("k","N","y","z","r","a0","b","c","x"));sk = Succ(k)
            data = u.hyp("sum_data")
            earlier = apply(specialize(u,"le_trans",sk,Succ(sk),N),apply(specialize(u,"le_succ",sk,sk),specialize(u,"le_refl",sk)),u.hyp("bound"))
            old = apply(specialize(u,"IH",x,c),earlier,field(data,1,3),u.hyp("previous"))
            ratio = apply(specialize(u,"ratio",k,c,b),u.hyp("bound"),u.hyp("previous"),field(data,0,3))
            lifted = apply(specialize(u,"add_left_mono",Mul(Succ(r),b),Mul(r,c),x),ratio)
            bz = apply(specialize(u,"beta_unique",*u.terms(A),sk,b,z),field(data,0,3),u.hyp("last"))
            equal = _chain(CongAdd(field(data,2,3),CongMul(EqRefl(r),EqSym(bz))),
                specialize(u,"add_assoc",x,b,Mul(r,b)),
                CongAdd(EqRefl(x),specialize(u,"add_comm",b,Mul(r,b))),
                CongAdd(EqRefl(x),EqSym(specialize(u,"mul_succ_left",r,b))))
            lifted = _subst(u,registry,"Le(slot,x+r*c)",EqSym(equal),lifted)
            return apply(specialize(u,"le_trans",Add(y,Mul(r,z)),Add(x,Mul(r,c)),Mul(Succ(r),a0)),lifted,old)
        return eliminate(t,apply(specialize(t,"sum_decompose",*t.terms(A),Succ(t.term("k")),t.term("y")),t.hyp("sum")),("b","x"),"sum_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(A+("k",))),("c",),"previous",chosen))
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.right.right.body
    row_params,row_hyps = ("y","z"),("bound","sum","last")
    return introduce(s,FIXED,("ratio","head"),lambda t:Ind(motive,introduce(t,row_params,row_hyps,base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,row_params,row_hyps,successor))))


def _all_values(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import EqSym,OrElim
    from peano_lab.kernel.terms import Add,Mul,Succ
    def zero(t):
        empty = _subst(t,registry,"Sum(ab,ac,slot,s)",t.hyp("zero"),t.hyp("sum"))
        s0 = apply(specialize(t,"sum_zero",*t.terms(A+("s",))),empty)
        return _subst(t,registry,"Le(slot,(S r)*a0)",EqSym(s0),specialize(t,"zero_le",Mul(Succ(t.term("r")),t.term("a0"))))
    def positive(t):
        def chosen(u):
            k,N,r,a0,s,z = u.terms(("k","N","r","a0","s","z"));length = Succ(k)
            partial = _subst(u,registry,"Sum(ab,ac,slot,s)",u.hyp("index"),u.hyp("sum"))
            bound = _subst(u,registry,"Le(S k,slot)",EqSym(u.hyp("index")),specialize(u,"le_refl",length))
            invariant = apply(specialize(u,"all_prefixes",*u.terms(FIXED)),u.hyp("ratio"),u.hyp("head"))
            strong = apply(instantiate(invariant,k,s,z),bound,partial,u.hyp("last"))
            weaker = witness((Mul(r,z),),specialize(u,"add_comm",Mul(r,z),s))
            return apply(specialize(u,"le_trans",s,Add(s,Mul(r,z)),Mul(Succ(r),a0)),weaker,strong)
        return eliminate(t,t.hyp("positive"),("k",),"index",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(A+("k",))),("z",),"last",chosen))
    return introduce(s,FIXED+("s",),("ratio","head","sum"),lambda t:
        OrElim(specialize(t,"zero_or_succ",t.term("N")),zero(t.hypothesis("zero")),positive(t.hypothesis("positive"))))


def _root(s):
    from peano_lab.kernel.proofs import AndIntro
    def chosen(t):
        bound = apply(specialize(t,"all_values",*t.terms(FIXED+("s",))),t.hyp("ratio"),t.hyp("head"),t.hyp("sum"))
        return witness((t.term("s"),),AndIntro(t.hyp("sum"),bound))
    return introduce(s,FIXED,("ratio","head"),lambda t:
        eliminate(t,specialize(t,"sum_exists",*t.terms(A+("N",))),("s",),"sum",chosen))


def prove_ratio_sum_bound(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV068",target=frozen_ratio_sum_bound_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"all_prefixes":lambda s:_all_prefixes(s,parse_named(HELPER_SOURCES["all_prefixes"],registry=registry),registry),
            "all_values":lambda s:_all_values(s,registry),"CV068":_root},
        pins=ratio_sum_bound_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
