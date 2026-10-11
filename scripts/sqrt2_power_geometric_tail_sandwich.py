"""CV083: exact natural-arithmetic sandwich from a geometric prefix and tail.

The finite split y=b*r+u and geometric formula r+z=2*z*p, with h=p*b,
give y+z*b=2*z*h+u. A supplied tail bound then bounds the normalized whole
on both sides of two. Nonzero denominators and analytic interpretation are
separate obligations; no division or cancellation occurs here.
"""
from hashlib import sha256

from sqrt2_power_full_composition_evaluation import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,full_composition_evaluation_source_pins,conjoin,
)
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE
from sqrt2_power_quadratic_height import _chain,_additive_equal
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-geometric-tail-sandwich-v1"
PARAMETERS = ("r","z","p","b","y","u","h","q","a")
BALANCE = "y+z*b=(2*z)*h+u"
UPPER = "Le(y*q,(2*q+9*a)*(z*h))"
LOWER = "Le((2*p)*(z*h),y*p+z*h)"
PREMISES = ("r+z=(2*z)*p","y=b*r+u","h=p*b","Le(u*q,(9*a)*(z*h))")
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> "+conjoin((BALANCE,UPPER,LOWER))
TARGET_SHA256 = "6ab738597b29754dfe8c2ecd8edd19ed02b665f859a9b263e2eb80903c75afbd"
HELPER_SOURCES = {
    "balance":"forall r z p b y u h. "+" -> ".join(PREMISES[:3]+(BALANCE,)),
    "upper":"forall y z b h u q a. "+BALANCE+" -> "+PREMISES[3]+" -> "+UPPER,
    "lower":"forall y z b h u p. "+BALANCE+" -> h=p*b -> "+LOWER,
}
HELPER_TARGET_SHA256 = {"balance":"b7546ba54e3689ae5ecca66d2b04f1393b69004499beab87ee893cc2413f637e",
    "upper":"1a9866d1c1084af8ec8043644b0c0aa51c1f39cd43d49495c36112831b3ecd0d",
    "lower":"ad62db8c1a568fc2ded7c3f54538ecca25a8fd7196ccc9a5d4273d0a40771261"}
ARCHIVES = (COMPOSITION_ARCHIVE,)
ENDPOINT_SOURCES = {
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)","add_comm":"forall a b. a+b=b+a",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c","add_mul":"forall a b c. (a+b)*c=a*c+b*c",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {
    "balance":("add_assoc","add_comm","mul_assoc","mul_comm","mul_add"),
    "upper":("add_assoc","add_comm","mul_assoc","mul_comm","add_mul"),
    "lower":("add_comm","mul_assoc","mul_comm","add_mul"),
    "CV083":("balance","upper","lower"),
}


class GeometricTailSandwichError(ValueError):
    """Changed finite identities or the two exact denominator-cleared bounds."""


def frozen_geometric_tail_sandwich_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=9 or len(premises)!=4 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise GeometricTailSandwichError("CV083 exact geometric-tail arithmetic changed")
    return target


def source_contract():
    return dict(code="CV083",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,supplied_finite_geometric_split_and_scale_identities_required=True,
        supplied_natural_tail_bound_required=True,exact_balance=BALANCE,
        denominator_cleared_upper=UPPER,denominator_cleared_lower=LOWER,
        all_natural_zero_cases_allowed=True,no_division_or_cancellation=True,
        deterministic_additive_and_multiplicative_reassociation=True,
        actual_horner_or_power_witnesses_constructed=False,rational_denominator_validity_claimed=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def geometric_tail_sandwich_source_pins():
    result = full_composition_evaluation_source_pins()
    expected = {"scripts/sqrt2_power_full_composition_evaluation.py":"1f072083655a535b2116b2e6f7dcac7c5459fb83e15899b485347b456bb6f544",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_geometric_tail_sandwich.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise GeometricTailSandwichError("geometric-tail source or actual arithmetic archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _numeral(n):
    from peano_lab.kernel.terms import Succ,Zero
    value = Zero()
    for _ in range(n):
        value = Succ(value)
    return value


def _balance(s):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        r,z,p,b,y,u,h = t.terms(("r","z","p","b","y","u","h"));two = _numeral(2)
        br,bz = Mul(b,r),Mul(b,z);zz = Mul(two,z)
        return _chain(CongAdd(t.hyp("whole"),EqRefl(Mul(z,b))),
            CongAdd(EqRefl(Add(br,u)),specialize(t,"mul_comm",z,b)),
            _additive_equal(t,Add(Add(br,u),bz),Add(Add(br,bz),u)),
            CongAdd(EqSym(specialize(t,"mul_add",b,r,z)),EqRefl(u)),
            CongAdd(CongMul(EqRefl(b),t.hyp("geometric")),EqRefl(u)),
            CongAdd(_multiplicative_equal(t,Mul(b,Mul(zz,p)),Mul(zz,Mul(p,b))),EqRefl(u)),
            CongAdd(CongMul(EqRefl(zz),EqSym(t.hyp("scale"))),EqRefl(u)))
    return introduce(s,("r","z","p","b","y","u","h"),("geometric","whole","scale"),finish)


def _upper(s):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def chosen(t):
        y,z,b,h,u,q,a,g = t.terms(("y","z","b","h","u","q","a","g"))
        two,nine = _numeral(2),_numeral(9);zb,zh = Mul(z,b),Mul(z,h)
        B,uq,yq,zbq = Mul(Mul(two,z),h),Mul(u,q),Mul(y,q),Mul(zb,q)
        gap = Add(zbq,g);a9 = Mul(nine,a);q2 = Mul(two,q)
        equation = _chain(_additive_equal(t,Add(gap,yq),Add(g,Add(yq,zbq))),
            CongAdd(EqRefl(g),EqSym(specialize(t,"add_mul",y,zb,q))),
            CongAdd(EqRefl(g),CongMul(t.hyp("balance"),EqRefl(q))),
            CongAdd(EqRefl(g),specialize(t,"add_mul",B,u,q)),
            _additive_equal(t,Add(g,Add(Mul(B,q),uq)),Add(Mul(B,q),Add(g,uq))),
            CongAdd(EqRefl(Mul(B,q)),t.hyp("gap")),
            CongAdd(_multiplicative_equal(t,Mul(B,q),Mul(q2,zh)),EqRefl(Mul(a9,zh))),
            EqSym(specialize(t,"add_mul",q2,a9,zh)))
        return witness((gap,),equation)
    return introduce(s,("y","z","b","h","u","q","a"),("balance","bound"),lambda t:
        eliminate(t,t.hyp("bound"),("g",),"gap",chosen))


def _lower(s):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        y,z,b,h,u,p = t.terms(("y","z","b","h","u","p"));two = _numeral(2)
        B,zh,zb,up,yp = Mul(Mul(two,z),h),Mul(z,h),Mul(z,b),Mul(u,p),Mul(y,p)
        lower = Mul(Mul(two,p),zh)
        equation = _chain(CongAdd(EqRefl(up),_multiplicative_equal(t,lower,Mul(B,p))),
            specialize(t,"add_comm",up,Mul(B,p)),EqSym(specialize(t,"add_mul",B,u,p)),
            CongMul(EqSym(t.hyp("balance")),EqRefl(p)),specialize(t,"add_mul",y,zb,p),
            CongAdd(EqRefl(yp),_multiplicative_equal(t,Mul(zb,p),Mul(z,Mul(p,b)))),
            CongAdd(EqRefl(yp),CongMul(EqRefl(z),EqSym(t.hyp("scale")))))
        return witness((up,),equation)
    return introduce(s,("y","z","b","h","u","p"),("balance","scale"),finish)


def _root(s):
    def finish(t):
        balance = apply(specialize(t,"balance",*t.terms(PARAMETERS[:7])),t.hyp("geometric"),t.hyp("whole"),t.hyp("scale"))
        upper = apply(specialize(t,"upper",*t.terms(("y","z","b","h","u","q","a"))),balance,t.hyp("tail_bound"))
        lower = apply(specialize(t,"lower",*t.terms(("y","z","b","h","u","p"))),balance,t.hyp("scale"))
        return conjunction(balance,upper,lower)
    return introduce(s,PARAMETERS,("geometric","whole","scale","tail_bound"),finish)


def prove_geometric_tail_sandwich(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV083",target=frozen_geometric_tail_sandwich_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"balance":_balance,"upper":_upper,"lower":_lower,"CV083":_root},
        pins=geometric_tail_sandwich_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
