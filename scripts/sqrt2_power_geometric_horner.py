"""CV033: exact finite evaluation of z,2z,2z,... at one third.

Construct H,r,p with the actual Horner trace of length k+1, Pow(3,k,p),
p nonzero and r+z=(2*z)*p. The coefficient pattern is an explicit premise;
linking the constructed composition to this premise is a separate application.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_horner_trace import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as horner_registry,horner_trace_source_pins,
    NAMED_SOURCE as HORNER_SOURCE,HELPER_SOURCES as HORNER_HELPERS,
)
from sqrt2_power_weight_factorials import (
    definition_registry as factorial_registry,weight_factorials_source_pins,
    ENDPOINT_SOURCES as FACTORIAL_ENDPOINTS,
)
from sqrt2_power_normalized_composition import FACTORIAL_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_exponential_weights import ENDPOINT_SOURCES as ARITHMETIC_ENDPOINTS
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive
from sqrt2_power_convolution_unit import _subst

SCHEMA = "sqrt2-power-geometric-horner-v1"
A,H = ("ab","ac"),("hb","hc")


def pattern(length="N"):
    return "forall i a. Lt(i,"+length+") -> BetaAt(ab,ac,i,a) -> ((i=0 /\\ a=z) \\/ (exists j. i=S j /\\ a=2*z))"


def trace(length="N"):
    return "NatScaledHornerTrace(ab,ac,3,"+length+",hb,hc)"


NAMED_SOURCE = "forall ab ac z k. ("+pattern("S k")+") -> exists hb hc r p. "+trace("S k")+" /\\ (BetaAt(hb,hc,S k,r) /\\ (Pow(3,k,p) /\\ (~p=0 /\\ r+z=(2*z)*p)))"
TARGET_SHA256 = "fbb3d37960c61bdda6f6242ac8a1ea3bd5ea98c9d28b11ee26556b39dce16fd6"
HELPER_SOURCES = {
    "pattern_zero":"forall ab ac N z a. ("+pattern()+") -> Lt(0,N) -> BetaAt(ab,ac,0,a) -> a=z",
    "pattern_succ":"forall ab ac N z j a. ("+pattern()+") -> Lt(S j,N) -> BetaAt(ab,ac,S j,a) -> a=2*z",
    "double":"forall z. z+z=2*z",
    "shuffle":"forall h z q p. h+z=(2*z)*q -> p=q*3 -> (3*h+2*z)+z=(2*z)*p",
    "power_nonzero":"forall d. ~d=0 -> forall k p. Pow(d,k,p) -> ~p=0",
    "evaluation":"forall ab ac N hb hc z. "+trace()+" -> ("+pattern()+") -> forall k r p. Le(S k,N) -> BetaAt(hb,hc,S k,r) -> Pow(3,k,p) -> r+z=(2*z)*p",
}
HELPER_TARGET_SHA256 = {
    "pattern_zero":"80ca71ea177452b41ad3d95abf4fc487d3f5e16574b7189641814f579e07c025",
    "pattern_succ":"d4f399c388c8d187258bed6043ac84ede96b3af53a27e75dee18a730ae08f1ed",
    "double":"cd36bfaa5ff0160749574a8ae99a7aa70e2453a9f928e527e717d9a375eeaf8d",
    "shuffle":"b386666aa0bbacee77ee046b9c73692adf2e55ad3fd622422c89312eda5b8dc9",
    "power_nonzero":"de75d189e7ac8f5117a9d035a9b0e917c9448363eebb08c95794a2ee9aa7757b",
    "evaluation":"6f65bc610043b806e128fc9c586972d1a28901499a091f9c33397dce7c26bf2e",
}
HORNER_ARCHIVE = dict(case="CV032",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-trace-v1/generation-process.json.gz",
    bytes=19912,sha256="368fb5737349848206fedf779b5c7202e5c297a760a8e269e157578d6e9430fb",
    raw_bytes=297764,raw_sha256="c9ebb596c996463eff51f18a8faf69f02a756395754505f36d34cfce33a87f46",
    bundle_bytes=175054,bundle_sha256="97f4656c45ac339b593d9cfb83632028e297d6ba9cfc7ef4bd2c7bfe7f066787",
    nodes=107,root=106,target_ast_sha256="ef5c41487529723c8676ac25e7e7972e81abf1f34730285cf1abfaae5b63ce80")
ARCHIVES = (HORNER_ARCHIVE,FACTORIAL_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {name:ARITHMETIC_ENDPOINTS[name] for name in
    ("beta_exists","succ_ne_zero","mul_ne_zero","le_succ","le_refl","one_mul","mul_one","mul_assoc","mul_comm")}
ENDPOINT_SOURCES.update({name:FACTORIAL_ENDPOINTS[name] for name in ("power_exists","power_zero","power_step","le_trans")})
ENDPOINT_SOURCES.update(horner_exists=HORNER_SOURCE,step_value=HORNER_HELPERS["step_value"],
    zero_add="forall a. 0+a=a",add_assoc="forall a b c. (a+b)+c=a+(b+c)",
    mul_succ_left="forall a b. (S a)*b=a*b+b",mul_add="forall a b c. a*(b+c)=a*b+a*c")
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:"CV030" for name in ("power_exists","power_zero","power_step")})
ENDPOINT_OWNERS.update(horner_exists="CV032",step_value="CV032")
HELPER_DEPENDENCIES = {
    "pattern_zero":("succ_ne_zero",),"pattern_succ":("succ_ne_zero",),
    "double":("mul_succ_left","one_mul"),
    "shuffle":("add_assoc","mul_succ_left","mul_add","mul_comm","mul_assoc"),
    "power_nonzero":("power_zero","power_step","succ_ne_zero","mul_ne_zero"),
    "evaluation":("beta_exists","pattern_zero","pattern_succ","step_value","power_zero","power_step","zero_add","double","mul_one","le_succ","le_trans","le_refl","shuffle"),
    "CV033":("horner_exists","beta_exists","power_exists","evaluation","le_refl","power_nonzero","succ_ne_zero"),
}


class GeometricHornerError(ValueError):
    """Changed coefficient premise, exact remainder identity or source data."""


def definition_registry():
    result = dict(horner_registry())
    for name,d in factorial_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise GeometricHornerError("shared Horner/power definition mismatch")
        result[name] = d
    return MappingProxyType(result)


def frozen_geometric_horner_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=4 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise GeometricHornerError("CV033 exact integer evaluation target changed")
    return target


def source_contract():
    return dict(code="CV033",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,coefficient_pattern_required=True,actual_horner_trace_constructed=True,
        actual_nonzero_power_constructed=True,exact_integer_remainder_identity=True,
        zero_scale_allowed=True,new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",composition_witnesses_constructed=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def geometric_horner_source_pins():
    result = horner_trace_source_pins()
    for name,pin in weight_factorials_source_pins().items():
        if name in result and result[name]!=pin:
            raise GeometricHornerError("source pin disagreement")
        result[name] = pin
    expected = {"scripts/sqrt2_power_horner_trace.py":"32feca5a71d2b82367e6321d7a276c8c7de0f0fbf9b97513e22e816f80ee0328",
        "scripts/sqrt2_power_normalized_composition.py":"d2444ad39a22c50a6afbeb5f3ec3b67527c25f2c5985877ec4604dad08790d23",**{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_geometric_horner.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise GeometricHornerError("geometric Horner source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _pattern_zero(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,EqSym,OrElim
    from peano_lab.kernel.terms import Zero
    def finish(t):
        cases = apply(specialize(t,"pattern",Zero(),t.term("a")),t.hyp("bound"),t.hyp("value"))
        other = t.hypothesis("positive")
        positive = eliminate(other,other.hyp("positive"),("j",),"data",lambda u:
            BotElim(apply(specialize(u,"succ_ne_zero",u.term("j")),EqSym(AndElimL(u.hyp("data"))))))
        return OrElim(cases,AndElimR(t.hypothesis("zero").hyp("zero")),positive)
    return introduce(s,A+("N","z","a"),("pattern","bound","value"),finish)


def _pattern_succ(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,OrElim
    from peano_lab.kernel.terms import Succ
    def finish(t):
        cases = apply(specialize(t,"pattern",Succ(t.term("j")),t.term("a")),t.hyp("bound"),t.hyp("value"))
        u = t.hypothesis("zero")
        zero = BotElim(apply(specialize(u,"succ_ne_zero",u.term("j")),AndElimL(u.hyp("zero"))))
        v = t.hypothesis("positive")
        return OrElim(cases,zero,eliminate(v,v.hyp("positive"),("l",),"data",lambda w:AndElimR(w.hyp("data"))))
    return introduce(s,A+("N","z","j","a"),("pattern","bound","value"),finish)


def _double(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    return introduce(s,("z",),(),lambda t:EqSym(_chain(specialize(t,"mul_succ_left",Succ(Zero()),t.term("z")),
        CongAdd(specialize(t,"one_mul",t.term("z")),EqRefl(t.term("z"))))))


def _shuffle(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        h,z,q = t.terms(("h","z","q"))
        two = Succ(Succ(Zero()));three = Succ(two)
        return _chain(specialize(t,"add_assoc",Mul(three,h),Mul(two,z),z),
            CongAdd(EqRefl(Mul(three,h)),EqSym(specialize(t,"mul_succ_left",two,z))),
            EqSym(specialize(t,"mul_add",three,h,z)),CongMul(EqRefl(three),t.hyp("old")),
            specialize(t,"mul_comm",three,Mul(Mul(two,z),q)),specialize(t,"mul_assoc",Mul(two,z),q,three),
            CongMul(EqRefl(Mul(two,z)),EqSym(t.hyp("power"))))
    return introduce(s,("h","z","q","p"),("old","power"),finish)


def _power_nonzero(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Succ,Zero
    def base(t):
        p1 = apply(specialize(t,"power_zero",t.term("d"),Zero(),t.term("p")),EqRefl(Zero()),t.hyp("power"))
        return _subst(t,registry,"~slot=0",EqSym(p1),specialize(t,"succ_ne_zero",Zero()))
    def successor(t):
        def chosen(u):
            old = apply(specialize(u,"IH",u.term("q")),AndElimL(u.hyp("data")))
            product = apply(specialize(u,"mul_ne_zero",*u.terms(("q","d"))),old,u.hyp("nonzero"))
            return _subst(u,registry,"~slot=0",EqSym(AndElimR(u.hyp("data"))),product)
        return eliminate(t,apply(specialize(t,"power_step",*t.terms(("d","k")),Succ(t.term("k")),t.term("p")),EqRefl(Succ(t.term("k"))),t.hyp("power")),("q",),"data",chosen)
    motive = target.body.right.body
    return introduce(s,("d",),("nonzero",),lambda t:Ind(motive,introduce(t,("p",),("power",),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,("p",),("power",),successor))))


def _evaluation(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two,three = Succ(Succ(Zero())),Succ(Succ(Succ(Zero())))
    def base(t):
        def chosen(u):
            z,a,r,p = u.terms(("z","a","r","p"))
            a_z = apply(specialize(u,"pattern_zero",*u.terms(A+("N","z","a"))),u.hyp("pattern"),u.hyp("bound"),u.hyp("coefficient"))
            st = apply(instantiate(AndElimR(u.hyp("trace")),Zero()),u.hyp("bound"))
            value = apply(specialize(u,"step_value",*u.terms(A),three,*u.terms(H),Zero(),Zero(),a,r),
                st,AndElimL(u.hyp("trace")),u.hyp("coefficient"),u.hyp("value"))
            rz = _chain(value,CongAdd(instantiate(Axiom("PA5"),three),EqRefl(a)),specialize(u,"zero_add",a),a_z)
            p1 = apply(specialize(u,"power_zero",three,Zero(),p),EqRefl(Zero()),u.hyp("power"))
            return _chain(CongAdd(rz,EqRefl(z)),specialize(u,"double",z),EqSym(specialize(u,"mul_one",Mul(two,z))),CongMul(EqRefl(Mul(two,z)),EqSym(p1)))
        return eliminate(t,specialize(t,"beta_exists",*t.terms(A),Zero()),("a",),"coefficient",chosen)
    def successor(t):
        def chosen(u):
            k,N,h,r,z = u.terms(("k","N","h","r","z"))
            previous = apply(specialize(u,"le_trans",Succ(k),Succ(Succ(k)),N),
                apply(specialize(u,"le_succ",Succ(k),Succ(k)),specialize(u,"le_refl",Succ(k))),u.hyp("bound"))
            old = apply(specialize(u,"IH",*u.terms(("h","q"))),previous,u.hyp("old_value"),AndElimL(u.hyp("power_data")))
            a2z = apply(specialize(u,"pattern_succ",*u.terms(A+("N","z")),k,u.term("a")),u.hyp("pattern"),u.hyp("bound"),u.hyp("coefficient"))
            st = apply(instantiate(AndElimR(u.hyp("trace")),Succ(k)),u.hyp("bound"))
            value = apply(specialize(u,"step_value",*u.terms(A),three,*u.terms(H),Succ(k),h,u.term("a"),r),st,u.hyp("old_value"),u.hyp("coefficient"),u.hyp("value"))
            rewrite = _chain(value,CongAdd(EqRefl(Mul(three,h)),a2z))
            return _chain(CongAdd(rewrite,EqRefl(z)),apply(specialize(u,"shuffle",*u.terms(("h","z","q","p"))),old,AndElimR(u.hyp("power_data"))))
        power = apply(specialize(t,"power_step",three,t.term("k"),Succ(t.term("k")),t.term("p")),EqRefl(Succ(t.term("k"))),t.hyp("power"))
        return eliminate(t,power,("q",),"power_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H),Succ(u.term("k"))),("h",),"old_value",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(A),Succ(v.term("k"))),("a",),"coefficient",chosen)))
    motive = target
    for _ in range(6):
        motive = motive.body
    motive = motive.right.right.body
    return introduce(s,A+("N",)+H+("z",),("trace","pattern"),lambda t:Ind(motive,
        introduce(t,("r","p"),("bound","value","power"),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,("r","p"),("bound","value","power"),successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL
    from peano_lab.kernel.terms import Succ,Zero
    three = Succ(Succ(Succ(Zero())))
    def chosen(t):
        graph = AndElimL(t.hyp("horner"))
        evaluation = apply(specialize(t,"evaluation",*t.terms(A),Succ(t.term("k")),*t.terms(H+("z",))),graph,t.hyp("pattern"))
        identity = apply(instantiate(evaluation,*t.terms(("k","r","p"))),specialize(t,"le_refl",Succ(t.term("k"))),t.hyp("value"),t.hyp("power"))
        positive = apply(instantiate(apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",Succ(Succ(Zero())))),*t.terms(("k","p"))),t.hyp("power"))
        return witness(t.terms(H+("r","p")),conjunction(graph,t.hyp("value"),t.hyp("power"),positive,identity))
    return introduce(s,A+("z","k"),("pattern",),lambda t:
        eliminate(t,specialize(t,"horner_exists",*t.terms(A),three,Succ(t.term("k"))),H,"horner",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H),Succ(u.term("k"))),("r",),"value",lambda v:
                eliminate(v,specialize(v,"power_exists",three,v.term("k")),("p",),"power",chosen))))


def prove_geometric_horner(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"pattern_zero":_pattern_zero,"pattern_succ":_pattern_succ,"double":_double,"shuffle":_shuffle,
        "power_nonzero":lambda s:_power_nonzero(s,parse_named(HELPER_SOURCES["power_nonzero"],registry=registry),registry),
        "evaluation":lambda s:_evaluation(s,parse_named(HELPER_SOURCES["evaluation"],registry=registry)),"CV033":_root}
    return assemble_mixed_certificate(code="CV033",target=frozen_geometric_horner_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,
        pins=geometric_horner_source_pins,contract=source_contract(),limits=limits,new_induction_count=2)
