"""CV097: construct actual rescaled exponential terms and their finite sum.

Scale every term by c and multiply the argument numerator/denominator by f.
The checked finite recurrences and sum identity remain valid, even for zero
scalars. No rational validity or equality of independently coded tables is used.
"""
from hashlib import sha256

from sqrt2_power_sum_linear_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,sum_linear_bound_source_pins,BOUND_ARCHIVE,
)
from sqrt2_power_series_linear_combination import (
    COMBINATION_SOURCE,series_linear_combination_source_pins,
)
from sqrt2_power_weighted_series_trace import COMBINATION_ARCHIVE
from sqrt2_power_sum_linearity import LINEARITY_SOURCE
from sqrt2_power_euler_product import LINEARITY_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-rescaling-v1"
A,U=("ab","ac"),("ub","uc")
PARAMETERS=("d","x","f","c","N")+A+("a0","s")
OUTPUTS=U+("t",)
GRAPH="NatLinearTriple(c,0,1,ab,ac,ab,ac,ub,uc,S N)"
ENTRY_GRAPH="NatLinearTriple(c,0,1,ab,ac,ab,ac,ub,uc,L)"
RECURRENCE="NatScaledExpRecurrence(d,x,ab,ac,N)"
SCALED_RECURRENCE="NatScaledExpRecurrence(d*f,f*x,ub,uc,N)"
PARTS=(GRAPH,SCALED_RECURRENCE,"BetaAt(ub,uc,0,c*a0)","Sum(ub,uc,S N,t)","t=c*s")


def conjoin(parts):
    result=parts[-1]
    for part in reversed(parts[:-1]):
        result=part+" /\\ ("+result+")"
    return result


NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+RECURRENCE+" -> BetaAt(ab,ac,0,a0) -> Sum(ab,ac,S N,s) -> exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256="1366d756cc52f3aeda1363ed3188f534bc5489ed2977f09a101be2c92e875243"
HELPER_SOURCES={
    "entry":"forall c ab ac ub uc L i a b. "+ENTRY_GRAPH+" -> Lt(i,L) -> BetaAt(ab,ac,i,a) -> BetaAt(ub,uc,i,b) -> b=c*a",
    "recurrence":"forall d x f c N ab ac ub uc. "+RECURRENCE+" -> "+GRAPH+" -> "+SCALED_RECURRENCE,
    "head":"forall c ab ac ub uc N a0. "+GRAPH+" -> BetaAt(ab,ac,0,a0) -> BetaAt(ub,uc,0,c*a0)",
}
HELPER_TARGET_SHA256={
    "entry":"2cb48af6f55f8976a78ffa539c8a2be5200f9e5be9f72e386ffc830fb86861ef",
    "recurrence":"512c7a72704de8219920a03c154aa01b58b10e198bc313c4ae0fa0d55c92fc7e",
    "head":"ccb245727513f2cb623d98f5545cab7d7655169eb8cc41fd7ff7abfeed93edae",
}
ARCHIVES=(COMBINATION_ARCHIVE,LINEARITY_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "combination_exists":COMBINATION_SOURCE,"linearity":LINEARITY_SOURCE,
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "sum_exists":"forall b c N. exists n. Sum(b,c,N,n)",
    "one_mul":"forall a. 1*a=a","zero_mul":"forall a. 0*a=0",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)","zero_le":"forall a. Le(0,a)",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(combination_exists="CV018",linearity="CV006")
HELPER_DEPENDENCIES={
    "entry":("one_mul","zero_mul"),
    "recurrence":("entry","beta_exists","le_succ","succ_le_succ","mul_assoc","mul_comm"),
    "head":("entry","beta_exists","zero_le","succ_le_succ"),
    "CV097":("combination_exists","sum_exists","recurrence","head","linearity","one_mul","zero_mul"),
}


class ExpRescalingError(ValueError):
    """Changed actual scaled table, argument factors, head or sum identity."""


def frozen_exp_rescaling_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=9 or len(premises)!=3 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRescalingError("CV097 exact constructed exponential rescaling changed")
    return target


def source_contract():
    return dict(code="CV097",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,supplied_recurrence_head_and_sum_preserved=True,actual_scaled_table_and_sum_constructed=True,
        pointwise_relation_constructed_not_assumed=True,term_scaling="U[j]=c*A[j]",
        denominator="d*f",numerator="f*x",actual_head="c*a0",sum_identity="t=c*s",
        zero_denominator_factors_and_scalars_allowed=True,zero_degree_allowed=True,new_induction_needed=False,
        code_number_equality_claimed=False,rational_validity_claimed=False,analytic_limit_claim=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def exp_rescaling_source_pins():
    result=sum_linear_bound_source_pins()
    for name,pin in series_linear_combination_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpRescalingError("exponential rescaling source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_sum_linear_bound.py":"3beb3be7e6e7c4de8a82c0d600f947a5df3259dccdf36603d12af56f2fdf7c92",
        "scripts/sqrt2_power_series_linear_combination.py":"068c70dd150d2057d95d62bd10aba40b9df7d00aeadfd1c8eec7ce97dd0ffa4a",
        "scripts/sqrt2_power_weighted_series_trace.py":"34b97b7cc1a0391e74b01db46847dd78260e751b47312acdd64fea5281958bbc",
        "scripts/sqrt2_power_sum_linearity.py":"5a9131119953036d5bb1c7cb2b08e26bcc4fa63fd31a8c0cbc77409f17358bc0",
        "scripts/sqrt2_power_euler_product.py":"c26512518de941c9f8c54bfe682732d601158748f25955166b3ea6d8290afa10",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_rescaling.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRescalingError("rescaling source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _entry(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        i,a,b,c=t.terms(("i","a","b","c"))
        eq=apply(specialize(t,"graph",i,a,a,b),t.hyp("bound"),t.hyp("input"),t.hyp("input"),t.hyp("output"))
        return _chain(EqSym(specialize(t,"one_mul",b)),eq,
            CongAdd(EqRefl(Mul(c,a)),specialize(t,"zero_mul",a)),instantiate(Axiom("PA3"),Mul(c,a)))
    return introduce(s,("c",)+A+U+("L","i","a","b"),("graph","bound","input","output"),finish)


def _recurrence(s):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ
    fixed=("d","x","f","c","N")+A+U
    def chosen(t):
        d,x,f,c,N,j,a,b,u,v=t.terms(("d","x","f","c","N","j","a","b","u","v"));sj=Succ(j)
        old_in=apply(specialize(t,"le_succ",sj,N),t.hyp("bound"))
        new_in=apply(specialize(t,"succ_le_succ",sj,N),t.hyp("bound"))
        old=apply(specialize(t,"entry",c,*t.terms(A+U),Succ(N),j,u,a),t.hyp("graph"),old_in,t.hyp("source_old"),t.hyp("output_old"))
        new=apply(specialize(t,"entry",c,*t.terms(A+U),Succ(N),sj,v,b),t.hyp("graph"),new_in,t.hyp("source_new"),t.hyp("output_new"))
        rec=apply(specialize(t,"source_recurrence",j,u,v),t.hyp("bound"),t.hyp("source_old"),t.hyp("source_new"))
        outer=Mul(sj,Mul(d,f));fc=Mul(f,c);fx=Mul(f,x)
        return _chain(CongMul(EqRefl(outer),new),
            _multiplicative_equal(t,Mul(outer,Mul(c,v)),Mul(fc,Mul(Mul(sj,d),v))),
            CongMul(EqRefl(fc),rec),_multiplicative_equal(t,Mul(fc,Mul(x,u)),Mul(fx,Mul(c,u))),
            CongMul(EqRefl(fx),EqSym(old)))
    def row(t):
        return eliminate(t,specialize(t,"beta_exists",*t.terms(A),t.term("j")),("u",),"source_old",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(A),Succ(u.term("j"))),("v",),"source_new",chosen))
    return introduce(s,fixed,("source_recurrence","graph"),lambda t:
        introduce(t,("j","a","b"),("bound","output_old","output_new"),row))


def _head(s,registry):
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        c,N,a0,h=t.terms(("c","N","a0","h"))
        bound=apply(specialize(t,"succ_le_succ",Zero(),N),specialize(t,"zero_le",N))
        eq=apply(specialize(t,"entry",c,*t.terms(A+U),Succ(N),Zero(),a0,h),t.hyp("graph"),bound,t.hyp("head"),t.hyp("decoded_head"))
        return _subst(t,registry,"BetaAt(ub,uc,0,slot)",eq,t.hyp("decoded_head"))
    return introduce(s,("c",)+A+U+("N","a0"),("graph","head"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(U),Zero()),("h",),"decoded_head",chosen))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def chosen(t):
        c,N,a0,z,out=t.terms(("c","N","a0","s","t"))
        linear=apply(specialize(t,"linearity",c,Zero(),Succ(Zero()),*t.terms(A+A+U),Succ(N),z,z,out),
            t.hyp("sum"),t.hyp("sum"),t.hyp("scaled_sum"),t.hyp("graph"))
        exact=_chain(EqSym(specialize(t,"one_mul",out)),linear,CongAdd(EqRefl(Mul(c,z)),specialize(t,"zero_mul",z)),instantiate(Axiom("PA3"),Mul(c,z)))
        rec=apply(specialize(t,"recurrence",*t.terms(("d","x","f","c","N")+A+U)),t.hyp("source_recurrence"),t.hyp("graph"))
        head=apply(specialize(t,"head",c,*t.terms(A+U),N,a0),t.hyp("graph"),t.hyp("source_head"))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("graph"),rec,head,t.hyp("scaled_sum"),exact))
    return introduce(s,PARAMETERS,("source_recurrence","source_head","sum"),lambda t:
        eliminate(t,specialize(t,"combination_exists",t.term("c"),Zero(),*t.terms(A+A),Succ(t.term("N"))),U,"graph",lambda u:
            eliminate(u,specialize(u,"sum_exists",*u.terms(U),Succ(u.term("N"))),("t",),"scaled_sum",chosen)))


def prove_exp_rescaling(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV097",target=frozen_exp_rescaling_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"entry":_entry,"recurrence":_recurrence,"head":lambda s:_head(s,registry),"CV097":_root},
        pins=exp_rescaling_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
