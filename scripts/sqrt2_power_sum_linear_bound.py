"""CV095: pointwise weighted order transports to three supplied finite sums.

The sole new conservative alias specifies decoded-entry bounds, not a sum
inequality. One ordinary induction proves the sum conclusion for arbitrary
encodings, empty prefixes and zero weights. No accuracy assertion is defined.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_exp_term_difference import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as base_registry,exp_term_difference_source_pins,
    BOUND_ARCHIVE,
)
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE
from sqrt2_power_quadratic_height import _chain,_additive_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-sum-linear-bound-v1"
A,B,C=("ab","ac"),("bb","bc"),("cb","cc")
FIXED=("alpha","beta","gamma")+A+B+C+("N",)
PARAMETERS=FIXED+("u","v","w")
DEFINITIONS=(("ND0445","NatLinearBound",FIXED,
    "forall i a b c. Lt(i,N) -> BetaAt(ab,ac,i,a) -> BetaAt(bb,bc,i,b) -> BetaAt(cb,cc,i,c) -> Le(gamma*c,alpha*a+beta*b)",
    ("Lt","BetaAt","Le"),"e8e9af5e154cab1910f48e44f6e1358487f6ddf92dbd30bcef6acc4ba69d5ad3"),)
GRAPH="NatLinearBound("+",".join(FIXED)+")"
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+GRAPH+" -> Sum(ab,ac,N,u) -> Sum(bb,bc,N,v) -> Sum(cb,cc,N,w) -> Le(gamma*w,alpha*u+beta*v)"
TARGET_SHA256="5c476b035cc43d4fd6b3e03efbe6c35fb50f132bb036051a3e1bb5e3c1ad422a"
ROWS="forall k u v w. Le(k,N) -> Sum(ab,ac,k,u) -> Sum(bb,bc,k,v) -> Sum(cb,cc,k,w) -> Le(gamma*w,alpha*u+beta*v)"
HELPER_SOURCES={
    "combine":"forall alpha beta gamma a b c u v w. Le(gamma*c,alpha*a+beta*b) -> Le(gamma*w,alpha*u+beta*v) -> Le(gamma*(c+w),alpha*(a+u)+beta*(b+v))",
    "all_prefixes":"forall "+" ".join(FIXED)+". "+GRAPH+" -> "+ROWS,
}
HELPER_TARGET_SHA256={"combine":"23304e31a0d5bda706c79872d9ee7550bcd014852b1dd494994312fc7cbaaa95",
    "all_prefixes":"29f67e380ca153d76a2fa84a862222cc196a3de2bf5d705a9e95f479577a2e76"}
ARCHIVES=(BOUND_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)","add_right_mono":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)","le_refl":"forall a. Le(a,a)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)","mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)","add_comm":"forall a b. a+b=b+a",
    "sum_zero":"forall b c n. Sum(b,c,0,n) -> n=0",
    "sum_decompose":"forall b c L n. Sum(b,c,S L,n) -> exists a r. BetaAt(b,c,L,a) /\\ (Sum(b,c,L,r) /\\ n=r+a)",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(sum_zero="CV061",sum_decompose="CV061")
HELPER_DEPENDENCIES={
    "combine":("add_left_mono","add_right_mono","le_trans","mul_add","add_assoc","add_comm"),
    "all_prefixes":("sum_zero","sum_decompose","combine","le_refl","le_succ","le_trans"),
    "CV095":("all_prefixes","le_refl"),
}


class SumLinearBoundError(ValueError):
    """Changed pointwise conservative order, supplied sums or exact target."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    result=dict(base_registry())
    parent=json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids={d["id"] for d in parent}|{d.stable_id for d in result.values()}
    names={d["name"] for d in parent}|set(result)
    for identifier,name,params,source,deps,digest in DEFINITIONS:
        if identifier in ids or name in names or not set(deps)<=result.keys():
            raise SumLinearBoundError("pointwise order collision or forward dependency")
        formula=parse_named(source,params,result)
        if json_hash(encode_formula(formula))!=digest:
            raise SumLinearBoundError("pointwise weighted order expansion changed")
        text=pretty_formula(formula,list(params))
        d=_definition(stable_id=identifier,name=name,parameters=params,template_source=text,
            summary="Separate pointwise weighted bound between decoded prefixes; no sum or analytic assertion.",
            category="irrationality_formal_series",conceptual_dependencies=deps)
        if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula:
            raise SumLinearBoundError("pointwise order failed conservative roundtrip")
        result[name]=d;ids.add(identifier);names.add(name)
    return MappingProxyType(result)


def frozen_sum_linear_bound_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    # Internal callers already hold the freshly checked immutable registry.
    # The exact expanded target hash is checked in either entry path.
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=13 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SumLinearBoundError("CV095 exact supplied weighted sum bound changed")
    return target


def source_contract():
    return dict(code="CV095",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,three_supplied_sum_values_preserved=True,explicit_pointwise_bound_required=True,
        independent_input_and_sum_history_codes_allowed=True,empty_prefix_and_zero_weights_allowed=True,
        sum_bound="gamma*w<=alpha*u+beta*v",definition_contains_sum_or_accuracy_claim=False,
        new_definition_ids=["ND0445"],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def sum_linear_bound_source_pins():
    result=exp_term_difference_source_pins()
    expected={"scripts/sqrt2_power_exp_term_difference.py":"d095d11d40de1b22ee992f2e47b4545725bcf6e63b159edce96047f78c48084b",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_sum_linear_bound.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SumLinearBoundError("weighted-sum bound source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _combine(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        alpha,beta,gamma,a,b,c,u,v,w=t.terms(("alpha","beta","gamma","a","b","c","u","v","w"))
        gc,gw=Mul(gamma,c),Mul(gamma,w)
        aa,bb,au,bv=Mul(alpha,a),Mul(beta,b),Mul(alpha,u),Mul(beta,v)
        first=apply(specialize(t,"add_right_mono",gc,Add(aa,bb),gw),t.hyp("first"))
        second=apply(specialize(t,"add_left_mono",gw,Add(au,bv),Add(aa,bb)),t.hyp("second"))
        both=apply(specialize(t,"le_trans",Add(gc,gw),Add(Add(aa,bb),gw),Add(Add(aa,bb),Add(au,bv))),first,second)
        both=_subst(t,registry,"Le(slot,(alpha*a+beta*b)+(alpha*u+beta*v))",EqSym(specialize(t,"mul_add",gamma,c,w)),both)
        right=_chain(_additive_equal(t,Add(Add(aa,bb),Add(au,bv)),Add(Add(aa,au),Add(bb,bv))),
            CongAdd(EqSym(specialize(t,"mul_add",alpha,a,u)),EqSym(specialize(t,"mul_add",beta,b,v))))
        return _subst(t,registry,"Le(gamma*(c+w),slot)",right,both)
    return introduce(s,("alpha","beta","gamma","a","b","c","u","v","w"),("first","second"),finish)


def _all_prefixes(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def base(t):
        alpha,beta,gamma,u,v,w=t.terms(("alpha","beta","gamma","u","v","w"))
        equations=[apply(specialize(t,"sum_zero",*t.terms(codes),t.term(value)),t.hyp(label))
            for codes,value,label in ((A,"u","sum_a"),(B,"v","sum_b"),(C,"w","sum_c"))]
        left=_chain(CongMul(EqRefl(gamma),equations[2]),instantiate(Axiom("PA5"),gamma))
        right=_chain(CongAdd(CongMul(EqRefl(alpha),equations[0]),CongMul(EqRefl(beta),equations[1])),
            CongAdd(instantiate(Axiom("PA5"),alpha),instantiate(Axiom("PA5"),beta)),instantiate(Axiom("PA3"),Zero()))
        return _subst(t,registry,"Le(gamma*w,slot)",_chain(left,EqSym(right)),specialize(t,"le_refl",Mul(gamma,w)))
    def successor(t):
        def chosen(u):
            k,N=u.terms(("k","N"));ad,bd,cd=(u.hyp(label) for label in ("data_a","data_b","data_c"))
            earlier=apply(specialize(u,"le_trans",k,Succ(k),N),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            old=apply(specialize(u,"IH",*u.terms(("ru","rv","rw"))),earlier,field(ad,1,3),field(bd,1,3),field(cd,1,3))
            last=apply(specialize(u,"graph",*u.terms(("k","a","b","c"))),u.hyp("bound"),field(ad,0,3),field(bd,0,3),field(cd,0,3))
            total=apply(specialize(u,"combine",*u.terms(("alpha","beta","gamma","ru","rv","rw","a","b","c"))),old,last)
            total=_subst(u,registry,"Le(gamma*slot,alpha*(ru+a)+beta*(rv+b))",EqSym(field(cd,2,3)),total)
            total=_subst(u,registry,"Le(gamma*w,alpha*slot+beta*(rv+b))",EqSym(field(ad,2,3)),total)
            return _subst(u,registry,"Le(gamma*w,alpha*u+beta*slot)",EqSym(field(bd,2,3)),total)
        def decode(u,remaining):
            if not remaining:
                return chosen(u)
            codes,value,label,outputs=remaining[0]
            proof=apply(specialize(u,"sum_decompose",*u.terms(codes+("k",value))),u.hyp(label))
            return eliminate(u,proof,outputs,"data_"+label[-1],lambda v:decode(v,remaining[1:]))
        return decode(t,((A,"u","sum_a",("a","ru")),(B,"v","sum_b",("b","rv")),(C,"w","sum_c",("c","rw"))))
    motive=target
    for _ in FIXED:
        motive=motive.body
    motive=motive.right.body
    variables,hyps=("u","v","w"),("bound","sum_a","sum_b","sum_c")
    return introduce(s,FIXED,("graph",),lambda t:Ind(motive,introduce(t,variables,hyps,base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,variables,hyps,successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    def finish(t):
        all_values=apply(specialize(t,"all_prefixes",*t.terms(FIXED)),t.hyp("graph"))
        return apply(instantiate(all_values,*t.terms(("N","u","v","w"))),specialize(t,"le_refl",t.term("N")),
            *(t.hyp(label) for label in ("sum_a","sum_b","sum_c")))
    return introduce(s,PARAMETERS,("graph","sum_a","sum_b","sum_c"),finish)


def prove_sum_linear_bound(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV095",target=frozen_sum_linear_bound_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"combine":lambda s:_combine(s,registry),"all_prefixes":lambda s:_all_prefixes(s,parse_named(HELPER_SOURCES["all_prefixes"],registry=registry),registry),"CV095":_root},
        pins=sum_linear_bound_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
