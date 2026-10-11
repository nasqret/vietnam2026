"""AP012: a uniform dyadic error for actual samples at strictly finer precision.

Construct the auxiliary cutoff power internally. Its domination properties
turn AP009's two error denominators into the actual coarse dyadic denominator.
Both complete supplied graphs and positive coefficient scales are preserved.
"""
from hashlib import sha256

from sqrt2_power_exp_sample_modulus import (
    ROOT,Scope,introduce,conjunction,apply,specialize,field,canonical,json_hash,_and,
    definition_registry,PARAMETERS as MODULUS_PARAMETERS,COARSE_GRAPH,FINE_GRAPH,
    NAMED_SOURCE as MODULUS_SOURCE,exp_sample_modulus_source_pins,
)
from sqrt2_power_approximation_power_bounds import (
    NAMED_SOURCE as POWERS_SOURCE,approximation_power_bounds_source_pins,BOUND_ARCHIVE,
)
from sqrt2_power_positive_power_comparison import HELPER_SOURCES as POWER_HELPERS
from sqrt2_power_quadratic_trace_exists import eliminate,witness
from sqrt2_power_exp_two_sided_continuity import _left,_right,_chain,_multiplicative_equal
from sqrt2_power_argument_modulus import _sum_order
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-sample-uniform-error-v1"
PARAMETERS=MODULUS_PARAMETERS[:-1]
COEFFICIENT="((9*3)+2)"
PARTS=("~d=0","~w0=0","~v0=0",f"Le(d*(w0*o),d*(v0*y)+{COEFFICIENT}*(w0*v0))",
    f"Le(d*(v0*y),d*(w0*o)+{COEFFICIENT}*(w0*v0))")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~D=0 -> ~E=0 -> "+COARSE_GRAPH+" -> "+FINE_GRAPH+" -> "+_and(PARTS)
TARGET_SHA256="309286b62c9ba3f6357861cfacebc829369cbcc7919b6c039df4852a2f7bfb99"
HELPER_SOURCES={
    "arithmetic":"forall d p r A B x y h. ~p=0 -> ~r=0 -> Le(d,p) -> Le(d,r) -> Le((p*r)*x,(p*r)*y+(A*r+B*p)*h) -> Le(d*x,d*y+(A+B)*h)",
    "reverse":"forall d x y h. Le(d*y,d*x+9*h) -> Le(d*y,d*x+"+COEFFICIENT+"*h)",
}
HELPER_TARGET_SHA256={"arithmetic":"01344d2d310e3d4277cb9df9d39dd97fe89bef582d051c73e1041bac6e3c1399",
    "reverse":"bee1d03144b3d14efba79102c5f67bdf64e926976f5fdee599b4bcae0267df9d"}
MODULUS_ARCHIVE=dict(case="AP009",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-sample-modulus-v1/generation-process.json.gz",
    bytes=98372,sha256="8ab2a3a784757b830c54179e1035e202cf8f50fddedef4f8072d77ef26abac64",
    raw_bytes=2090863,raw_sha256="4d6b344bd4f988e7849a99ca61d5d23aa78bc2be74b468ef22885d6558177896",
    bundle_bytes=1257796,bundle_sha256="b30e8f3596e922ae6f3391b2bab3b75574459487def0a796d30dba6d283933df",
    nodes=273,root=272,target_ast_sha256="073e1e33119841ca820f40504b4be88839cec838afc45b6028bda6807fa464dd")
POWERS_ARCHIVE=dict(case="AP011",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-approximation-power-bounds-v1/generation-process.json.gz",
    bytes=45384,sha256="f0341d659f64918495aab1e1c8d2f77627d280159048359a5e75d9702c4a124f",
    raw_bytes=512620,raw_sha256="76f79393925741de85fc92e43beac29edcfd05e51fb376f1168dc4f9645d69e6",
    bundle_bytes=270071,bundle_sha256="59a7b1470dfeb2ff50255f79fa96efc0cb349ddcb36ba6ffd8fcc0643ee68c02",
    nodes=128,root=127,target_ast_sha256="a41d4293a571408ac987bb69b06a49ec1afd6527e75e6d2404265714b00fb69e")
ARCHIVES=(MODULUS_ARCHIVE,POWERS_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "modulus":MODULUS_SOURCE,"powers":POWERS_SOURCE,"positive_factor":POWER_HELPERS["positive_factor"],
    "power_exists":"forall a k. exists p. Pow(a,k,p)",
    "mul_le_cancel":"forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)",
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0","succ_ne_zero":"forall a. ~S a=0",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)","mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)","add_right_mono":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c","add_mul":"forall a b c. (a+b)*c=a*c+b*c",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "add_comm":"forall a b. a+b=b+a",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(modulus="AP009",powers="AP011",positive_factor="AP011",power_exists="AP011")
HELPER_DEPENDENCIES={
    "arithmetic":("mul_left_mono","mul_right_mono","add_left_mono","add_right_mono","le_trans","mul_add","add_mul","mul_assoc","mul_comm","mul_ne_zero","mul_le_cancel"),
    "reverse":("positive_factor","succ_ne_zero","add_comm","le_trans","mul_right_mono","add_left_mono"),
    "AP012":("modulus","powers","power_exists","arithmetic","reverse"),
}


class ExpSampleUniformError(ValueError):
    """Changed complete actual samples, positive scales or uniform dyadic bound."""


def frozen_exp_sample_uniform_error_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=32 or len(premises)!=4 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSampleUniformError("AP012 exact uniform dyadic sample-error target changed")
    return target


def source_contract():
    return dict(code="AP012",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,both_supplied_complete_sample_graphs_preserved=True,positive_coefficient_scales_required=True,
        strict_precision_increment="S l",actual_cutoff_power_constructed_internally=True,
        uniform_two_sided_error="((9*3)+2)/d",dyadic_denominator="d=2^k",only_proved_positive_factors_cancelled=True,
        all_output_denominators_proved_nonzero=True,zero_precision_allowed=True,same_precision_requires_separate_AP005=True,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_sample_uniform_error_source_pins():
    result=exp_sample_modulus_source_pins()
    for name,pin in approximation_power_bounds_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpSampleUniformError("uniform sample-error source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_sample_modulus.py":"1d78e9661a21956e9c483f98d61012a8e44831be7d597c54bf55bb5f7df509b8",
        "scripts/sqrt2_power_approximation_power_bounds.py":"ef4401c17fb3c3ddf0ef47aaea1ea5396a5c658ed6eb4e88d4349256cf5f9856",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_sample_uniform_error.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSampleUniformError("uniform sample-error source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        d,p,r,A,B,x,y,h=t.terms(("d","p","r","A","B","x","y","h"))
        pr=Mul(p,r);ar=Mul(A,r);bp=Mul(B,p);coef=Add(ar,bp);combined=Add(A,B)
        dx,dy=Mul(d,x),Mul(d,y);lhs=Mul(pr,dx);base=Mul(pr,dy);newerr=Mul(combined,h)
        oldlhs,oldbase=Mul(pr,x),Mul(pr,y);olderr=Mul(coef,h)
        upper=apply(specialize(t,"mul_left_mono",oldlhs,Add(oldbase,olderr),d),t.hyp("bound"))
        upper=_left(t,registry,upper,Mul(d,Add(oldbase,olderr)),_multiplicative_equal(t,Mul(d,oldlhs),lhs))
        dar,dbp=Mul(d,ar),Mul(d,bp);oldsum=Add(dar,dbp)
        error=_chain(_multiplicative_equal(t,Mul(d,olderr),Mul(Mul(d,coef),h)),CongMul(specialize(t,"mul_add",d,ar,bp),EqRefl(h)))
        upper=_right(t,registry,upper,lhs,_chain(specialize(t,"mul_add",d,oldbase,olderr),CongAdd(_multiplicative_equal(t,Mul(d,oldbase),base),error)))
        # Each actual error denominator dominates the same dyadic denominator.
        first=apply(specialize(t,"mul_right_mono",d,p,ar),t.hyp("d_le_p"))
        first=_right(t,registry,first,dar,_multiplicative_equal(t,Mul(p,ar),Mul(A,pr)))
        second=apply(specialize(t,"mul_right_mono",d,r,bp),t.hyp("d_le_r"))
        second=_right(t,registry,second,dbp,_multiplicative_equal(t,Mul(r,bp),Mul(B,pr)))
        errors=_sum_order(t,dar,Mul(A,pr),dbp,Mul(B,pr),first,second)
        errors=_right(t,registry,errors,oldsum,EqSym(specialize(t,"add_mul",A,B,pr)))
        errors=apply(specialize(t,"mul_right_mono",oldsum,Mul(combined,pr),h),errors)
        errors=_right(t,registry,errors,Mul(oldsum,h),_multiplicative_equal(t,Mul(Mul(combined,pr),h),Mul(pr,newerr)))
        errors=apply(specialize(t,"add_left_mono",Mul(oldsum,h),Mul(pr,newerr),base),errors)
        upper=apply(specialize(t,"le_trans",lhs,Add(base,Mul(oldsum,h)),Add(base,Mul(pr,newerr))),upper,errors)
        upper=_right(t,registry,upper,lhs,EqSym(specialize(t,"mul_add",pr,dy,newerr)))
        nonzero=apply(specialize(t,"mul_ne_zero",p,r),t.hyp("p_nonzero"),t.hyp("r_nonzero"))
        return apply(specialize(t,"mul_le_cancel",pr,dx,Add(dy,newerr)),nonzero,upper)
    return introduce(s,("d","p","r","A","B","x","y","h"),("p_nonzero","r_nonzero","d_le_p","d_le_r","bound"),finish)


def _reverse(s):
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,three,nine=(parse_term(n) for n in ("2","3","9"))
    product=Mul(nine,three);coef=Add(product,two)
    def finish(t):
        d,x,y,h=t.terms(("d","x","y","h"));dx,dy=Mul(d,x),Mul(d,y)
        first=apply(specialize(t,"positive_factor",nine,three),specialize(t,"succ_ne_zero",two))
        coefficient=apply(specialize(t,"le_trans",nine,product,coef),first,witness((two,),specialize(t,"add_comm",two,product)))
        error=apply(specialize(t,"mul_right_mono",nine,coef,h),coefficient)
        error=apply(specialize(t,"add_left_mono",Mul(nine,h),Mul(coef,h),dx),error)
        return apply(specialize(t,"le_trans",dy,Add(dx,Mul(nine,h)),Add(dx,Mul(coef,h))),t.hyp("bound"),error)
    return introduce(s,("d","x","y","h"),("bound",),finish)


def _root(s):
    from peano_lab.kernel.proofs import AndElimL
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,nine,three=(parse_term(n) for n in ("2","9","3"))
    def chosen(t):
        k,d,p,r,w0,v0,y,o=t.terms(("k","d","p","r","w0","v0","y","o"))
        result=apply(specialize(t,"modulus",*t.terms(MODULUS_PARAMETERS)),
            t.hyp("D_nonzero"),t.hyp("E_nonzero"),t.hyp("coarse"),t.hyp("fine"),t.hyp("power"))
        argument=field(t.hyp("coarse"),0,9)
        powers=apply(specialize(t,"powers",k,d,p,r),AndElimL(field(argument,0,4)),field(argument,3,4),t.hyp("power"))
        x,z,h=Mul(w0,o),Mul(v0,y),Mul(w0,v0)
        forward=apply(specialize(t,"arithmetic",d,p,r,Mul(nine,three),two,x,z,h),
            field(powers,1,5),field(powers,2,5),field(powers,3,5),field(powers,4,5),field(result,5,7))
        backward=apply(specialize(t,"reverse",d,x,z,h),field(result,6,7))
        return conjunction(field(result,0,7),field(result,3,7),field(result,4,7),forward,backward)
    return introduce(s,PARAMETERS,("D_nonzero","E_nonzero","coarse","fine"),lambda t:
        eliminate(t,specialize(t,"power_exists",two,Add(t.term("k"),two)),("r",),"power",chosen))


def prove_exp_sample_uniform_error(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP012",target=frozen_exp_sample_uniform_error_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"arithmetic":lambda s:_arithmetic(s,registry),"reverse":_reverse,"AP012":_root},
        pins=exp_sample_uniform_error_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
