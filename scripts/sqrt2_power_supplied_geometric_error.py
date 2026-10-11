"""CV084: actual supplied base-three values have valid rational error bounds.

Align the cutoff and tail lengths explicitly, prove the product of actual
powers, split the caller's full value, and apply the geometric-tail sandwich.
All rational denominators are proved nonzero. This is still a conditional
finite computation theorem, not construction of an analytic limit.
"""
from hashlib import sha256

from sqrt2_power_rational_tail_majorant import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,rational_tail_majorant_source_pins,
    HELPER_SOURCES as RATIONAL_HELPERS,ENDPOINT_SOURCES as RATIONAL_ENDPOINTS,
    COMPOSITION_ARCHIVE,
)
from sqrt2_power_composition_tail_bound import RATIONAL_TAIL_ARCHIVE
from sqrt2_power_supplied_horner_splitting import NAMED_SOURCE as SPLIT_SOURCE,supplied_horner_splitting_source_pins
from sqrt2_power_geometric_tail_sandwich import NAMED_SOURCE as SANDWICH_SOURCE,geometric_tail_sandwich_source_pins,_numeral
from sqrt2_power_full_composition_evaluation import conjoin
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-supplied-geometric-error-v1"
U,T = ("ub","uc"),("tb","tc")
PARAMETERS = U+T+("k","r","z","x","y","u","p","h","q","a")
J,N,L = "((S k)+r)","S k","S r"
PREMISES = ("~z=0","NatHornerValue(ub,uc,3,S k,x)","x+z=(2*z)*p","Pow(3,k,p)",
    "NatAffineSlice(ub,uc,S k,1,tb,tc,S r)","NatHornerValue(tb,tc,3,S r,u)",
    "NatHornerValue(ub,uc,3,S "+J+",y)","Pow(3,"+J+",h)","Pow(3,S k,q)","Pow(2,S k,a)",
    "Le(u*q,(9*a)*(z*h))")
PARTS = ("Pow(3,S r,b)","h=p*b","y=b*x+u","~p=0","~q=0","~h=0","~(z*h)=0","~((z*h)*p)=0",
    "y+z*b=(2*z)*h+u","Le(y*q,(2*q+9*a)*(z*h))","Le((2*p)*(z*h),y*p+z*h)",
    "IRatLe(y,0,z*h,2*q+9*a,0,q)","IRatLe(2,0,1,y*p+z*h,0,(z*h)*p)")
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> exists b. "+conjoin(PARTS)
TARGET_SHA256 = "4ee4edb3a27c63810499bc48918c92c504253b783efa6e306acf9c98ba79f558"
HELPER_SOURCES,HELPER_TARGET_SHA256 = {},{}
SPLIT_ARCHIVE = dict(case="CV082",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-supplied-horner-splitting-v1/generation-process.json.gz",
    bytes=18725,sha256="c92eae18812fccb9ec15c9f6f102e21f362704a53e91ba9df082abbb655d767f",
    raw_bytes=228514,raw_sha256="8261fbb8a83c577d258b64e7960d543584c7279014fe4094a054d6ab0dd724cc",
    bundle_bytes=106956,bundle_sha256="471fda92b4c23387af927e0452c262de5ebc4f043563b67c1eec37c75bc90b57",
    nodes=38,root=37,target_ast_sha256="2060fe5fe40be2b8cca591f0f8c6e4703cbe9367a3616d60b77f5e6c457553fc")
SANDWICH_ARCHIVE = dict(case="CV083",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-geometric-tail-sandwich-v1/generation-process.json.gz",
    bytes=14294,sha256="55290ccb937f68306de9b1c299d63ae342327dcc598c103948f4c1c0f0033503",
    raw_bytes=107369,raw_sha256="490566adba0c14f9737b43c29851e048555fd6de7074f27832b0166b94e97a14",
    bundle_bytes=32215,bundle_sha256="c6ba62017eda3d139acc2d7694d8e37d2d02da904b4054901c0d2ac9103bde0a",
    nodes=14,root=13,target_ast_sha256="6ab738597b29754dfe8c2ecd8edd19ed02b665f859a9b263e2eb80903c75afbd")
ARCHIVES = (COMPOSITION_ARCHIVE,RATIONAL_TAIL_ARCHIVE,SPLIT_ARCHIVE,SANDWICH_ARCHIVE)
ENDPOINT_SOURCES = {"split":SPLIT_SOURCE,"sandwich":SANDWICH_SOURCE,"positive_order":RATIONAL_HELPERS["positive_order"],
    **{name:RATIONAL_ENDPOINTS[name] for name in ("power_exists","power_add","power_nonzero","mul_ne_zero","succ_ne_zero","mul_assoc","mul_comm")},
    "add_succ_left":"forall a b. S a+b=S(a+b)","mul_one":"forall a. a*1=a"}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(split="CV082",sandwich="CV083",positive_order="CV075",power_nonzero="CV075")
HELPER_DEPENDENCIES = {"CV084":tuple(ENDPOINT_SOURCES)}


class SuppliedGeometricErrorError(ValueError):
    """Changed actual finite evaluation, power alignment or valid denominators."""


def frozen_supplied_geometric_error_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=14 or len(premises)!=11 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SuppliedGeometricErrorError("CV084 exact supplied finite rational errors changed")
    return target


def source_contract():
    return dict(code="CV084",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=11,supplied_coefficients_tail_and_values_preserved=True,cutoff="N=k+1",full_degree="J=N+r",
        actual_tail_scaling_power_constructed=True,actual_power_product_proved=True,
        exact_prefix_tail_split_proved=True,all_rational_denominators_proved_nonzero=True,
        rational_upper="y/(z*3^J) <= 2+9*(2/3)^N",
        rational_lower="2 <= y/(z*3^J)+1/3^(N-1)",
        approximation_or_composition_existence_claimed=False,geometric_pattern_and_tail_bound_are_premises=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def supplied_geometric_error_source_pins():
    result = rational_tail_majorant_source_pins()
    for source in (supplied_horner_splitting_source_pins,geometric_tail_sandwich_source_pins):
        for name,pin in source().items():
            if name in result and result[name]!=pin:
                raise SuppliedGeometricErrorError("supplied geometric-error source pin disagreement")
            result[name] = pin
    expected = {"scripts/sqrt2_power_supplied_horner_splitting.py":"b1fdc189346d96374957b602fee0109b517dd7602884769e7ea18ff77cd8b199",
        "scripts/sqrt2_power_geometric_tail_sandwich.py":"95083a6719b0cb25c7b1c25539713def8dcfacb3d89484316b75fb32ecf5cb56",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_supplied_geometric_error.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SuppliedGeometricErrorError("supplied geometric-error source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def chosen(t):
        k,r,z,x,y,u,p,h,q,a,b = t.terms(("k","r","z","x","y","u","p","h","q","a","b"))
        one,two,three,nine = _numeral(1),_numeral(2),_numeral(3),_numeral(9)
        N,J = Succ(k),Add(Succ(k),r);zh = Mul(z,h);zhp = Mul(zh,p)
        exponent = _chain(specialize(t,"add_succ_left",k,r),EqSym(instantiate(Axiom("PA4"),k,r)))
        scale = apply(specialize(t,"power_add",three,k,Succ(r),J,p,b,h),exponent,t.hyp("power_p"),t.hyp("power_b"),t.hyp("power_h"))
        whole = _subst(t,registry,"NatHornerValue(ub,uc,3,slot,y)",EqSym(instantiate(Axiom("PA4"),N,r)),t.hyp("whole_value"))
        split = apply(specialize(t,"split",*t.terms(U+T),three,N,Succ(r),x,u,y,b),
            t.hyp("slice"),t.hyp("prefix_value"),t.hyp("tail_value"),whole,t.hyp("power_b"))
        sandwich = apply(specialize(t,"sandwich",x,z,p,b,y,u,h,q,a),t.hyp("geometric"),split,scale,t.hyp("tail_bound"))
        three_nz = specialize(t,"succ_ne_zero",two)
        def power_nonzero(exponent,value,proof):
            return apply(instantiate(apply(specialize(t,"power_nonzero",three),three_nz),exponent,value),proof)
        pnz = power_nonzero(k,p,t.hyp("power_p"));qnz = power_nonzero(N,q,t.hyp("power_q"));hnz = power_nonzero(J,h,t.hyp("power_h"))
        zhnz = apply(specialize(t,"mul_ne_zero",z,h),t.hyp("nonzero_z"),hnz)
        zhpnz = apply(specialize(t,"mul_ne_zero",zh,p),zhnz,pnz)
        upper = apply(specialize(t,"positive_order",y,Add(Mul(two,q),Mul(nine,a)),zh,q),zhnz,qnz,field(sandwich,1,3))
        lower_rhs = Add(Mul(y,p),zh)
        lower_nat = _subst(t,registry,"Le(slot,y*p+z*h)",
            _multiplicative_equal(t,Mul(Mul(two,p),zh),Mul(two,zhp)),field(sandwich,2,3))
        lower_nat = _subst(t,registry,"Le(2*((z*h)*p),slot)",EqSym(specialize(t,"mul_one",lower_rhs)),lower_nat)
        lower = apply(specialize(t,"positive_order",two,lower_rhs,one,zhp),specialize(t,"succ_ne_zero",Zero()),zhpnz,lower_nat)
        return witness((b,),conjunction(t.hyp("power_b"),scale,split,pnz,qnz,hnz,zhnz,zhpnz,
            *(field(sandwich,i,3) for i in range(3)),upper,lower))
    return introduce(s,PARAMETERS,("nonzero_z","prefix_value","geometric","power_p","slice","tail_value","whole_value","power_h","power_q","power_a","tail_bound"),lambda t:
        eliminate(t,specialize(t,"power_exists",_numeral(3),Succ(t.term("r"))),("b",),"power_b",chosen))


def prove_supplied_geometric_error(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV084",target=frozen_supplied_geometric_error_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"CV084":lambda s:_root(s,registry)},pins=supplied_geometric_error_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
