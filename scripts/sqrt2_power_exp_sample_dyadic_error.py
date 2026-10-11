"""AP015: the eight-bit shift gives finite sample error at most 2^-n.

Construct actual powers 2^n and 2^8, use the actual coarse dyadic subgraph,
and cancel only the proved positive shift power. Both full supplied graphs
and positive coefficient scales remain premises. This is a finite Cauchy
bound, not a canonical PR algorithm or identification with a real constant.
"""
from hashlib import sha256

from sqrt2_power_exp_sample_all_precision import (
    ROOT,Scope,introduce,conjunction,apply,specialize,field,canonical,json_hash,_and,
    definition_registry,COEFFICIENT,BOUND_ARCHIVE,PARAMETERS as ALL_PARAMETERS,
    NAMED_SOURCE as ALL_SOURCE,exp_sample_all_precision_source_pins,
)
from sqrt2_power_exp_sample_modulus import COARSE_PARAMETERS,FINE_OUTPUTS
from sqrt2_power_fixed_precision_threshold import (
    NAMED_SOURCE as THRESHOLD_SOURCE,fixed_precision_threshold_source_pins,
)
from sqrt2_power_quadratic_trace_exists import eliminate,witness
from sqrt2_power_exp_two_sided_continuity import _left,_right,_chain,_multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-sample-dyadic-error-v1"
PARAMETERS=("n",)+ALL_PARAMETERS[1:]
COARSE_GRAPH="NatSqrt2ExpSample(n+8,"+",".join(COARSE_PARAMETERS[1:])+")"
FINE_GRAPH="NatSqrt2ExpSample((n+8)+l,"+",".join(FINE_OUTPUTS)+")"
PARTS=("Pow(2,n,r)","~r=0","~w0=0","~v0=0",
    "Le(r*(w0*o),r*(v0*y)+(w0*v0))","Le(r*(v0*y),r*(w0*o)+(w0*v0))")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~D=0 -> ~E=0 -> "+COARSE_GRAPH+" -> "+FINE_GRAPH+" -> exists r. "+_and(PARTS)
TARGET_SHA256="98633f6b0d2144188f824e0f5f1f367d8113fe1999e66199a3b54eb28f615703"
HELPER_SOURCES={"arithmetic":"forall d r v C x y h. d=r*v -> ~v=0 -> Le(C,v) -> Le(d*x,d*y+C*h) -> Le(r*x,r*y+h)"}
HELPER_TARGET_SHA256={"arithmetic":"a7c53737271485b94934c473aece0dc46b01bc06fb94722136bb502ba69f7eb8"}
ALL_ARCHIVE=dict(case="AP013",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-sample-all-precision-v1/generation-process.json.gz",
    bytes=111660,sha256="fb8b5da6295217b821a250c06364af616d990d102bc5bf1604a5e60498928a62",
    raw_bytes=2565294,raw_sha256="a06bf6d4e6d8abceaf24b66b8a045630ed80d939741204af41606b92b3aa2272",
    bundle_bytes=1549613,bundle_sha256="e02a1654a4fa32bfa0c52da1c745d22083dc69a1eaf362ee3950df341d422a73",
    nodes=297,root=296,target_ast_sha256="2ea71d464e47c52e625a986dcb55ac5c92ff24daf2fd7b95c71d36d58aad8634")
THRESHOLD_ARCHIVE=dict(case="AP014",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-precision-threshold-v2/generation-process.json.gz",
    bytes=46906,sha256="c601cc676804dbad912ee44b7370ef28629ccf0ca344e835ec2c6f4bc79f2ead",
    raw_bytes=562621,raw_sha256="f4157734f2b5a75434979a54e3a5e083495b1ce0c5e5c0b86dafc460b28f2b68",
    bundle_bytes=300966,bundle_sha256="79b74784f51a096ec9525ac54fbe9fce921049df06b0579fef8d1a44d2695eed",
    nodes=130,root=129,target_ast_sha256="2ec3a5c39030d975d8ddf79a41d7793afd4f5fdfd25bcd49657f7335af0fba3c")
ARCHIVES=(ALL_ARCHIVE,THRESHOLD_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={"all_precision":ALL_SOURCE,"threshold":THRESHOLD_SOURCE,
    "power_exists":"forall a k. exists p. Pow(a,k,p)",
    "power_add":"forall a e f s x y z. s=e+f -> Pow(a,e,x) -> Pow(a,f,y) -> Pow(a,s,z) -> z=x*y",
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0",
    "mul_le_cancel":"forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a"}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(all_precision="AP013",threshold="AP014",power_exists="AP014",power_add="AP014",power_nonzero="AP014")
HELPER_DEPENDENCIES={"arithmetic":("mul_assoc","mul_comm","mul_add","mul_right_mono","add_left_mono","le_trans","mul_le_cancel"),
    "AP015":("arithmetic","all_precision","threshold","power_exists","power_add","power_nonzero","succ_ne_zero")}


class ExpSampleDyadicError(ValueError):
    """Changed full supplied graphs, fixed shift, actual powers or finite bound."""


def frozen_exp_sample_dyadic_error_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=32 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSampleDyadicError("AP015 exact fixed-shift dyadic error target changed")
    return target


def source_contract():
    return dict(code="AP015",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,both_supplied_complete_sample_graphs_preserved=True,positive_coefficient_scales_required=True,
        all_precision_indices_and_increments_including_zero=True,coarse_precision="n+8",fine_precision="(n+8)+l",
        actual_dyadic_output_power_constructed=True,actual_shift_power_constructed=True,
        actual_coarse_power_factored=True,only_proved_positive_shift_power_cancelled=True,
        finite_two_sided_error="1/r where r=2^n",positive_output_denominators_proved=True,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_sample_dyadic_error_source_pins():
    result=exp_sample_all_precision_source_pins()
    for name,pin in fixed_precision_threshold_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpSampleDyadicError("shifted sample source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_exp_sample_all_precision.py":"303645a0fccd095204aea8117d4ef18e6e84df5eb2e7565b043a8e2e2c3a3945",
        "scripts/sqrt2_power_fixed_precision_threshold.py":"2135396cb60dc5e367407ad5a5328066d8e252e5ca58869adbac7d370080239f",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_sample_dyadic_error.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSampleDyadicError("shifted sample source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        d,r,v,C,x,y,h=t.terms(("d","r","v","C","x","y","h"))
        rx,ry=Mul(r,x),Mul(r,y);left,base=Mul(v,rx),Mul(v,ry);error=Mul(C,h)
        def normalized(value):
            return _chain(CongMul(t.hyp("factor"),EqRefl(value)),
                _multiplicative_equal(t,Mul(Mul(r,v),value),Mul(v,Mul(r,value))))
        upper=_left(t,registry,t.hyp("bound"),Add(Mul(d,y),error),normalized(x))
        upper=_right(t,registry,upper,left,CongAdd(normalized(y),EqRefl(error)))
        enlarged=apply(specialize(t,"mul_right_mono",C,v,h),t.hyp("threshold"))
        enlarged=apply(specialize(t,"add_left_mono",error,Mul(v,h),base),enlarged)
        upper=apply(specialize(t,"le_trans",left,Add(base,error),Add(base,Mul(v,h))),upper,enlarged)
        upper=_right(t,registry,upper,left,EqSym(specialize(t,"mul_add",v,ry,h)))
        return apply(specialize(t,"mul_le_cancel",v,rx,Add(ry,h)),t.hyp("nonzero"),upper)
    return introduce(s,("d","r","v","C","x","y","h"),("factor","nonzero","threshold","bound"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,eight,coefficient=(parse_term(source) for source in ("2","8",COEFFICIENT))
    def chosen(t):
        n,l,d,r,shift,w0,v0,y,o=t.terms(("n","l","d","r","shift","w0","v0","y","o"));precision=Add(n,eight)
        result=apply(specialize(t,"all_precision",precision,l,*t.terms(ALL_PARAMETERS[2:])),
            t.hyp("D_nonzero"),t.hyp("E_nonzero"),t.hyp("coarse"),t.hyp("fine"))
        threshold=apply(specialize(t,"threshold",shift),t.hyp("shift_power"))
        coarse_power=AndElimL(field(field(t.hyp("coarse"),0,9),0,4))
        factor=apply(specialize(t,"power_add",two,n,eight,precision,r,shift,d),EqRefl(precision),t.hyp("dyadic_power"),t.hyp("shift_power"),coarse_power)
        nonzero=apply(instantiate(apply(specialize(t,"power_nonzero",two),specialize(t,"succ_ne_zero",parse_term("1"))),n,r),t.hyp("dyadic_power"))
        x,z,h=Mul(w0,o),Mul(v0,y),Mul(w0,v0)
        forward=apply(specialize(t,"arithmetic",d,r,shift,coefficient,x,z,h),factor,AndElimL(threshold),AndElimR(threshold),field(result,3,5))
        backward=apply(specialize(t,"arithmetic",d,r,shift,coefficient,z,x,h),factor,AndElimL(threshold),AndElimR(threshold),field(result,4,5))
        return witness((r,),conjunction(t.hyp("dyadic_power"),nonzero,field(result,1,5),field(result,2,5),forward,backward))
    def dyadic(t):
        return eliminate(t,specialize(t,"power_exists",two,eight),("shift",),"shift_power",chosen)
    return introduce(s,PARAMETERS,("D_nonzero","E_nonzero","coarse","fine"),lambda t:
        eliminate(t,specialize(t,"power_exists",two,t.term("n")),("r",),"dyadic_power",dyadic))


def prove_exp_sample_dyadic_error(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP015",target=frozen_exp_sample_dyadic_error_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"arithmetic":lambda s:_arithmetic(s,registry),"AP015":_root},
        pins=exp_sample_dyadic_error_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
