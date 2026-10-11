"""CV036: exact denominator scaling when a Horner prefix has a zero tail.

Given actual zero coefficients on [M,M+N), construct the length-M+N trace,
both endpoints and Pow(t,N,p), proving v=p*u. The premise is essential;
zero multiplier and empty lengths are allowed. No rational limit is asserted.
"""
from hashlib import sha256

from sqrt2_power_geometric_horner import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,geometric_horner_source_pins,
    ENDPOINT_SOURCES as GEOMETRIC_ENDPOINTS,HORNER_ARCHIVE,FACTORIAL_ARCHIVE,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive
from sqrt2_power_convolution_unit import _subst

SCHEMA = "sqrt2-power-horner-zero-tail-v1"
A,H = ("ab","ac"),("hb","hc")
PARAMETERS = A+("t","M","N")
OUTPUTS = H+("u","v","p")
TRACE = "NatScaledHornerTrace(ab,ac,t,M+N,hb,hc)"
ZERO_TAIL = "forall j a. Lt(j,N) -> BetaAt(ab,ac,M+j,a) -> a=0"
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". ("+ZERO_TAIL+") -> exists "+" ".join(OUTPUTS)+". "+TRACE+" /\\ (BetaAt(hb,hc,M,u) /\\ (BetaAt(hb,hc,M+N,v) /\\ (Pow(t,N,p) /\\ v=p*u)))"
TARGET_SHA256 = "ba1d797f495177c7c2b6f504d04e3cb81acb6460d86b60a22e46f3369a8a78d9"
HELPER_SOURCES = {
    "shift_bound":"forall M k N. Lt(k,N) -> Lt(M+k,M+N)",
    "zero_tail":"forall "+" ".join(PARAMETERS+H+("u",))+". "+TRACE+" -> BetaAt(hb,hc,M,u) -> ("+ZERO_TAIL+") -> forall k v p. Le(k,N) -> BetaAt(hb,hc,M+k,v) -> Pow(t,k,p) -> v=p*u",
}
HELPER_TARGET_SHA256 = {
    "shift_bound":"3d8886715f77e54984962e85b495f7e237809502bcc8bf2c4da646cc93759a71",
    "zero_tail":"3cc9a1e8dd9b89115d16d4de418ed6a129125101623d534d51da692996c31923",
}
ARCHIVES = (HORNER_ARCHIVE,FACTORIAL_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {name:GEOMETRIC_ENDPOINTS[name] for name in (
    "beta_exists","le_refl","le_succ","le_trans","mul_assoc","mul_comm","one_mul",
    "power_exists","power_zero","power_step","horner_exists","step_value","add_assoc")}
ENDPOINT_SOURCES.update(beta_unique="forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    add_comm="forall a b. a+b=b+a")
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:"CV030" for name in ("power_exists","power_zero","power_step")})
ENDPOINT_OWNERS.update(horner_exists="CV032",step_value="CV032")
HELPER_DEPENDENCIES = {
    "shift_bound":("add_assoc","add_comm"),
    "zero_tail":("beta_unique","power_zero","one_mul","beta_exists","power_step","le_refl","le_succ","le_trans","shift_bound","step_value","mul_assoc","mul_comm"),
    "CV036":("horner_exists","beta_exists","power_exists","zero_tail","le_refl"),
}


class HornerZeroTailError(ValueError):
    """Changed zero-coefficient premise, exact scaling or actual proof source."""


def frozen_horner_zero_tail_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerZeroTailError("CV036 exact constructed padding target changed")
    return target


def source_contract():
    return dict(code="CV036",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,actual_zero_tail_required=True,actual_trace_and_endpoints_constructed=True,
        actual_power_constructed=True,exact_padding_scale_proved=True,
        zero_multiplier_and_empty_lengths_allowed=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        multiplication_evaluation_identity=False,analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def horner_zero_tail_source_pins():
    result = geometric_horner_source_pins()
    expected = {"scripts/sqrt2_power_geometric_horner.py":"6179fa42c4437ed53db78fdc4f806d281d4774b58544150c7007dcfa3b656adc",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_horner_zero_tail.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerZeroTailError("Horner padding source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _shift_bound(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain,_additive_equal
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongS,EqRefl,EqSym
    from peano_lab.kernel.terms import Add
    def chosen(t):
        M,k,h = t.terms(("M","k","h"))
        equality = _chain(instantiate(Axiom("PA4"),h,Add(M,k)),
            CongS(_additive_equal(t,Add(h,Add(M,k)),Add(M,Add(h,k)))),
            EqSym(instantiate(Axiom("PA4"),M,Add(h,k))),
            CongAdd(EqRefl(M),EqSym(instantiate(Axiom("PA4"),h,k))),CongAdd(EqRefl(M),t.hyp("gap")))
        return witness((h,),equality)
    return introduce(s,("M","k","N"),("bound",),lambda t:eliminate(t,t.hyp("bound"),("h",),"gap",chosen))


def _zero_tail(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def base(t):
        entry = _subst(t,registry,"BetaAt(hb,hc,slot,v)",instantiate(Axiom("PA3"),t.term("M")),t.hyp("value"))
        vu = apply(specialize(t,"beta_unique",*t.terms(H+("M","v","u"))),entry,t.hyp("initial"))
        p1 = apply(specialize(t,"power_zero",t.term("t"),Zero(),t.term("p")),EqRefl(Zero()),t.hyp("power"))
        return _chain(vu,EqSym(specialize(t,"one_mul",t.term("u"))),CongMul(EqSym(p1),EqRefl(t.term("u"))))
    def successor(t):
        def chosen(u):
            k,N,M,t0,h = u.terms(("k","N","M","t","h"))
            earlier = apply(specialize(u,"le_trans",k,Succ(k),N),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            old = apply(specialize(u,"IH",*u.terms(("h","q"))),earlier,u.hyp("old_value"),AndElimL(u.hyp("power_data")))
            a0 = apply(specialize(u,"zeros",*u.terms(("k","a"))),u.hyp("bound"),u.hyp("coefficient"))
            shifted = apply(specialize(u,"shift_bound",M,k,N),u.hyp("bound"))
            step = apply(instantiate(AndElimR(u.hyp("trace")),Add(M,k)),shifted)
            entry = _subst(u,registry,"BetaAt(hb,hc,slot,v)",instantiate(Axiom("PA4"),M,k),u.hyp("value"))
            value = apply(specialize(u,"step_value",*u.terms(A),t0,*u.terms(H),Add(M,k),h,*u.terms(("a","v"))),
                step,u.hyp("old_value"),u.hyp("coefficient"),entry)
            return _chain(value,CongAdd(EqRefl(Mul(t0,h)),a0),instantiate(Axiom("PA3"),Mul(t0,h)),
                CongMul(EqRefl(t0),old),EqSym(specialize(u,"mul_assoc",t0,*u.terms(("q","u")))),
                CongMul(specialize(u,"mul_comm",t0,u.term("q")),EqRefl(u.term("u"))),
                CongMul(EqSym(AndElimR(u.hyp("power_data"))),EqRefl(u.term("u"))))
        power = apply(specialize(t,"power_step",*t.terms(("t","k")),Succ(t.term("k")),t.term("p")),EqRefl(Succ(t.term("k"))),t.hyp("power"))
        return eliminate(t,power,("q",),"power_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H),Add(u.term("M"),u.term("k"))),("h",),"old_value",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(A),Add(v.term("M"),v.term("k"))),("a",),"coefficient",chosen)))
    motive = target
    for _ in PARAMETERS+H+("u",):
        motive = motive.body
    motive = motive.right.right.right.body
    return introduce(s,PARAMETERS+H+("u",),("trace","initial","zeros"),lambda t:Ind(motive,
        introduce(t,("v","p"),("bound","value","power"),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,("v","p"),("bound","value","power"),successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL
    from peano_lab.kernel.terms import Add
    def chosen(t):
        graph = AndElimL(t.hyp("horner"))
        invariant = apply(specialize(t,"zero_tail",*t.terms(PARAMETERS+H+("u",))),graph,t.hyp("initial"),t.hyp("zeros"))
        equal = apply(instantiate(invariant,*t.terms(("N","v","p"))),specialize(t,"le_refl",t.term("N")),t.hyp("value"),t.hyp("power"))
        return witness(t.terms(OUTPUTS),conjunction(graph,t.hyp("initial"),t.hyp("value"),t.hyp("power"),equal))
    return introduce(s,PARAMETERS,("zeros",),lambda t:
        eliminate(t,specialize(t,"horner_exists",*t.terms(A+("t",)),Add(t.term("M"),t.term("N"))),H,"horner",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H+("M",))),("u",),"initial",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(H),Add(v.term("M"),v.term("N"))),("v",),"value",lambda w:
                    eliminate(w,specialize(w,"power_exists",*w.terms(("t","N"))),("p",),"power",chosen)))))


def prove_horner_zero_tail(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"shift_bound":_shift_bound,"zero_tail":lambda s:_zero_tail(s,parse_named(HELPER_SOURCES["zero_tail"],registry=registry),registry),"CV036":_root}
    return assemble_mixed_certificate(code="CV036",target=frozen_horner_zero_tail_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,
        pins=horner_zero_tail_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
