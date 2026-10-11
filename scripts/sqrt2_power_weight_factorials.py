"""CV030: interpret terminal-one weights by actual factorials and powers.

Construct W,w0,f,p with Factorial(N,f), Pow(d,N,p), w0=f*p and
(w[j]*j!)*d^j=w0 for every j<=N. The equality holds also for d=0.
Nonvanishing remains a separate consequence with its nonzero-d premise.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exponential_weights import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as weights_registry,
    exponential_weights_source_pins,NAMED_SOURCE as WEIGHTS_SOURCE,positive,
    ENDPOINT_SOURCES as WEIGHT_ENDPOINTS,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-weight-factorials-v1"
W = ("wb","wc")
WEIGHTS = "NatExpWeightTable(d,N,wb,wc)"
INVARIANT = "forall j w f p. Le(j,N) -> BetaAt(wb,wc,j,w) -> Factorial(j,f) -> Pow(d,j,p) -> (w*f)*p=w0"
NAMED_SOURCE = "forall d N. exists wb wc w0 f p. "+WEIGHTS+" /\\ (("+positive(W)+") /\\ (BetaAt(wb,wc,0,w0) /\\ (Factorial(N,f) /\\ (Pow(d,N,p) /\\ (w0=f*p /\\ ("+INVARIANT+"))))))"
TARGET_SHA256 = "7416c0350bc9ea0e640eccd8e16eeb667dc7c4ae78dfb37bc2abd3442cdaa923"
HELPER_SOURCES = {
    "shuffle":"forall w f p j d. (w*(f*j))*(p*d)=(((j*d)*w)*f)*p",
    "invariant":"forall d N wb wc w0. "+WEIGHTS+" -> BetaAt(wb,wc,0,w0) -> "+INVARIANT,
}
HELPER_TARGET_SHA256 = {
    "shuffle":"22ac4ad46f4a8d831418da4ea5966f5fce3fde13e6009f6fcc7468dcc85ae24b",
    "invariant":"8ad5ef6c8e7ecca4d3fa5fd16ca5ae7dc4cbb50395e3574401d9fb4a7e105a0f",
}
EXISTING_DEFINITIONS = {
    "Product":("PD0014","0c80640a44f6aa5891ef273b1e877e98eeac9eac1905294ea2afc48b7888fad6"),
    "Range":("PD0018","6c310db01f61726e99639fd6043cc7fd524932b7215a046f8798c82a377f2ca6"),
    "Repeat":("PD0019","cc4b13cedf42cae46d24a19cd9d8f38d7fb0fef6139087fdb4c4c262e4955096"),
    "Pow":("PD0020","7d41c5fb594f69e8b48825bdf74fd23ab031a03290a2a5bc42e89bb89fa2bc5f"),
    "Factorial":("PD0023","d6d7019304f48e82ba168a0c6218ec523775b4563a2504dab3f6d17d88c8b104"),
}
LUCAS_ARCHIVE = dict(case="lucas-factorial-v1",format="raw-canonical",
    path="research/arithmetic-library/artifacts/lucas-proof-bundle-v1.json",
    bytes=1103202,sha256="02b1eef360dce55f0156bda2029e64567b8b83b5d58833d6c4f8695ab8d41832",
    nodes=213,root=212,target_ast_sha256="0b3ad61d473c448d7d0c7ff2cdcec2323167825451a61377576e76ef6d215444")
POWER_ARCHIVE = dict(case="QF005",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-bounded-quadratic-product-v1/generation-process.json.gz",
    bytes=132996,sha256="c0786528662b9bd2ade0652029011f1b05d12b9521150c35e97e2e81e05d9388",
    raw_bytes=5638528,raw_sha256="73b6cc6c1cc779d69fe7fc285148607edd5b8901b03b7e64809c05fa96d289f4",
    bundle_bytes=3513591,bundle_sha256="c46933a920ba23989841a3f8e243c32c16a127b9a15cf699cd8d4b4ab448bad0",
    nodes=297,root=296,target_ast_sha256="dcb0b757df5bea77acb675edba870bb7cc99be0a5f700ee1782c1f55f324ec14")
POWER_LAWS_ARCHIVE = dict(case="QH002",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-quadratic-trace-height-v1/generation-process.json.gz",
    bytes=13328,sha256="c1f1f6eae3e44c2a5ecb020001d4941571a7f42d3e5c41297ca3b2ccad9ba47e",
    raw_bytes=240236,raw_sha256="1e273e99d467af646c18b20a2be12e1a3da6c155bd9fafef57a9e81d3e8cb5a5",
    bundle_bytes=141562,bundle_sha256="080feebc1b7dcc21e09c4d259e5922341b0f4267f9df0e6b52fa2135c7f70ea2",
    nodes=41,root=40,target_ast_sha256="e68c7893269115ba0b6b6505c3974c336b5fb98db8d47c2d3ef227003f8a388c")
WEIGHTS_ARCHIVE = dict(case="CV022",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-exponential-weights-v1/generation-process.json.gz",
    bytes=20252,sha256="a87619923985c88f1c822641495e8643a21e348d760223d273eced922c9e493c",
    raw_bytes=296689,raw_sha256="063dd5b87d8f1780bca63c4c80cca17dbbaf4581a72ebbb72886354779349c23",
    bundle_bytes=175040,bundle_sha256="e94cd7dab31d292ec52a9fff9ca85a05f17b5ba0aac7c396fa8c25c449b7b998",
    nodes=108,root=107,target_ast_sha256="67f4d5cffffb0e5b5dd1f559eb6b6d8cd2dbb5ac23bdeb79d580326b4cf5a880")
ARCHIVES = (LUCAS_ARCHIVE,POWER_ARCHIVE,POWER_LAWS_ARCHIVE,WEIGHTS_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:WEIGHT_ENDPOINTS[name] for name in ("mul_assoc","mul_comm","mul_one","one_mul","beta_exists","beta_unique","le_refl","le_succ")},
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "factorial_exists":"forall n. exists f. Factorial(n,f)",
    "factorial_zero":"forall n f. n=0 -> Factorial(n,f) -> f=1",
    "factorial_step":"forall n sn f. sn=S n -> Factorial(sn,f) -> exists g. Factorial(n,g) /\\ f=g*(S n)",
    "power_exists":"forall d n. exists p. Pow(d,n,p)",
    "power_zero":"forall d n p. n=0 -> Pow(d,n,p) -> p=1",
    "power_step":"forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d",
    "weights_exists":WEIGHTS_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV022" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(factorial_exists="lucas-factorial-v1",factorial_zero="lucas-factorial-v1",factorial_step="lucas-factorial-v1",
    power_exists="QF005",power_zero="QH002",power_step="QH002")
HELPER_DEPENDENCIES = {
    "shuffle":("mul_assoc","mul_comm"),
    "invariant":("factorial_zero","power_zero","beta_unique","mul_one","factorial_step","power_step","beta_exists","le_refl","le_succ","le_trans","shuffle"),
    "CV030":("weights_exists","beta_exists","factorial_exists","power_exists","invariant","le_refl","one_mul"),
}


class WeightFactorialsError(ValueError):
    """Changed weight computation, factorial/power body, source or exact target."""


def definition_registry():
    from peano_lab.library.defined_syntax import DEFINITIONS_BY_NAME
    from peano_lab.library.proof_bundle import encode_formula
    result = dict(weights_registry())
    for name,(identifier,digest) in EXISTING_DEFINITIONS.items():
        d = DEFINITIONS_BY_NAME[name]
        if (d.stable_id!=identifier or json_hash(encode_formula(d.template_formula))!=digest
                or not set(d.conceptual_dependencies)<=result.keys()):
            raise WeightFactorialsError("existing factorial/power definition or DAG changed")
        if name in result and result[name].template_formula!=d.template_formula:
            raise WeightFactorialsError("shared factorial/power alias disagrees")
        result[name] = d
    return MappingProxyType(result)


def frozen_weight_factorials_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=2 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise WeightFactorialsError("CV030 exact constructed factorial weight target changed")
    return target


def source_contract():
    return dict(code="CV030",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,weights_and_initial_value_constructed=True,
        actual_factorial_and_power_values_constructed=True,all_in_range_weights_interpreted=True,
        terminal_normalization_proved=True,zero_d_allowed=True,
        nonvanishing_keeps_nonzero_d_premise=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        raw_archive_metadata_is_authority=False,analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def weight_factorials_source_pins():
    result = exponential_weights_source_pins()
    expected = {
        "scripts/sqrt2_power_exponential_weights.py":"f9e1c356636cffd2d244cd01974999b32e835f864bfdfbef4ded8e2ea26e6085",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_weight_factorials.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise WeightFactorialsError("factorial weight source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _shuffle(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        w,f,p,j,d = t.terms(("w","f","p","j","d"))
        wf,jd,pd = Mul(w,f),Mul(j,d),Mul(p,d)
        return _chain(CongMul(EqSym(specialize(t,"mul_assoc",w,f,j)),EqRefl(pd)),
            specialize(t,"mul_assoc",wf,j,pd),CongMul(EqRefl(wf),CongMul(EqRefl(j),specialize(t,"mul_comm",p,d))),
            CongMul(EqRefl(wf),EqSym(specialize(t,"mul_assoc",j,d,p))),EqSym(specialize(t,"mul_assoc",wf,jd,p)),
            CongMul(specialize(t,"mul_comm",wf,jd),EqRefl(p)),CongMul(EqSym(specialize(t,"mul_assoc",jd,w,f)),EqRefl(p)))
    return introduce(s,("w","f","p","j","d"),(),finish)


def _invariant(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    params,premises = ("w","f","p"),("bound","weight","factorial","power")
    def base(t):
        w,f,p,w0 = t.terms(("w","f","p","w0"))
        ww0 = apply(specialize(t,"beta_unique",*t.terms(W),Zero(),w,w0),t.hyp("weight"),t.hyp("initial"))
        f1 = apply(specialize(t,"factorial_zero",Zero(),f),EqRefl(Zero()),t.hyp("factorial"))
        p1 = apply(specialize(t,"power_zero",t.term("d"),Zero(),p),EqRefl(Zero()),t.hyp("power"))
        return _chain(CongMul(CongMul(ww0,f1),p1),specialize(t,"mul_one",Mul(w0,Succ(Zero()))),specialize(t,"mul_one",w0))
    def successor(t):
        def chosen(u):
            j,N,d,w,a,f0,p0 = u.terms(("j","N","d","w","a","f0","p0"))
            adjacent = apply(instantiate(AndElimR(u.hyp("weights")),j,a,w),u.hyp("bound"),u.hyp("old_weight"),u.hyp("weight"))
            old_bound = apply(specialize(u,"le_trans",j,Succ(j),N),apply(specialize(u,"le_succ",j,j),specialize(u,"le_refl",j)),u.hyp("bound"))
            old = apply(specialize(u,"IH",a,f0,p0),old_bound,u.hyp("old_weight"),AndElimL(u.hyp("factorial_data")),AndElimL(u.hyp("power_data")))
            return _chain(CongMul(CongMul(EqRefl(w),AndElimR(u.hyp("factorial_data"))),AndElimR(u.hyp("power_data"))),
                specialize(u,"shuffle",w,f0,p0,Succ(j),d),CongMul(CongMul(EqSym(adjacent),EqRefl(f0)),EqRefl(p0)),old)
        return eliminate(t,apply(specialize(t,"factorial_step",t.term("j"),Succ(t.term("j")),t.term("f")),EqRefl(Succ(t.term("j"))),t.hyp("factorial")),("f0",),"factorial_data",lambda u:
            eliminate(u,apply(specialize(u,"power_step",u.term("d"),u.term("j"),Succ(u.term("j")),u.term("p")),EqRefl(Succ(u.term("j"))),u.hyp("power")),("p0",),"power_data",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(W+("j",))),("a",),"old_weight",chosen)))
    motive = target
    for _ in range(5):
        motive = motive.body
    motive = motive.right.right.body
    return introduce(s,("d","N")+W+("w0",),("weights","initial"),lambda t:
        Ind(motive,introduce(t,params,premises,base),introduce(t,("j",),("IH",),lambda u:introduce(u,params,premises,successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        invariant = apply(specialize(t,"invariant",*t.terms(("d","N")+W+("w0",))),AndElimL(t.hyp("weights_data")),t.hyp("initial"))
        terminal = apply(instantiate(invariant,t.term("N"),Succ(Zero()),*t.terms(("f","p"))),specialize(t,"le_refl",t.term("N")),
            AndElimL(AndElimL(t.hyp("weights_data"))),t.hyp("factorial"),t.hyp("power"))
        norm = _chain(EqSym(terminal),CongMul(specialize(t,"one_mul",t.term("f")),EqRefl(t.term("p"))))
        return witness(t.terms(W+("w0","f","p")),conjunction(AndElimL(t.hyp("weights_data")),AndElimR(t.hyp("weights_data")),
            t.hyp("initial"),t.hyp("factorial"),t.hyp("power"),norm,invariant))
    return introduce(s,("d","N"),(),lambda t:
        eliminate(t,specialize(t,"weights_exists",*t.terms(("d","N"))),W,"weights_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(W),Zero()),("w0",),"initial",lambda v:
                eliminate(v,specialize(v,"factorial_exists",v.term("N")),("f",),"factorial",lambda w:
                    eliminate(w,specialize(w,"power_exists",*w.terms(("d","N"))),("p",),"power",chosen)))))


def prove_weight_factorials(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"shuffle":_shuffle,"invariant":lambda s:_invariant(s,parse_named(HELPER_SOURCES["invariant"],registry=registry)),"CV030":_root}
    return assemble_mixed_certificate(code="CV030",target=frozen_weight_factorials_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,
        pins=weight_factorials_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
