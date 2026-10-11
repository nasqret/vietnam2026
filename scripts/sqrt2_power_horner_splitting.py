"""CV062: exact Horner splitting with a constructed genuine shifted tail.

Construct x for the first M entries, y for the next N entries, z for the whole
prefix and p=t^N. Prove z=p*x+y, with all computation witnesses retained.
No coefficient is assumed zero and no limit or subtraction is used.
"""
from hashlib import sha256

from sqrt2_power_full_composition_evaluation import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,full_composition_evaluation_source_pins,
)
from sqrt2_power_horner_zero_tail import ENDPOINT_SOURCES as TAIL_ENDPOINTS,HELPER_SOURCES as TAIL_HELPERS
from sqrt2_power_horner_prefix_transport import HELPER_SOURCES as TRANSPORT_HELPERS
from sqrt2_power_natural_fubini import HELPER_SOURCES as FUBINI_HELPERS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-horner-splitting-v1"
A,B,HA,HB = ("ab","ac"),("bb","bc"),("ahb","ahc"),("bhb","bhc")
PARAMETERS = A+("t","M","N")
OUTPUTS = B+("x","y","z","p")
FIXED = A+B+("t","M","N")+HA+HB+("x",)
SLICE = "NatAffineSlice(ab,ac,M,1,bb,bc,N)"
TRACE_A = "NatScaledHornerTrace(ab,ac,t,M+N,ahb,ahc)"
TRACE_B = "NatScaledHornerTrace(bb,bc,t,N,bhb,bhc)"
ALL_PREFIXES = "forall k h g p. Le(k,N) -> BetaAt(ahb,ahc,M+k,h) -> BetaAt(bhb,bhc,k,g) -> Pow(t,k,p) -> h=p*x+g"
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". exists "+" ".join(OUTPUTS)+". "+SLICE+" /\\ (NatHornerValue(ab,ac,t,M,x) /\\ (NatHornerValue(bb,bc,t,N,y) /\\ (NatHornerValue(ab,ac,t,M+N,z) /\\ (Pow(t,N,p) /\\ z=p*x+y))))"
TARGET_SHA256 = "9cde54938675644bbc152c11b3e0270bf4ac303df68a8275b2e5ab6341e8f467"
HELPER_SOURCES = {"all_prefixes":"forall "+" ".join(FIXED)+". "+SLICE+" -> "+TRACE_A+" -> BetaAt(ahb,ahc,M,x) -> "+TRACE_B+" -> "+ALL_PREFIXES}
HELPER_TARGET_SHA256 = {"all_prefixes":"a9f4060bc5016322d5fe8523d63c2c8ab5708c87bdc192a10907d5da2571edf0"}
COMPOSITION_ARCHIVE = dict(case="CV061",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-full-composition-evaluation-v1/generation-process.json.gz",
    bytes=78304,sha256="f0ee0cb3c6f84f5c03b51922449be39096311025112681ce19bb7ee3c5a4ac14",
    raw_bytes=2161642,raw_sha256="90362c4a43f84b35dc254e53ad2ed6e921f43e1dbf4c6c105fffabf9463a342c",
    bundle_bytes=1315237,bundle_sha256="101556adbd46ec693ecb3f630be9b7a5471bb14b5135ef20121d61b54b2161dd",
    nodes=276,root=275,target_ast_sha256="574be3227d697f0533ee581f7baa664dcfca27230214e8992f1bab97fe4e3aaf")
ARCHIVES = (COMPOSITION_ARCHIVE,)
ENDPOINT_SOURCES = {
    **{name:TAIL_ENDPOINTS[name] for name in ("beta_exists","beta_unique","le_refl","le_succ","le_trans","mul_assoc","mul_comm","one_mul","power_zero","power_step","power_exists","horner_exists","step_value","add_assoc")},
    "add_comm":"forall a b. a+b=b+a","mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "slice_exists":FUBINI_HELPERS["slice_exists"],"shift_bound":TAIL_HELPERS["shift_bound"],
    "trace_transport":TRANSPORT_HELPERS["transport"],
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {
    "all_prefixes":("beta_exists","beta_unique","power_zero","power_step","one_mul","le_refl","le_succ","le_trans","shift_bound","step_value","mul_add","mul_assoc","mul_comm","add_assoc"),
    "CV062":("slice_exists","horner_exists","beta_exists","power_exists","trace_transport","add_comm","le_refl","all_prefixes"),
}


class HornerSplittingError(ValueError):
    """Changed actual shifted tail, split indices or explicit scaling."""


def frozen_horner_splitting_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerSplittingError("CV062 exact constructed splitting target changed")
    return target


def source_contract():
    return dict(code="CV062",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_shifted_tail_constructed=True,actual_prefix_tail_and_whole_values_constructed=True,
        actual_scaling_power_constructed=True,identity="z=p*x+y",power="p=t^N",
        arbitrary_coefficients_and_split_lengths=True,zero_multiplier_and_empty_lengths_allowed=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",tail_bound_claimed=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def horner_splitting_source_pins():
    result = full_composition_evaluation_source_pins()
    expected = {"scripts/sqrt2_power_full_composition_evaluation.py":"1f072083655a535b2116b2e6f7dcac7c5459fb83e15899b485347b456bb6f544",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_horner_splitting.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerSplittingError("splitting source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _all_prefixes(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def base(t):
        moved = _subst(t,registry,"BetaAt(ahb,ahc,slot,h)",instantiate(Axiom("PA3"),t.term("M")),t.hyp("full_value"))
        hx = apply(specialize(t,"beta_unique",*t.terms(HA+("M","h","x"))),moved,t.hyp("initial"))
        g0 = apply(specialize(t,"beta_unique",*t.terms(HB),Zero(),t.term("g"),Zero()),t.hyp("tail_value"),AndElimL(t.hyp("tail_trace")))
        p1 = apply(specialize(t,"power_zero",t.term("t"),Zero(),t.term("p")),EqRefl(Zero()),t.hyp("power"))
        right = _chain(CongAdd(CongMul(p1,EqRefl(t.term("x"))),g0),instantiate(Axiom("PA3"),Mul(Succ(Zero()),t.term("x"))),specialize(t,"one_mul",t.term("x")))
        return _chain(hx,EqSym(right))
    def successor(t):
        def chosen(u):
            t0,M,N,k,x,q,h0,g0,a = u.terms(("t","M","N","k","x","q","h0","g0","a"))
            earlier = apply(specialize(u,"le_trans",k,Succ(k),N),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            old = apply(specialize(u,"IH",*u.terms(("h0","g0","q"))),earlier,u.hyp("old_full"),u.hyp("old_tail"),AndElimL(u.hyp("power_data")))
            coefficient = apply(specialize(u,"slice",*u.terms(("k","a"))),u.hyp("bound"),u.hyp("coefficient"))
            coefficient = _subst(u,registry,"BetaAt(ab,ac,slot,a)",CongAdd(EqRefl(M),specialize(u,"one_mul",k)),coefficient)
            full_bound = apply(specialize(u,"shift_bound",M,k,N),u.hyp("bound"))
            full_step = apply(instantiate(AndElimR(u.hyp("full_trace")),Add(M,k)),full_bound)
            current = _subst(u,registry,"BetaAt(ahb,ahc,slot,h)",instantiate(Axiom("PA4"),M,k),u.hyp("full_value"))
            full = apply(specialize(u,"step_value",*u.terms(A),t0,*u.terms(HA),Add(M,k),h0,a,u.term("h")),full_step,u.hyp("old_full"),coefficient,current)
            tail_step = apply(instantiate(AndElimR(u.hyp("tail_trace")),k),u.hyp("bound"))
            tail = apply(specialize(u,"step_value",*u.terms(B),t0,*u.terms(HB),k,g0,a,u.term("g")),tail_step,u.hyp("old_tail"),u.hyp("coefficient"),u.hyp("tail_value"))
            return _chain(full,CongAdd(CongMul(EqRefl(t0),old),EqRefl(a)),
                CongAdd(specialize(u,"mul_add",t0,Mul(q,x),g0),EqRefl(a)),
                specialize(u,"add_assoc",Mul(t0,Mul(q,x)),Mul(t0,g0),a),
                CongAdd(EqSym(specialize(u,"mul_assoc",t0,q,x)),EqSym(tail)),
                CongAdd(CongMul(specialize(u,"mul_comm",t0,q),EqRefl(x)),EqRefl(u.term("g"))),
                CongAdd(CongMul(EqSym(AndElimR(u.hyp("power_data"))),EqRefl(x)),EqRefl(u.term("g"))))
        power = apply(specialize(t,"power_step",t.term("t"),t.term("k"),Succ(t.term("k")),t.term("p")),EqRefl(Succ(t.term("k"))),t.hyp("power"))
        return eliminate(t,power,("q",),"power_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(HA),Add(*u.terms(("M","k")))),("h0",),"old_full",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(HB+("k",))),("g0",),"old_tail",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(B+("k",))),("a",),"coefficient",chosen))))
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.right.right.right.right.body
    return introduce(s,FIXED,("slice","full_trace","initial","tail_trace"),lambda t:Ind(motive,
        introduce(t,("h","g","p"),("bound","full_value","tail_value","power"),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,("h","g","p"),("bound","full_value","tail_value","power"),successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndIntro
    from peano_lab.kernel.terms import Add,Succ,Zero
    def chosen(t):
        M,N = t.terms(("M","N"));full = Add(M,N)
        order = witness((N,),specialize(t,"add_comm",N,M))
        same = introduce(t,("i","a"),("bound","entry"),lambda u:u.hyp("entry"))
        short_trace = apply(specialize(t,"trace_transport",*t.terms(A+A+("t",)),M,full,*t.terms(HA)),order,same,AndElimL(t.hyp("full_horner")))
        invariant = apply(specialize(t,"all_prefixes",*t.terms(FIXED)),t.hyp("slice"),AndElimL(t.hyp("full_horner")),t.hyp("prefix_value"),AndElimL(t.hyp("tail_horner")))
        identity = apply(instantiate(invariant,*t.terms(("N","z","y","p"))),specialize(t,"le_refl",N),t.hyp("whole_value"),t.hyp("tail_value"),t.hyp("power"))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("slice"),
            witness(t.terms(HA),AndIntro(short_trace,t.hyp("prefix_value"))),
            witness(t.terms(HB),AndIntro(AndElimL(t.hyp("tail_horner")),t.hyp("tail_value"))),
            witness(t.terms(HA),AndIntro(AndElimL(t.hyp("full_horner")),t.hyp("whole_value"))),t.hyp("power"),identity))
    return introduce(s,PARAMETERS,(),lambda t:
        eliminate(t,specialize(t,"slice_exists",*t.terms(A+("M",)),Succ(Zero()),t.term("N")),B,"slice",lambda u:
            eliminate(u,specialize(u,"horner_exists",*u.terms(A+("t",)),Add(*u.terms(("M","N")))),HA,"full_horner",lambda v:
                eliminate(v,specialize(v,"horner_exists",*v.terms(B+("t","N"))),HB,"tail_horner",lambda w:
                    eliminate(w,specialize(w,"beta_exists",*w.terms(HA+("M",))),("x",),"prefix_value",lambda a:
                        eliminate(a,specialize(a,"beta_exists",*a.terms(HB+("N",))),("y",),"tail_value",lambda b:
                            eliminate(b,specialize(b,"beta_exists",*b.terms(HA),Add(*b.terms(("M","N")))),("z",),"whole_value",lambda c:
                                eliminate(c,specialize(c,"power_exists",*c.terms(("t","N"))),("p",),"power",chosen))))))))


def prove_horner_splitting(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV062",target=frozen_horner_splitting_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"all_prefixes":lambda s:_all_prefixes(s,parse_named(HELPER_SOURCES["all_prefixes"],registry=registry),registry),"CV062":_root},
        pins=horner_splitting_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
