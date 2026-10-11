"""CV093: finite rational truncation bounds across independent actual tables.

Preserve both supplied coefficient encodings, values and powers. Their scales
need not coincide. The short value is transported by CV092's cross identity,
not by equating unrelated code numbers. All denominators are proved nonzero.
"""
from hashlib import sha256

from sqrt2_power_atanh_rational_truncation import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,atanh_rational_truncation_source_pins,
    TRUNCATION_ARCHIVE,RATIONAL_TAIL_ARCHIVE,TRUNCATION_SOURCE,RATIONAL_HELPERS,
)
from sqrt2_power_atanh_scale_independence import (
    NAMED_SOURCE as SCALING_SOURCE,atanh_scale_independence_source_pins,
)
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE
from sqrt2_power_row_horner_values import HELPER_SOURCES as VALUE_HELPERS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-independent-atanh-truncation-v1"
A,B=("ab","ac"),("bb","bc")
PARAMETERS=("d","e")+A+B+("M","N","x","z","p","h")
PREMISES=("~d=0","~e=0","NatAtanhPrefix(d,ab,ac,M)","NatAtanhPrefix(e,bb,bc,M+N)",
    "NatHornerValue(ab,ac,3,M,x)","NatHornerValue(bb,bc,3,M+N,z)","Pow(3,M,p)","Pow(3,M+N,h)")
LOWER="IRatLe(3*x,0,d*p,3*z,0,e*h)"
UPPER="IRatLe(3*z,0,e*h,3*x+3*d,0,d*p)"
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> "+LOWER+" /\\ "+UPPER
TARGET_SHA256="c8bd73e82050b43d383204e7e5e1fc00bda755d88df07a5fb9b1c8f5700f3f6b"
HELPER_SOURCES={"cross_orders":"forall d e p h x y z. e*x=d*y -> Le(h*y,p*z) -> Le(p*z,h*y+e*h) -> Le((3*x)*(e*h),(3*z)*(d*p)) /\\ Le((3*z)*(d*p),(3*x+3*d)*(e*h))"}
HELPER_TARGET_SHA256={"cross_orders":"57602660de46cc6cda05310ffb86d1484d8cadb7a3f566375a8209cbe1424ec3"}
SCALING_ARCHIVE=dict(case="CV092",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-atanh-scale-independence-v1/generation-process.json.gz",
    bytes=19166,sha256="e583517861cfe9cffef9f55a6d80a84e95d9d41eac9d71667c4acafeedb25736",
    raw_bytes=179928,raw_sha256="66715a5b9b15bfd5aba2a19fece9bec06f7feef6c97daab45181c9f477855459",
    bundle_bytes=72999,bundle_sha256="88406acbf3430be4143d97c26d2e1cb0a3f09d1a7b014add87323a1e08587074",
    nodes=37,root=36,target_ast_sha256="5b80b161ea46bbe0cbcdef8789de98218d6c1dfc077ff0023320f077fe3d8bc1")
ARCHIVES=(TRUNCATION_ARCHIVE,RATIONAL_TAIL_ARCHIVE,SCALING_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={
    "truncation":TRUNCATION_SOURCE,"scaling":SCALING_SOURCE,"value_unique":VALUE_HELPERS["value_unique"],
    "power_unique":"forall a n x y. Pow(a,n,x) -> Pow(a,n,y) -> x=y",
    "power_nonzero":"forall d. ~d=0 -> forall k p. Pow(d,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0","mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
    "positive_order":RATIONAL_HELPERS["positive_order"],
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c","add_mul":"forall a b c. (a+b)*c=a*c+b*c",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)","add_comm":"forall a b. a+b=b+a",
}
ENDPOINT_OWNERS={name:"CV090" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(scaling="CV092",value_unique="CV061",power_unique="CV061",le_trans="CV061",
    **{name:"CV075" for name in ("power_nonzero","succ_ne_zero","mul_ne_zero","positive_order")})
HELPER_DEPENDENCIES={
    "cross_orders":("mul_assoc","mul_comm","mul_add","add_mul","mul_left_mono"),
    "CV093":("truncation","scaling","value_unique","power_unique","power_nonzero","succ_ne_zero",
        "mul_ne_zero","positive_order","cross_orders","le_trans","add_comm"),
}


class IndependentAtanhTruncationError(ValueError):
    """Changed independent actual inputs, validity premises or error scale."""


def frozen_independent_atanh_truncation_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=12 or len(premises)!=8 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise IndependentAtanhTruncationError("CV093 exact independent-table rational bounds changed")
    return target


def source_contract():
    return dict(code="CV093",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=8,two_supplied_atanh_tables_values_and_powers_preserved=True,
        independent_coefficient_and_history_codes_allowed=True,independent_nonzero_scales_allowed=True,
        actual_value_and_power_uniqueness_used=True,cross_scale_identity_proved=True,
        all_rational_denominators_proved_nonzero=True,empty_prefix_and_empty_tail_allowed=True,
        rational_bounds="3*x/(d*p)<=3*z/(e*h)<=(3*x+3*d)/(d*p)",finite_error="3/3^M",
        code_number_equality_claimed=False,analytic_limit_claim=False,analytic_logarithm_identity=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def independent_atanh_truncation_source_pins():
    result=atanh_rational_truncation_source_pins()
    for name,pin in atanh_scale_independence_source_pins().items():
        if name in result and result[name]!=pin:
            raise IndependentAtanhTruncationError("independent truncation source disagreement")
        result[name]=pin
    expected={
        "scripts/sqrt2_power_atanh_rational_truncation.py":"953740a2bfba506707c506cf250cfb8425563c6246fbc57ae93c63f471529470",
        "scripts/sqrt2_power_atanh_scale_independence.py":"bc346b492c242367d2703c2bc9391b1ae0c289a518098e1aa30b3b70252e448d",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_independent_atanh_truncation.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise IndependentAtanhTruncationError("independent truncation source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _cross_orders(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    three=Succ(Succ(Succ(Zero())))
    def finish(t):
        d,e,p,h,x,y,z=t.terms(("d","e","p","h","x","y","z"))
        td,th,tx,tz=Mul(three,d),Mul(three,h),Mul(three,x),Mul(three,z)
        eh,dp=Mul(e,h),Mul(d,p)
        left=_chain(_multiplicative_equal(t,Mul(td,Mul(h,y)),Mul(th,Mul(d,y))),
            CongMul(EqRefl(th),EqSym(t.hyp("cross"))),
            _multiplicative_equal(t,Mul(th,Mul(e,x)),Mul(tx,eh)))
        right=_multiplicative_equal(t,Mul(td,Mul(p,z)),Mul(tz,dp))
        lower=apply(specialize(t,"mul_left_mono",Mul(h,y),Mul(p,z),td),t.hyp("lower"))
        lower=_subst(t,registry,"Le(slot,(3*d)*(p*z))",left,lower)
        lower=_subst(t,registry,"Le((3*x)*(e*h),slot)",right,lower)
        upper=apply(specialize(t,"mul_left_mono",Mul(p,z),Add(Mul(h,y),eh),td),t.hyp("upper"))
        upper=_subst(t,registry,"Le(slot,(3*d)*(h*y+e*h))",right,upper)
        aligned=_chain(specialize(t,"mul_add",td,Mul(h,y),eh),CongAdd(left,EqRefl(Mul(td,eh))),
            EqSym(specialize(t,"add_mul",tx,td,eh)))
        upper=_subst(t,registry,"Le((3*z)*(d*p),slot)",aligned,upper)
        return conjunction(lower,upper)
    return introduce(s,("d","e","p","h","x","y","z"),("cross","lower","upper"),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two=Succ(Succ(Zero()));three=Succ(two)
    def chosen(t):
        d,e,M,N,x,z,p,h=t.terms(("d","e","M","N","x","z","p","h"))
        data=t.hyp("data")
        def restrict(u):
            i,M,N=u.terms(("i","M","N"))
            order=witness((N,),specialize(u,"add_comm",N,M))
            bound=apply(specialize(u,"le_trans",Succ(i),M,Add(M,N)),u.hyp("bound"),order)
            return apply(specialize(u,"prefix_b",*u.terms(("i","a"))),bound,u.hyp("entry"))
        prefix=introduce(t,("i","a"),("bound","entry"),restrict)
        cross=apply(specialize(t,"scaling",d,e,*t.terms(A+B),M,three,x,t.term("u")),
            t.hyp("prefix_a"),prefix,t.hyp("value_x"),field(data,1,12))
        equal_z=apply(specialize(t,"value_unique",*t.terms(B),three,Add(M,N),t.term("w"),z),field(data,3,12),t.hyp("value_z"))
        equal_p=apply(specialize(t,"power_unique",three,M,t.term("P"),p),field(data,4,12),t.hyp("power_p"))
        equal_h=apply(specialize(t,"power_unique",three,Add(M,N),t.term("H"),h),field(data,6,12),t.hyp("power_h"))
        lower=_subst(t,registry,"Le(H*u,P*slot)",equal_z,field(data,10,12))
        lower=_subst(t,registry,"Le(H*u,slot*z)",equal_p,lower)
        lower=_subst(t,registry,"Le(slot*u,p*z)",equal_h,lower)
        upper=_subst(t,registry,"Le(P*slot,H*u+e*H)",equal_z,field(data,11,12))
        upper=_subst(t,registry,"Le(slot*z,H*u+e*H)",equal_p,upper)
        upper=_subst(t,registry,"Le(p*z,slot*u+e*slot)",equal_h,upper)
        orders=apply(specialize(t,"cross_orders",d,e,p,h,x,t.term("u"),z),cross,lower,upper)
        nz=apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",two))
        pnz=apply(instantiate(nz,M,p),t.hyp("power_p"))
        hnz=apply(instantiate(nz,Add(M,N),h),t.hyp("power_h"))
        dp,eh=Mul(d,p),Mul(e,h)
        dpnz=apply(specialize(t,"mul_ne_zero",d,p),t.hyp("d_nonzero"),pnz)
        ehnz=apply(specialize(t,"mul_ne_zero",e,h),t.hyp("e_nonzero"),hnz)
        tx,tz,td=Mul(three,x),Mul(three,z),Mul(three,d)
        return conjunction(apply(specialize(t,"positive_order",tx,tz,dp,eh),dpnz,ehnz,field(orders,0,2)),
            apply(specialize(t,"positive_order",tz,Add(tx,td),eh,dp),ehnz,dpnz,field(orders,1,2)))
    return introduce(s,PARAMETERS,("d_nonzero","e_nonzero","prefix_a","prefix_b","value_x","value_z","power_p","power_h"),lambda t:
        eliminate(t,apply(specialize(t,"truncation",*t.terms(("e",)+B+("M","N"))),t.hyp("prefix_b")),
            ("tb","tc","u","v","w","P","Q","H"),"data",chosen))


def prove_independent_atanh_truncation(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV093",target=frozen_independent_atanh_truncation_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"cross_orders":lambda s:_cross_orders(s,registry),"CV093":lambda s:_root(s,registry)},
        pins=independent_atanh_truncation_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
