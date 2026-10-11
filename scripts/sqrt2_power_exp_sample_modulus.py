"""AP009: scale-free two-sided errors for actual samples at finer precision.

Preserve both complete computation graphs at k and k+S l and an actual cutoff
power r=2^(k+2). Combine AP006 and AP008, then cancel only factors separately
proved nonzero. Neither independent codes nor normalization heads are equated.
"""
from hashlib import sha256

from sqrt2_power_supplied_exp_sample import (
    ROOT,Scope,introduce,conjunction,apply,specialize,field,canonical,json_hash,_and,
    definition_registry,PARAMETERS as COARSE_PARAMETERS,GRAPH as COARSE_GRAPH,
    NAMED_SOURCE as SUPPLIED_SOURCE,SQUARE_SOURCE,
)
from sqrt2_power_exp_sample_independence import SUPPLIED_ARCHIVE
from sqrt2_power_argument_modulus import NAMED_SOURCE as INPUT_SOURCE,argument_modulus_source_pins
from sqrt2_power_exp_two_sided_horizons import NAMED_SOURCE as HORIZON_SOURCE,exp_two_sided_horizons_source_pins
from sqrt2_power_exp_two_sided_continuity import _left,_right,_chain,_multiplicative_equal,_additive_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-sample-modulus-v1"
FINE_OUTPUTS=("q","t","E","bb","bc","z","v","xb","xc","ub","uc","v0","g","j","o")
PARAMETERS=("k","l")+COARSE_PARAMETERS[1:]+FINE_OUTPUTS+("r",)
FINE_GRAPH="NatSqrt2ExpSample(k+S l,"+",".join(FINE_OUTPUTS)+")"
PARTS=("~d=0","~p=0","~r=0","~w0=0","~v0=0",
    "Le((p*r)*(w0*o),(p*r)*(v0*y)+((9*3)*r+2*p)*(w0*v0))",
    "Le(d*(v0*y),d*(w0*o)+9*(w0*v0))")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~D=0 -> ~E=0 -> "+COARSE_GRAPH+" -> "+FINE_GRAPH+" -> Pow(2,k+2,r) -> "+_and(PARTS)
TARGET_SHA256="073e1e33119841ca820f40504b4be88839cec838afc45b6028bda6807fa464dd"
NORMALIZE_PARAMETERS=("d","F","p","r","B","a","b","u","v")
NORMALIZE_PREMISES=("~d=0","~F=0","p*B=3*F",
    "Le(r*(d*(F*(a*v))),r*(d*(F*(b*u)))+(9*(r*(d*B))+2*(d*F))*(a*b))",
    "Le(d*(F*(b*u)),d*(F*(a*v))+9*(F*(a*b)))")
NORMALIZE_CONCLUSION="Le((p*r)*(a*v),(p*r)*(b*u)+((9*3)*r+2*p)*(a*b)) /\\ Le(d*(b*u),d*(a*v)+9*(a*b))"
HELPER_SOURCES={
    "length":"forall k l. (k+S l)+2=S(k+2)+l",
    "normalize":"forall "+" ".join(NORMALIZE_PARAMETERS)+". "+" -> ".join(NORMALIZE_PREMISES)+" -> "+NORMALIZE_CONCLUSION,
}
HELPER_TARGET_SHA256={"length":"2b9c0600317f07df98b7bfbb39e953c7f52f75b7b4704f13da3576c86eb5ec01",
    "normalize":"f47da4b5c648dc0b6a9dee9076970a107b031c2585a43f6c18bf266359a6a545"}
INPUT_ARCHIVE=dict(case="AP006",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-argument-modulus-v1/generation-process.json.gz",
    bytes=63074,sha256="30590e98578f0d7b245cad99aed5b19c653d41b1ba6841846d59ad1c87a5e0de",
    raw_bytes=1029198,raw_sha256="6adfc247aace94ce0ed458f8270756b061f3eb22a1c174dc58b1346badf68cc8",
    bundle_bytes=595548,bundle_sha256="bf75787641e08251020beebea70fd3b959a6a124299bc6912608463dd6d8bb41",
    nodes=188,root=187,target_ast_sha256="cbc032a1e559ba87536c09544a5f7e321cc43378460e87bddebc0cb65a85584c")
HORIZON_ARCHIVE=dict(case="AP008",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-two-sided-horizons-v1/generation-process.json.gz",
    bytes=63747,sha256="a2dfe74b4f69cdf13a42acac76360583ec069b7932a9e8aa310ae17bc9b74fc0",
    raw_bytes=1113554,raw_sha256="a76ad2dd51339e2b019b106c04dfd56e3035b5a0f58ef539d80d2070e7388b0a",
    bundle_bytes=657992,bundle_sha256="bc30f35fc3fbab167f5bd5d629e8cc410adc89a0b3f0300f74702335b96ef99e",
    nodes=197,root=196,target_ast_sha256="345ef6c15b5813f3423a35a13c658fa76dd43b9bc8fc56f2aed0330e254c788a")
ARCHIVES=(INPUT_ARCHIVE,HORIZON_ARCHIVE,SUPPLIED_ARCHIVE)
ENDPOINT_SOURCES={
    "input":INPUT_SOURCE,"horizons":HORIZON_SOURCE,"supplied":SUPPLIED_SOURCE,"square":SQUARE_SOURCE,
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0","mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0",
    "mul_le_cancel":"forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)","add_comm":"forall a b. a+b=b+a",
    "add_succ_left":"forall a b. S a+b=S(a+b)",
}
ENDPOINT_OWNERS={name:"AP008" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(input="AP006",supplied="AP004",square="AP006",power_nonzero="AP004",succ_ne_zero="AP004",mul_ne_zero="AP004")
HELPER_DEPENDENCIES={
    "length":("add_succ_left","add_assoc","add_comm"),
    "normalize":("mul_left_mono","mul_assoc","mul_comm","mul_add","mul_ne_zero","mul_le_cancel"),
    "AP009":("length","normalize","input","horizons","supplied","square","power_nonzero","succ_ne_zero","mul_ne_zero","mul_left_mono","mul_add","mul_assoc","mul_comm"),
}


class ExpSampleModulusError(ValueError):
    """Changed complete samples, strict precision increment or scale-free error."""


def frozen_exp_sample_modulus_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=33 or len(premises)!=5 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSampleModulusError("AP009 exact finer sample error target changed")
    return target


def source_contract():
    return dict(code="AP009",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,both_supplied_complete_sample_graphs_preserved=True,positive_coefficient_scales_required=True,
        strict_precision_increment="S l",actual_cutoff_power="r=2^(k+2)",coarse_logarithm_power="p=3^(2*k+1)",
        arbitrary_common_coefficient_scales_eliminated=True,only_positive_factors_cancelled=True,
        rational_increase_bound="27/p+2/r",rational_decrease_bound="9/d",all_displayed_rational_denominators_proved_nonzero=True,
        argument_monotonicity_assumed=False,zero_precision_allowed=True,same_precision_requires_separate_AP005=True,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_sample_modulus_source_pins():
    result=argument_modulus_source_pins()
    for name,pin in exp_two_sided_horizons_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpSampleModulusError("sample modulus source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_argument_modulus.py":"e8b4b0f02084fa368f60fcb69c6f265e15bb2cb7d35b16118c69cea174f2a451",
        "scripts/sqrt2_power_exp_two_sided_horizons.py":"9496e65b6708aa5025dd8bfb06a2c79fb445f84f7deac2f7585d4861c04aeaf5",
        "scripts/sqrt2_power_supplied_exp_sample.py":"30423d296b32b21ea9d3c35802cb81dbe5dae1fb4a589f8a8abce112e93be11a",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_sample_modulus.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSampleModulusError("sample modulus source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _length(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongS,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,parse_term
    two=parse_term("2")
    def finish(t):
        k,l=t.terms(("k","l"))
        return _chain(CongAdd(instantiate(Axiom("PA4"),k,l),EqRefl(two)),specialize(t,"add_succ_left",Add(k,l),two),
            CongS(_additive_equal(t,Add(Add(k,l),two),Add(Add(k,two),l))),EqSym(specialize(t,"add_succ_left",Add(k,two),l)))
    return introduce(s,("k","l"),(),finish)


def _normalize(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,three,nine=(parse_term(n) for n in ("2","3","9"))
    def finish(t):
        d,F,p,r,B,a,b,u,v=t.terms(NORMALIZE_PARAMETERS)
        df=Mul(d,F);ab=Mul(a,b);av=Mul(a,v);bu=Mul(b,u);pr=Mul(p,r)
        oldleft=Mul(r,Mul(d,Mul(F,av)));oldbase=Mul(r,Mul(d,Mul(F,bu)))
        oldarg=Mul(nine,Mul(r,Mul(d,B)));oldtail=Mul(two,df);olderr=Mul(Add(oldarg,oldtail),ab)
        newleft=Mul(pr,av);newbase=Mul(pr,bu);argcoef=Mul(Mul(nine,three),r);tailcoef=Mul(two,p);coef=Add(argcoef,tailcoef);newerr=Mul(coef,ab)
        # Multiply by p, use p*B=3*F, and factor the positive common d*F.
        upper=apply(specialize(t,"mul_left_mono",oldleft,Add(oldbase,olderr),p),t.hyp("upper"))
        upper=_left(t,registry,upper,Mul(p,Add(oldbase,olderr)),_multiplicative_equal(t,Mul(p,oldleft),Mul(df,newleft)))
        nrd=Mul(Mul(nine,r),d)
        first=_chain(_multiplicative_equal(t,Mul(p,oldarg),Mul(nrd,Mul(p,B))),
            CongMul(EqRefl(nrd),t.hyp("scale")),_multiplicative_equal(t,Mul(nrd,Mul(three,F)),Mul(df,argcoef)))
        second=_multiplicative_equal(t,Mul(p,oldtail),Mul(df,tailcoef))
        error=_chain(_multiplicative_equal(t,Mul(p,olderr),Mul(Mul(p,Add(oldarg,oldtail)),ab)),
            CongMul(specialize(t,"mul_add",p,oldarg,oldtail),EqRefl(ab)),
            CongMul(CongAdd(first,second),EqRefl(ab)),
            CongMul(EqSym(specialize(t,"mul_add",df,argcoef,tailcoef)),EqRefl(ab)),specialize(t,"mul_assoc",df,coef,ab))
        right=_chain(specialize(t,"mul_add",p,oldbase,olderr),CongAdd(_multiplicative_equal(t,Mul(p,oldbase),Mul(df,newbase)),error),
            EqSym(specialize(t,"mul_add",df,newbase,newerr)))
        upper=_right(t,registry,upper,Mul(df,newleft),right)
        nz=apply(specialize(t,"mul_ne_zero",d,F),t.hyp("d_nonzero"),t.hyp("F_nonzero"))
        upper=apply(specialize(t,"mul_le_cancel",df,newleft,Add(newbase,newerr)),nz,upper)
        # For the reverse error only F is cancelled; its positivity is explicit.
        lowleft=Mul(d,bu);lowbase=Mul(d,av);lowerr=Mul(nine,ab)
        lower=_left(t,registry,t.hyp("lower"),Add(Mul(d,Mul(F,av)),Mul(nine,Mul(F,ab))),
            _multiplicative_equal(t,Mul(d,Mul(F,bu)),Mul(F,lowleft)))
        right=_chain(CongAdd(_multiplicative_equal(t,Mul(d,Mul(F,av)),Mul(F,lowbase)),
            _multiplicative_equal(t,Mul(nine,Mul(F,ab)),Mul(F,lowerr))),EqSym(specialize(t,"mul_add",F,lowbase,lowerr)))
        lower=_right(t,registry,lower,Mul(F,lowleft),right)
        lower=apply(specialize(t,"mul_le_cancel",F,lowleft,Add(lowbase,lowerr)),t.hyp("F_nonzero"),lower)
        return conjunction(upper,lower)
    return introduce(s,NORMALIZE_PARAMETERS,("d_nonzero","F_nonzero","scale","upper","lower"),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongS
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    two,three=(parse_term(n) for n in ("2","3"))
    def finish(t):
        k,l,d,root,D,x,p,q,out,E,z,v,r=t.terms(("k","l","d","s","D","x","p","q","t","E","z","v","r"))
        fine_precision=Add(k,Succ(l));m=Add(k,two)
        coarse=t.hyp("coarse");fine=t.hyp("fine");cg=field(coarse,0,9);fg=field(fine,0,9)
        A=apply(specialize(t,"supplied",*t.terms(COARSE_PARAMETERS)),t.hyp("D_nonzero"),coarse)
        B=apply(specialize(t,"supplied",fine_precision,*t.terms(FINE_OUTPUTS)),t.hyp("E_nonzero"),fine)
        U,V=Mul(Mul(three,x),d),Mul(Mul(D,p),root);Z,W=Mul(Mul(three,z),q),Mul(Mul(E,v),out)
        F=Mul(V,W);margin=Mul(Mul(Mul(three,D),Mul(E,v)),Mul(root,out));R=Mul(d,margin)
        errors=apply(specialize(t,"input",k,Succ(l),d,root,D,*t.terms(("ab","ac")),x,p,q,out,E,*t.terms(("bb","bc")),z,v),
            t.hyp("D_nonzero"),t.hyp("E_nonzero"),cg,fg)
        forward=apply(specialize(t,"mul_left_mono",Mul(V,Z),Add(Mul(W,U),margin),d),field(errors,2,4))
        forward=_right(t,registry,forward,Mul(d,Mul(V,Z)),specialize(t,"mul_add",d,Mul(W,U),margin))
        length=specialize(t,"length",k,l)
        recurrence=_subst(t,registry,"NatScaledExpRecurrence(((E*v)*t),((3*z)*q),ub,uc,slot)",length,field(B,3,5))
        total=_subst(t,registry,"Sum(ub,uc,slot,o)",CongS(length),field(fine,8,9))
        bounds=apply(specialize(t,"horizons",V,W,U,Z,d,R,F,m,l,*t.terms(("tb","tc","ub","uc","w0","v0","y","o")),r),
            field(A,1,5),field(B,1,5),field(A,2,5),field(B,2,5),forward,field(errors,3,4),
            field(A,3,5),recurrence,field(coarse,4,9),field(fine,4,9),field(coarse,8,9),total,t.hyp("power"))
        square=apply(specialize(t,"square",k,d,root),field(cg,0,4));dnz=field(square,0,6)
        Fnz=apply(specialize(t,"mul_ne_zero",V,W),field(A,1,5),field(B,1,5))
        scale=_multiplicative_equal(t,Mul(p,margin),Mul(three,F))
        normalized=apply(specialize(t,"normalize",d,F,p,r,margin,*t.terms(("w0","v0","y","o"))),dnz,Fnz,scale,AndElimL(bounds),AndElimR(bounds))
        pnz=apply(instantiate(apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",two)),Succ(Mul(two,k)),p),field(cg,3,4))
        rnz=apply(instantiate(apply(specialize(t,"power_nonzero",two),specialize(t,"succ_ne_zero",parse_term("1"))),m,r),t.hyp("power"))
        return conjunction(dnz,pnz,rnz,field(A,0,5),field(B,0,5),AndElimL(normalized),AndElimR(normalized))
    return introduce(s,PARAMETERS,("D_nonzero","E_nonzero","coarse","fine","power"),finish)


def prove_exp_sample_modulus(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP009",target=frozen_exp_sample_modulus_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"length":_length,"normalize":lambda s:_normalize(s,registry),"AP009":lambda s:_root(s,registry)},
        pins=exp_sample_modulus_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
