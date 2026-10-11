"""AP006: two-sided finite precision error for supplied log/root quotients.

The logarithm increases and the reciprocal root decreases. Their product
is not assumed monotone. Bound its possible increase by 3/p and decrease
by 1/d, using the actual coarse powers and two independent supplied graphs.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_log_root_argument import (
    ROOT,Scope,introduce,conjunction,apply,specialize,field,canonical,json_hash,_and,
    definition_registry as argument_registry,GRAPH as COARSE_GRAPH,BOUND_SOURCE,
)
from sqrt2_power_supplied_exp_sample import supplied_exp_sample_source_pins,HELPER_SOURCES as SUPPLIED_HELPERS
from sqrt2_power_exp_sample_independence import SUPPLIED_ARCHIVE
from sqrt2_power_dyadic_sqrt2_reciprocal import NAMED_SOURCE as RECIPROCAL_SOURCE,dyadic_sqrt2_reciprocal_source_pins
from sqrt2_power_dyadic_sqrt2_square_error import NAMED_SOURCE as SQUARE_SOURCE
from sqrt2_power_dyadic_sqrt2_modulus import HELPER_SOURCES as MODULUS_HELPERS
from sqrt2_power_dyadic_sqrt2_intervals import RATIONAL_DEFINITION_PINS,definition_registry as interval_registry
from sqrt2_power_independent_atanh_truncation import NAMED_SOURCE as LOG_SOURCE,independent_atanh_truncation_source_pins
from sqrt2_power_scaled_exp_tail import BOUND_ARCHIVE
from sqrt2_power_quadratic_trace_exists import witness
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-argument-modulus-v1"
PARAMETERS=("k","l","d","s","D","ab","ac","x","p","q","t","E","bb","bc","z","h")
FINE_GRAPH="NatSqrt2LogArgument(k+l,q,t,E,bb,bc,z,h)"
U,V,Z,W="((3*x)*d)","((D*p)*s)","((3*z)*q)","((E*h)*t)"
PARTS=(f"~{V}=0",f"~{W}=0",f"Le({V}*{Z},{W}*{U}+((3*D)*(E*h))*(s*t))",
       f"Le(d*({W}*{U}),d*({V}*{Z})+{V}*{W})")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". ~D=0 -> ~E=0 -> "+COARSE_GRAPH+" -> "+FINE_GRAPH+" -> "+_and(PARTS)
TARGET_SHA256="cbc032a1e559ba87536c09544a5f7e321cc43378460e87bddebc0cb65a85584c"
ARITHMETIC_PARAMETERS=("a","b","c","e","d","s","q","t","r")
ARITHMETIC_PREMISES=("Le(a*e,b*c)","Le(b*c,a*e+r)","Le(a,c)","Le(q*s,d*t)",
    "Le(d*(d*t),d*(q*s)+s*t)","Le(q,t)")
ARITHMETIC_CONCLUSION="Le((c*s)*(b*q),(e*t)*(a*d)+r*(s*t)) /\\ Le(d*((e*t)*(a*d)),d*((c*s)*(b*q))+(c*s)*(e*t))"
HELPER_SOURCES={
    "length":"forall k l. S(2*(k+l))=S(2*k)+2*l",
    "drop_margin":"forall a b c. Le(a+b,c) -> Le(a,c)",
    "arithmetic":"forall "+" ".join(ARITHMETIC_PARAMETERS)+". "+" -> ".join(ARITHMETIC_PREMISES)+" -> "+ARITHMETIC_CONCLUSION,
}
HELPER_TARGET_SHA256={"length":"7bdd21129f8217b37270af2f45a1d583d4f995c0ae99857ac64278a92883d232",
    "drop_margin":"07e8c8376000608c9dd8a34208a3ed121f1aa51311e5145bc574cf1743a2138e",
    "arithmetic":"5f85e6b81296b90529cd1fe2e105b33bba9a90a02ce7243787a16d220ad9dcc6"}
RECIPROCAL_ARCHIVE=dict(case="SQ010",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-dyadic-sqrt2-reciprocal-v1/generation-process.json.gz",
    bytes=28065,sha256="4309664d5bd82e7a9476beeaeeca621c709092979f93e680eac694135584dbbf",
    raw_bytes=527151,raw_sha256="c8251d2120094f8acbc59b74b7b5f20cff5d850af715a47f74e84a1cdc139d3b",
    bundle_bytes=318039,bundle_sha256="16ba3030487cf8f07c10bd9a3cc909569392a2b677c8bbd6322d8bcd4e403ab4",
    nodes=149,root=148,target_ast_sha256="4e5333c99ca1ed711e3c4059b5352c1b5545b4d3d6ce9e26db04482a0f15cdcd")
LOG_ARCHIVE=dict(case="CV093",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-independent-atanh-truncation-v1/generation-process.json.gz",
    bytes=51482,sha256="33edb62853baebb1d9030f635919e3c664378def86d0eb06791f0362c0ad072b",
    raw_bytes=755060,raw_sha256="1ed19bd21f7384ab214d464988bc17d4f0bfb3440ab121a4eeb48650b35f0d7c",
    bundle_bytes=430464,bundle_sha256="d687a27e5e4e4a010c27dcdc93fe18548e682cd1bfa3c03e7d32e04aa65f1acd",
    nodes=155,root=154,target_ast_sha256="c8bd73e82050b43d383204e7e5e1fc00bda755d88df07a5fb9b1c8f5700f3f6b")
ARCHIVES=(RECIPROCAL_ARCHIVE,LOG_ARCHIVE,SUPPLIED_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    "reciprocal":RECIPROCAL_SOURCE,"logarithm":LOG_SOURCE,"square":SQUARE_SOURCE,
    "argument":SUPPLIED_HELPERS["argument"],"positive_natural":MODULUS_HELPERS["positive_natural"],"inner_bound":BOUND_SOURCE,
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c","add_mul":"forall a b c. (a+b)*c=a*c+b*c",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "add_comm":"forall a b. a+b=b+a","add_succ_left":"forall a b. S a+b=S(a+b)",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)","mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "add_right_mono":"forall a b c. Le(a,b) -> Le(a+c,b+c)","add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(reciprocal="SQ010",square="SQ010",positive_natural="SQ010",logarithm="CV093",argument="AP004",inner_bound="AP004")
HELPER_DEPENDENCIES={
    "length":("mul_add","add_succ_left"),"drop_margin":("add_comm","le_trans"),
    "arithmetic":("mul_assoc","mul_comm","mul_add","add_mul","mul_left_mono","mul_right_mono","add_left_mono","add_right_mono","le_trans"),
    "AP006":("length","drop_margin","arithmetic","reciprocal","logarithm","square","argument","positive_natural","inner_bound","add_mul"),
}


class ArgumentModulusError(ValueError):
    """Changed actual precisions, asymmetric errors, definition identity or proof."""


def definition_registry():
    from peano_lab.library.proof_bundle import encode_formula
    result=dict(argument_registry());rational=interval_registry()
    for name,(identifier,digest) in RATIONAL_DEFINITION_PINS.items():
        spec=rational[name]
        if (spec.stable_id!=identifier or json_hash(encode_formula(spec.template_formula))!=digest
                or name in result or identifier in {d.stable_id for d in result.values()}
                or not set(spec.conceptual_dependencies)<=result.keys()):
            raise ArgumentModulusError("reused rational order definition identity or DAG changed")
        result[name]=spec
    return MappingProxyType(result)


def frozen_argument_modulus_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=16 or len(premises)!=4 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ArgumentModulusError("AP006 exact supplied-precision modulus target changed")
    return target


def source_contract():
    return dict(code="AP006",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,both_supplied_independent_graphs_preserved=True,positive_coefficient_scales_required=True,
        actual_coarse_and_fine_powers_preserved=True,zero_precision_and_increment_allowed=True,
        both_quotient_denominators_proved_nonzero=True,argument_monotonicity_assumed=False,
        rational_increase_bound="3/p",rational_decrease_bound="1/d",exact_prefix_length_alignment=True,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        reused_rational_definition_ids=["ND0382","ND0444"],analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def argument_modulus_source_pins():
    result=supplied_exp_sample_source_pins()
    for source in (dyadic_sqrt2_reciprocal_source_pins(),independent_atanh_truncation_source_pins()):
        for name,pin in source.items():
            if name in result and result[name]!=pin:
                raise ArgumentModulusError("argument modulus source disagreement")
            result[name]=pin
    expected={"scripts/sqrt2_power_dyadic_sqrt2_reciprocal.py":"fc6891efec73b36bb8aaba4386925f07bd5a39cd8ed85a233edede3384f4b339",
        "scripts/sqrt2_power_supplied_exp_sample.py":"30423d296b32b21ea9d3c35802cb81dbe5dae1fb4a589f8a8abce112e93be11a",
        "scripts/sqrt2_power_exp_sample_independence.py":"e6ec0523040135408adbadfc5cf46351f4682bd6a3b1f564c08263f8cb692187",
        "scripts/sqrt2_power_independent_atanh_truncation.py":"e51d53ad60fcc02a38ab75b6425abc92dbc58f06ba5f6309c562990cdc24c427",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_argument_modulus.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ArgumentModulusError("argument modulus source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _length(s):
    from peano_lab.kernel.proofs import CongS,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()))
    return introduce(s,("k","l"),(),lambda t:_chain(
        CongS(specialize(t,"mul_add",two,*t.terms(("k","l")))),
        EqSym(specialize(t,"add_succ_left",Mul(two,t.term("k")),Mul(two,t.term("l"))))))


def _drop_margin(s):
    from peano_lab.kernel.terms import Add
    def finish(t):
        a,b,c=t.terms(("a","b","c"))
        lower=witness((b,),specialize(t,"add_comm",b,a))
        return apply(specialize(t,"le_trans",a,Add(a,b),c),lower,t.hyp("bound"))
    return introduce(s,("a","b","c"),("bound",),finish)


def _left(t,registry,proof,right,equality):
    from peano_lab.kernel.terms import pretty_term
    return _subst(t,registry,"Le(slot,"+pretty_term(right,list(t.variables))+")",equality,proof)


def _right(t,registry,proof,left,equality):
    from peano_lab.kernel.terms import pretty_term
    return _subst(t,registry,"Le("+pretty_term(left,list(t.variables))+",slot)",equality,proof)


def _sum_order(t,a,b,c,d,first,second):
    from peano_lab.kernel.terms import Add
    left=apply(specialize(t,"add_right_mono",a,b,c),first)
    right=apply(specialize(t,"add_left_mono",c,d,b),second)
    return apply(specialize(t,"le_trans",Add(a,c),Add(b,c),Add(b,d)),left,right)


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        a,b,c,e,d,root,q,out,r=t.terms(ARITHMETIC_PARAMETERS)
        ae,bc,qs,dt,st=Mul(a,e),Mul(b,c),Mul(q,root),Mul(d,out),Mul(root,out)
        cs,et,ad,bq=Mul(c,root),Mul(e,out),Mul(a,d),Mul(b,q)
        vz,wu=Mul(cs,bq),Mul(et,ad)
        # Possible increase: log tail times the fine reciprocal (at most one).
        upper=apply(specialize(t,"mul_right_mono",bc,Add(ae,r),qs),t.hyp("log_upper"))
        upper=_left(t,registry,upper,Mul(Add(ae,r),qs),_multiplicative_equal(t,Mul(bc,qs),vz))
        upper=_right(t,registry,upper,vz,specialize(t,"add_mul",ae,r,qs))
        first=apply(specialize(t,"mul_left_mono",qs,dt,ae),t.hyp("reciprocal_lower"))
        small=apply(specialize(t,"mul_right_mono",q,out,root),t.hyp("fine_range"))
        small=_right(t,registry,small,qs,specialize(t,"mul_comm",out,root))
        second=apply(specialize(t,"mul_left_mono",qs,st,r),small)
        added=_sum_order(t,Mul(ae,qs),Mul(ae,dt),Mul(r,qs),Mul(r,st),first,second)
        upper=apply(specialize(t,"le_trans",vz,Add(Mul(ae,qs),Mul(r,qs)),Add(Mul(ae,dt),Mul(r,st))),upper,added)
        upper=_right(t,registry,upper,vz,CongAdd(_multiplicative_equal(t,Mul(ae,dt),wu),EqRefl(Mul(r,st))))
        # Possible decrease: reciprocal error times the coarse log (at most one).
        dqs=Mul(d,qs);dwu=Mul(d,wu);dvz=Mul(d,vz);vw=Mul(cs,et)
        lower=apply(specialize(t,"mul_left_mono",Mul(d,dt),Add(dqs,st),ae),t.hyp("reciprocal_upper"))
        lower=_left(t,registry,lower,Mul(ae,Add(dqs,st)),_multiplicative_equal(t,Mul(ae,Mul(d,dt)),dwu))
        lower=_right(t,registry,lower,dwu,specialize(t,"mul_add",ae,dqs,st))
        first=apply(specialize(t,"mul_right_mono",ae,bc,dqs),t.hyp("log_lower"))
        first=_right(t,registry,first,Mul(ae,dqs),_multiplicative_equal(t,Mul(bc,dqs),dvz))
        est=Mul(e,st)
        second=apply(specialize(t,"mul_right_mono",a,c,est),t.hyp("coarse_log_range"))
        second=_left(t,registry,second,Mul(c,est),_multiplicative_equal(t,Mul(a,est),Mul(ae,st)))
        second=_right(t,registry,second,Mul(ae,st),_multiplicative_equal(t,Mul(c,est),vw))
        added=_sum_order(t,Mul(ae,dqs),dvz,Mul(ae,st),vw,first,second)
        lower=apply(specialize(t,"le_trans",dwu,Add(Mul(ae,dqs),Mul(ae,st)),Add(dvz,vw)),lower,added)
        return conjunction(upper,lower)
    return introduce(s,ARITHMETIC_PARAMETERS,("log_lower","log_upper","coarse_log_range",
        "reciprocal_lower","reciprocal_upper","fine_range"),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two=Succ(Succ(Zero()));three=Succ(two)
    def finish(t):
        k,l,d,root,D,ab,ac,x,p,q,out,E,bb,bc,z,h=t.terms(PARAMETERS)
        coarse=t.hyp("coarse");fine=t.hyp("fine");M=Succ(Mul(two,k));extra=Mul(two,l)
        length=specialize(t,"length",k,l)
        prefix=_subst(t,registry,"NatAtanhPrefix(E,bb,bc,slot)",length,field(fine,1,4))
        value=_subst(t,registry,"NatHornerValue(bb,bc,3,slot,z)",length,field(fine,2,4))
        power=_subst(t,registry,"Pow(3,slot,h)",length,field(fine,3,4))
        log=apply(specialize(t,"logarithm",D,E,ab,ac,bb,bc,M,extra,x,z,p,h),t.hyp("D_nonzero"),t.hyp("E_nonzero"),
            field(coarse,1,4),prefix,field(coarse,2,4),value,field(coarse,3,4),power)
        a,b,c,e=Mul(three,x),Mul(three,z),Mul(D,p),Mul(E,h);td=Mul(three,D);r=Mul(td,e)
        log_lower=apply(specialize(t,"positive_natural",a,b,c,e),AndElimL(log))
        log_upper=apply(specialize(t,"positive_natural",b,Add(a,td),e,c),AndElimR(log))
        log_upper=_right(t,registry,log_upper,Mul(b,c),specialize(t,"add_mul",a,td,e))
        inner=apply(specialize(t,"inner_bound",D,ab,ac,Mul(two,k),x,p),field(coarse,1,4),field(coarse,2,4),field(coarse,3,4))
        inner=apply(specialize(t,"drop_margin",a,td,c),inner)
        reciprocal=apply(specialize(t,"reciprocal",k,l,d,root,q,out),field(coarse,0,4),field(fine,0,4))
        square=apply(specialize(t,"square",Add(k,l),q,out),field(fine,0,4))
        bounds=apply(specialize(t,"arithmetic",a,b,c,e,d,root,q,out,r),log_lower,log_upper,inner,
            field(reciprocal,3,5),field(reciprocal,4,5),field(square,2,6))
        coarse_valid=apply(specialize(t,"argument",k,d,root,D,ab,ac,x,p),t.hyp("D_nonzero"),coarse)
        fine_valid=apply(specialize(t,"argument",Add(k,l),q,out,E,bb,bc,z,h),t.hyp("E_nonzero"),fine)
        return conjunction(AndElimL(coarse_valid),AndElimL(fine_valid),AndElimL(bounds),AndElimR(bounds))
    return introduce(s,PARAMETERS,("D_nonzero","E_nonzero","coarse","fine"),finish)


def prove_argument_modulus(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP006",target=frozen_argument_modulus_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"length":_length,"drop_margin":_drop_margin,"arithmetic":lambda s:_arithmetic(s,registry),
                   "AP006":lambda s:_root(s,registry)},pins=argument_modulus_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
