"""CV090: exact finite atanh truncations have a controlled difference.

Construct one supplied table's prefix, affine tail and whole Horner values.
Actual powers and splitting identify their common scaling. Natural cross
bounds express monotonicity and an error <=3/3^M after nonzero rational
normalization; this theorem itself does not divide or assert an analytic limit.
"""
from hashlib import sha256

from sqrt2_power_ternary_prefix_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,ternary_prefix_bound_source_pins,
    NAMED_SOURCE as BOUNDED_SOURCE,
)
from sqrt2_power_horner_splitting import NAMED_SOURCE as SPLIT_SOURCE,COMPOSITION_ARCHIVE
from sqrt2_power_horner_tail_majorant import SPLITTING_ARCHIVE
from sqrt2_power_composition_majorant import INNER_ARCHIVE
from sqrt2_power_atanh_majorant import HELPER_SOURCES as ATANH_HELPERS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-atanh-truncation-v1"
A,B=("ab","ac"),("bb","bc")
PARAMETERS=("d",)+A+("M","N")
OUTPUTS=B+("x","y","z","p","q","h")
SPLIT_OUTPUTS=B+("x","y","z","q")
PARTS=("NatAffineSlice(ab,ac,M,1,bb,bc,N)","NatHornerValue(ab,ac,3,M,x)",
    "NatHornerValue(bb,bc,3,N,y)","NatHornerValue(ab,ac,3,M+N,z)",
    "Pow(3,M,p)","Pow(3,N,q)","Pow(3,M+N,h)","h=p*q","z=q*x+y",
    "Le(y+d,d*q)","Le(h*x,p*z)","Le(p*z,h*x+d*h)")


def conjoin(parts):
    result=parts[-1]
    for part in reversed(parts[:-1]):
        result=part+" /\\ ("+result+")"
    return result


CONCLUSION="exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". NatAtanhPrefix(d,ab,ac,M+N) -> "+CONCLUSION
TARGET_SHA256="fe8e75a1b92914b876b3335a496085b7cea520d900aaedca8a40e6f31ac26fa6"
HELPER_SOURCES={
    "slice_bound":"forall d ab ac bb bc M N. NatBoundedPrefix(ab,ac,2*d,M+N) -> NatAffineSlice(ab,ac,M,1,bb,bc,N) -> NatBoundedPrefix(bb,bc,2*d,N)",
    "arithmetic":"forall d p q h x y z. h=p*q -> z=q*x+y -> Le(y+d,d*q) -> Le(h*x,p*z) /\\ Le(p*z,h*x+d*h)",
    "bounded":"forall "+" ".join(PARAMETERS)+". NatBoundedPrefix(ab,ac,2*d,M+N) -> "+CONCLUSION,
}
HELPER_TARGET_SHA256={
    "slice_bound":"3eb80d0f0bf0f75f5fb0ffb1c90a20a7b8441761f66ef65175f503e648172ffe",
    "arithmetic":"b73df43a8c51cd5940f2e4fd71e1eaeb791ad8f04fa63fd67d1c90d30cd87bab",
    "bounded":"443c84e819c2377f8a46a00effe3cb97447dcb05095c1be66fedd298a6686a3f",
}
BOUNDED_ARCHIVE=dict(case="CV089",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-ternary-prefix-bound-v1/generation-process.json.gz",
    bytes=18450,sha256="57881a27a45e2f8487099af2348532194f5a329061403a25741e7d28e1652cf9",
    raw_bytes=200469,raw_sha256="5c081341b60530b0ba38054c8c1561851e0322c7f6a35944044b7695fea0e62e",
    bundle_bytes=87358,bundle_sha256="24c5dab66abdf543bfa39db7e32f55de16c4e88cd4f17fc80bf203a809ddd6cc",
    nodes=40,root=39,target_ast_sha256="5065e02e01a4babe946abf7b6ad03affafc1b509d98b79ed7d5f71995498c926")
ARCHIVES=(BOUNDED_ARCHIVE,SPLITTING_ARCHIVE,INNER_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={
    "bounded_value":BOUNDED_SOURCE,"splitting":SPLIT_SOURCE,"prefix_bound":ATANH_HELPERS["prefix_bound"],
    "power_exists":"forall d n. exists p. Pow(d,n,p)",
    "power_add":"forall a e f s x y z. s=e+f -> Pow(a,e,x) -> Pow(a,f,y) -> Pow(a,s,z) -> z=x*y",
    "one_mul":"forall a. 1*a=a","add_comm":"forall a b. a+b=b+a",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "mul_comm":"forall a b. a*b=b*a","le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
}
ENDPOINT_OWNERS={name:"CV089" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(splitting="CV062",prefix_bound="CV066",power_exists="CV061",power_add="CV061",one_mul="CV061")
HELPER_DEPENDENCIES={
    "slice_bound":("one_mul","add_left_mono"),
    "arithmetic":("add_comm","mul_add","mul_assoc","mul_comm","le_trans","mul_left_mono","add_left_mono"),
    "bounded":("splitting","power_exists","power_add","slice_bound","bounded_value","arithmetic"),
    "CV090":("prefix_bound","bounded"),
}


class AtanhTruncationError(ValueError):
    """Changed actual shared prefix/tail or denominator-cleared difference."""


def frozen_atanh_truncation_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=5 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise AtanhTruncationError("CV090 exact supplied atanh truncation changed")
    return target


def source_contract():
    return dict(code="CV090",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,supplied_atanh_table_preserved=True,
        actual_prefix_tail_whole_values_slice_and_powers_constructed=True,
        actual_power_product_and_scaled_split_proved=True,
        tail_bound="y+d<=d*q",monotonicity="h*x<=p*z",difference_bound="p*z<=h*x+d*h",
        prefix_length="M",tail_length="N",whole_length="M+N",powers="p=3^M; q=3^N; h=3^(M+N)",
        zero_lengths_and_zero_denominator_allowed_for_natural_bounds=True,
        code_number_equality_claimed=False,rational_denominator_validity_claimed=False,
        analytic_limit_claim=False,analytic_logarithm_identity=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def atanh_truncation_source_pins():
    result=ternary_prefix_bound_source_pins()
    expected={"scripts/sqrt2_power_ternary_prefix_bound.py":"0825490caef0118bc79ee8d41efccd91d023d9f60305f8d97fd813c0311d6608",
        "scripts/sqrt2_power_horner_splitting.py":"17d330dc31b9e7c6aca718bbce4c4cbbeab881783cb42118b3e0a76c322fe27a",
        "scripts/sqrt2_power_atanh_majorant.py":"994b47e03f8b9021bef219df7f91270ad2d790f91d788be62d7839d9afdf419e",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_atanh_truncation.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise AtanhTruncationError("atanh truncation source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _slice_bound(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl
    from peano_lab.kernel.terms import Succ
    def entry(t):
        M,N,i,a=t.terms(("M","N","i","a"))
        bound=apply(specialize(t,"add_left_mono",Succ(i),N,M),t.hyp("bound"))
        bound=_subst(t,registry,"Le(slot,M+N)",instantiate(Axiom("PA4"),M,i),bound)
        actual=apply(specialize(t,"slice",i,a),t.hyp("bound"),t.hyp("entry"))
        actual=_subst(t,registry,"BetaAt(ab,ac,slot,a)",CongAdd(EqRefl(M),specialize(t,"one_mul",i)),actual)
        from peano_lab.kernel.terms import Add
        return apply(specialize(t,"coefficients",Add(M,i),a),bound,actual)
    return introduce(s,("d",)+A+B+("M","N"),("coefficients","slice"),lambda t:
        introduce(t,("i","a"),("bound","entry"),entry))


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        d,p,q,h,x,y,z=t.terms(("d","p","q","h","x","y","z"))
        hx,py,pz=Mul(h,x),Mul(p,y),Mul(p,z)
        term=_chain(EqSym(specialize(t,"mul_assoc",p,q,x)),CongMul(EqSym(t.hyp("product")),EqRefl(x)))
        balance=_chain(CongMul(EqRefl(p),t.hyp("split")),specialize(t,"mul_add",p,Mul(q,x),y),CongAdd(term,EqRefl(py)))
        lower=witness((py,),_chain(specialize(t,"add_comm",py,hx),EqSym(balance)))
        small=witness((d,),specialize(t,"add_comm",d,y))
        small=apply(specialize(t,"le_trans",y,Add(y,d),Mul(d,q)),small,t.hyp("tail_bound"))
        scaled=apply(specialize(t,"mul_left_mono",y,Mul(d,q),p),small)
        aligned=_chain(_multiplicative_equal(t,Mul(p,Mul(d,q)),Mul(d,Mul(p,q))),CongMul(EqRefl(d),EqSym(t.hyp("product"))))
        scaled=_subst(t,registry,"Le(p*y,slot)",aligned,scaled)
        upper=apply(specialize(t,"add_left_mono",py,Mul(d,h),hx),scaled)
        upper=_subst(t,registry,"Le(slot,h*x+d*h)",EqSym(balance),upper)
        return conjunction(lower,upper)
    return introduce(s,("d","p","q","h","x","y","z"),("product","split","tail_bound"),finish)


def _bounded(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl
    from peano_lab.kernel.terms import Add,Succ,Zero
    three=Succ(Succ(Succ(Zero())))
    def chosen(t):
        d,M,N=t.terms(("d","M","N"));parts=t.hyp("split_data")
        bounded=apply(specialize(t,"slice_bound",d,*t.terms(A+B),M,N),t.hyp("coefficients"),field(parts,0,6))
        tail=apply(specialize(t,"bounded_value",*t.terms(B),d,N,*t.terms(("y","q"))),bounded,field(parts,2,6),field(parts,4,6))
        product=apply(specialize(t,"power_add",three,M,N,Add(M,N),*t.terms(("p","q","h"))),
            EqRefl(Add(M,N)),t.hyp("prefix_power"),field(parts,4,6),t.hyp("whole_power"))
        bounds=apply(specialize(t,"arithmetic",*t.terms(("d","p","q","h","x","y","z"))),product,field(parts,5,6),tail)
        return witness(t.terms(OUTPUTS),conjunction(*(field(parts,i,6) for i in range(4)),
            t.hyp("prefix_power"),field(parts,4,6),t.hyp("whole_power"),product,field(parts,5,6),tail,
            AndElimL(bounds),AndElimR(bounds)))
    return introduce(s,PARAMETERS,("coefficients",),lambda t:
        eliminate(t,specialize(t,"splitting",*t.terms(A),three,*t.terms(("M","N"))),SPLIT_OUTPUTS,"split_data",lambda u:
            eliminate(u,specialize(u,"power_exists",three,u.term("M")),("p",),"prefix_power",lambda v:
                eliminate(v,specialize(v,"power_exists",three,Add(*v.terms(("M","N")))),("h",),"whole_power",chosen))))


def _root(s):
    from peano_lab.kernel.terms import Add
    def finish(t):
        bound=apply(specialize(t,"prefix_bound",*t.terms(("d",)+A),Add(*t.terms(("M","N")))),t.hyp("prefix"))
        return apply(specialize(t,"bounded",*t.terms(PARAMETERS)),bound)
    return introduce(s,PARAMETERS,("prefix",),finish)


def prove_atanh_truncation(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV090",target=frozen_atanh_truncation_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"slice_bound":lambda s:_slice_bound(s,registry),"arithmetic":lambda s:_arithmetic(s,registry),"bounded":_bounded,"CV090":_root},
        pins=atanh_truncation_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
