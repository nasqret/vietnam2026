"""CV066: majorize the actual finite denominator-cleared atanh polynomial.

For every k construct the CV025 coefficient table of length k+1, its nonzero
denominator d, actual Horner value y at two and p=2^k, with y+2d<=2d*p.
The same table is used throughout. No logarithm identity or limit is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_bounded_horner import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as bounded_registry,bounded_horner_source_pins,
    NAMED_SOURCE as BOUNDED_SOURCE,
)
from sqrt2_power_atanh_coefficients import (
    definition_registry as atanh_registry,atanh_coefficients_source_pins,NAMED_SOURCE as ATANH_SOURCE,
)
from sqrt2_power_atanh_euler import ATANH_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-atanh-majorant-v1"
A = ("ab","ac")
OUTPUTS = ("d",)+A+("y","p")
PREFIX = "NatAtanhPrefix(d,ab,ac,S k)"
BOUND = "NatBoundedPrefix(ab,ac,2*d,S k)"
VALUE = "NatHornerValue(ab,ac,2,S k,y)"
NAMED_SOURCE = "forall k. exists "+" ".join(OUTPUTS)+". ~d=0 /\\ ("+PREFIX+" /\\ (NatZeroBefore(ab,ac,S k,1) /\\ (BetaAt(ab,ac,0,0) /\\ ("+BOUND+" /\\ ("+VALUE+" /\\ (Pow(2,k,p) /\\ Le(y+2*d,(2*d)*p)))))))"
TARGET_SHA256 = "b21b3f67a0aa28eb1456681cada027f47d5323c8f0b7e3c66defa64552756e5d"
HELPER_SOURCES = {
    "entry_bound":"forall d i a. NatAtanhCoefficient(d,i,a) -> Le(a,2*d)",
    "entry_zero":"forall d a. NatAtanhCoefficient(d,0,a) -> a=0",
    "prefix_bound":"forall d ab ac N. NatAtanhPrefix(d,ab,ac,N) -> NatBoundedPrefix(ab,ac,2*d,N)",
    "prefix_head":"forall d ab ac k. "+PREFIX+" -> BetaAt(ab,ac,0,0)",
    "prefix_majorant":"forall d ab ac k. "+PREFIX+" -> exists y p. "+VALUE+" /\\ (Pow(2,k,p) /\\ Le(y+2*d,(2*d)*p))",
}
HELPER_TARGET_SHA256 = {
    "entry_bound":"e14d3284cc68fb2bfdc64f4ee8d20019e0aee8ca88331086e9889141df5c071a",
    "entry_zero":"a4d6eb45cc65d7f056212745507b14caf85aa393cbf70f0b0d9e1a1bc5b73fb0",
    "prefix_bound":"430630898bc996b475b9cf054b27bb94c5fca01d8ec23d915c1914b74c7e3d56",
    "prefix_head":"45a266298c6c55d8ceb2d86f1b3efdafc2f803dc155a2070e76fa2d153519901",
    "prefix_majorant":"887fe3d5a26ab38d58fade428c8185f6fc4d26841d71a567690a76c856db1e48",
}
BOUNDED_ARCHIVE = dict(case="CV065",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-bounded-horner-v1/generation-process.json.gz",
    bytes=29766,sha256="822d7e65bfa4e82a28cab04c361b985e895a1d12349e69c218e1a51f0cb2b9f5",
    raw_bytes=439133,raw_sha256="7849577b72c0b307cd34819ddba5be94dee674cd4f04cb6f434ebf26302c1f87",
    bundle_bytes=240999,bundle_sha256="015481deac61973d996c1014b3c0c9f76bbfd20614546338bc6b86a4be7a41b8",
    nodes=125,root=124,target_ast_sha256="9014d749012734cecddb6aba75ab714b63794d50d28aef611ecc1a9018f2c091")
ARCHIVES = (BOUNDED_ARCHIVE,ATANH_ARCHIVE)
ENDPOINT_SOURCES = {
    "bounded_horner":BOUNDED_SOURCE,"atanh_exists":ATANH_SOURCE,
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "zero_le":"forall a. Le(0,a)","succ_ne_zero":"forall a. ~S a=0",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "one_mul":"forall a. 1*a=a",
}
ENDPOINT_OWNERS = {name:"CV065" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(atanh_exists="CV025",succ_ne_zero="CV025")
HELPER_DEPENDENCIES = {
    "entry_bound":("zero_le","mul_right_mono","one_mul"),
    "entry_zero":("succ_ne_zero",),
    "prefix_bound":("entry_bound",),
    "prefix_head":("beta_exists","entry_zero"),
    "prefix_majorant":("bounded_horner","prefix_head","prefix_bound"),
    "CV066":("atanh_exists","prefix_majorant","prefix_head","prefix_bound"),
}


class AtanhMajorantError(ValueError):
    """Changed actual atanh data or finite denominator-cleared bound."""


def definition_registry():
    result = dict(bounded_registry())
    for name,d in atanh_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise AtanhMajorantError("shared conservative definition mismatch")
        if name not in result and d.stable_id in {v.stable_id for v in result.values()}:
            raise AtanhMajorantError("cross-registry definition id collision")
        result[name] = d
    return MappingProxyType(result)


def frozen_atanh_majorant_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise AtanhMajorantError("CV066 exact finite atanh majorant target changed")
    return target


def source_contract():
    return dict(code="CV066",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_atanh_prefix_constructed=True,same_coefficient_table_throughout=True,
        actual_nonzero_denominator_constructed=True,zero_head_and_coefficient_bound_proved=True,
        actual_horner_value_and_power_constructed=True,inequality="y+2*d<=(2*d)*p; p=2^k",
        arbitrary_supplied_prefix_helper=True,rational_division_transport_claimed=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def atanh_majorant_source_pins():
    result = bounded_horner_source_pins()
    for name,pin in atanh_coefficients_source_pins().items():
        if name in result and result[name]!=pin:
            raise AtanhMajorantError("source pin disagreement")
        result[name] = pin
    expected = {"scripts/sqrt2_power_bounded_horner.py":"c2fc3d532479883717809be952fe2e31ce3b3f8a283f854e1ae59773cd2864bd",
        "scripts/sqrt2_power_atanh_coefficients.py":"f933ef2b4a35fa6bfe67eabb9279b200a27dcb9a32904b1c4b689b8528386abd",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_atanh_majorant.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise AtanhMajorantError("atanh majorant source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _entry_bound(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongS,EqSym,OrElim
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two = Succ(Succ(Zero()))
    def even(t):
        return eliminate(t,t.hyp("even"),("j",),"data",lambda u:
            _subst(u,registry,"Le(slot,2*d)",EqSym(AndElimR(u.hyp("data"))),specialize(u,"zero_le",Mul(two,u.term("d")))))
    def odd(t):
        def chosen(u):
            a,i = u.terms(("a","i"));tj = Mul(two,u.term("j"));one = Succ(Zero())
            index = _chain(instantiate(Axiom("PA4"),tj,Zero()),CongS(instantiate(Axiom("PA3"),tj)),EqSym(AndElimL(u.hyp("data"))))
            bound = apply(specialize(u,"mul_right_mono",one,i,a),witness((tj,),index))
            bound = _subst(u,registry,"Le(slot,i*a)",specialize(u,"one_mul",a),bound)
            return _subst(u,registry,"Le(a,slot)",AndElimR(u.hyp("data")),bound)
        return eliminate(t,t.hyp("odd"),("j",),"data",chosen)
    return introduce(s,("d","i","a"),("coefficient",),lambda t:
        OrElim(t.hyp("coefficient"),even(t.hypothesis("even")),odd(t.hypothesis("odd"))))


def _entry_zero(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,EqSym,OrElim
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        even = t.hypothesis("even");odd = t.hypothesis("odd")
        return OrElim(t.hyp("coefficient"),eliminate(even,even.hyp("even"),("j",),"data",lambda u:AndElimR(u.hyp("data"))),
            eliminate(odd,odd.hyp("odd"),("j",),"data",lambda u:
                BotElim(apply(specialize(u,"succ_ne_zero",Mul(Succ(Succ(Zero())),u.term("j"))),EqSym(AndElimL(u.hyp("data")))))))
    return introduce(s,("d","a"),("coefficient",),finish)


def _prefix_bound(s):
    return introduce(s,("d",)+A+("N",),("prefix",),lambda t:
        introduce(t,("i","a"),("index","value"),lambda u:
            apply(specialize(u,"entry_bound",*u.terms(("d","i","a"))),
                apply(specialize(u,"prefix",*u.terms(("i","a"))),u.hyp("index"),u.hyp("value")))))


def _prefix_head(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,CongS
    from peano_lab.kernel.terms import Zero
    def chosen(t):
        k = t.term("k")
        index = witness((k,),_chain(instantiate(Axiom("PA4"),k,Zero()),CongS(instantiate(Axiom("PA3"),k))))
        coefficient = apply(specialize(t,"prefix",Zero(),t.term("a")),index,t.hyp("value"))
        a0 = apply(specialize(t,"entry_zero",*t.terms(("d","a"))),coefficient)
        return _subst(t,registry,"BetaAt(ab,ac,0,slot)",a0,t.hyp("value"))
    return introduce(s,("d",)+A+("k",),("prefix",),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(A),Zero()),("a",),"value",chosen))


def _prefix_majorant(s):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        return apply(specialize(t,"bounded_horner",*t.terms(A),Mul(Succ(Succ(Zero())),t.term("d")),t.term("k")),
            apply(specialize(t,"prefix_head",*t.terms(("d",)+A+("k",))),t.hyp("prefix")),
            apply(specialize(t,"prefix_bound",*t.terms(("d",)+A),Succ(t.term("k"))),t.hyp("prefix")))
    return introduce(s,("d",)+A+("k",),("prefix",),finish)


def _root(s):
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        table,majorant = t.hyp("table"),t.hyp("majorant")
        prefix = field(table,1,3)
        head = apply(specialize(t,"prefix_head",*t.terms(("d",)+A+("k",))),prefix)
        bound = apply(specialize(t,"prefix_bound",*t.terms(("d",)+A),Succ(t.term("k"))),prefix)
        return witness(t.terms(OUTPUTS),conjunction(field(table,0,3),prefix,field(table,2,3),head,bound,
            field(majorant,0,3),field(majorant,1,3),field(majorant,2,3)))
    return introduce(s,("k",),(),lambda t:
        eliminate(t,specialize(t,"atanh_exists",Succ(t.term("k"))),("d",)+A,"table",lambda u:
            eliminate(u,apply(specialize(u,"prefix_majorant",*u.terms(("d",)+A+("k",))),field(u.hyp("table"),1,3)),("y","p"),"majorant",chosen)))


def prove_atanh_majorant(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV066",target=frozen_atanh_majorant_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"entry_bound":lambda s:_entry_bound(s,registry),"entry_zero":_entry_zero,
            "prefix_bound":_prefix_bound,"prefix_head":lambda s:_prefix_head(s,registry),
            "prefix_majorant":_prefix_majorant,"CV066":_root},
        pins=atanh_majorant_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
