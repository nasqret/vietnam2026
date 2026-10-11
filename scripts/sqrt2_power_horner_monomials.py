"""CV040: exact complementary powers in the constructed Horner sum.

Preserve CV039's actual tables and sums. Prove W[j]=q whenever j+e=N
and Pow(t,e,q); consequently Q[j]=a*q when (j+1)+e=N and A[j]=a.
No subtraction, division, nonzero multiplier or analytic limit is used.
"""
from hashlib import sha256

from sqrt2_power_constructed_horner_sum import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,constructed_horner_sum_source_pins,
    NAMED_SOURCE as CONSTRUCTED_SOURCE,GEOMETRIC_DATA,OUTPUTS,A,W,Q,H,prefix,
)
from sqrt2_power_geometric_weights import ENDPOINT_SOURCES as POWER_ENDPOINTS
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive
from sqrt2_power_convolution_unit import _subst

SCHEMA = "sqrt2-power-horner-monomials-v1"
WEIGHTS = "NatGeometricWeightTable(t,N,wb,wc)"
CONSTRUCTED_DATA = "("+GEOMETRIC_DATA+") /\\ ("+prefix(Q)+" /\\ (NatScaledHornerTrace(ab,ac,t,N,hb,hc) /\\ (BetaAt(hb,hc,N,r) /\\ Sum(qb,qc,N,r))))"
COMPLEMENT = "forall e j w q. j+e=N -> BetaAt(wb,wc,j,w) -> Pow(t,e,q) -> w=q"
MONOMIALS = "forall j e a q c. (S j)+e=N -> BetaAt(ab,ac,j,a) -> Pow(t,e,q) -> BetaAt(qb,qc,j,c) -> c=a*q"
NAMED_SOURCE = "forall ab ac t N. exists "+" ".join(OUTPUTS)+". ("+CONSTRUCTED_DATA+") /\\ (("+COMPLEMENT+") /\\ ("+MONOMIALS+"))"
TARGET_SHA256 = "76c2e7135bb0294d18ddca7f6750fc378916725dd05a107878f9dc22c55483d1"
HELPER_SOURCES = {
    "next_index":"forall j e N. j+S e=N -> (S j)+e=N",
    "below":"forall j e N. (S j)+e=N -> Lt(j,N)",
    "complement":"forall t N wb wc. "+WEIGHTS+" -> "+COMPLEMENT,
    "monomials":"forall "+" ".join(A+("t","N")+W+Q)+". "+WEIGHTS+" -> "+prefix(Q)+" -> "+MONOMIALS,
}
HELPER_TARGET_SHA256 = {
    "next_index":"2e0d240c521b1f2e4c198619c20e0089beef17455623892d72d2432863a6cfc0",
    "below":"c86e58158552692011b2965419bf10ea080c040cd19f4a255c5872f0ce423fe2",
    "complement":"820ec945c7d430f42172ca3ab5474c2b3ef6f14378716969e37a7e5687f53138",
    "monomials":"91330686755bcee4a0cc1f7e9fc6a1cf26bff45ce3e438a94c2e08d312c8f81f",
}
CONSTRUCTED_ARCHIVE = dict(case="CV039",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-constructed-horner-sum-v1/generation-process.json.gz",
    bytes=28665,sha256="e655320c0c77f5299e30bb59e570bcad60b39703ba4d506c603c2a48ea461665",
    raw_bytes=519918,raw_sha256="50772d39765345909b2e9d63a3fb298e4986c91c1df3d202981c4ed341e793bd",
    bundle_bytes=308879,bundle_sha256="8b1f8f7f6c20cc160fb79285ee98a4c22931aee8c7494f9e39d848055b15fc5c",
    nodes=137,root=136,target_ast_sha256="04e9780ee714dda23598933ee36bc81764c56ad8b2edc3632b84e8161529ddf8")
ARCHIVES = (CONSTRUCTED_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {name:POWER_ENDPOINTS[name] for name in ("beta_exists","beta_unique","power_zero","power_step","mul_comm")}
ENDPOINT_SOURCES.update(add_succ_left="forall a b. S a+b=S (a+b)",add_comm="forall a b. a+b=b+a",constructed_exists=CONSTRUCTED_SOURCE)
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:"CV039" for name in ("power_zero","power_step","constructed_exists")})
HELPER_DEPENDENCIES = {
    "next_index":("add_succ_left",),"below":("add_comm",),
    "complement":("beta_unique","power_zero","power_step","beta_exists","next_index","below","mul_comm"),
    "monomials":("beta_exists","below","complement"),
    "CV040":("constructed_exists","complement","monomials"),
}


class HornerMonomialsError(ValueError):
    """Changed complementary exponent, same computation witness or proof data."""


def frozen_horner_monomials_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=4 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerMonomialsError("CV040 exact constructed monomial interpretation changed")
    return target


def source_contract():
    return dict(code="CV040",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_actual_weight_product_horner_sum_witnesses_constructed=True,
        same_witnesses_preserved=True,complementary_weight_power_identity_proved=True,
        all_weighted_terms_identified_with_actual_powers=True,zero_multiplier_allowed=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",multiplication_evaluation_identity=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def horner_monomials_source_pins():
    result = constructed_horner_sum_source_pins()
    expected = {"scripts/sqrt2_power_constructed_horner_sum.py":"c0ee9f2e584ffa89201777e4b5f586b11832b5296199d11e8d8e4cb521800fbd",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_horner_monomials.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerMonomialsError("monomial interpretation source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _next_index(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,EqSym
    return introduce(s,("j","e","N"),("index",),lambda t:_chain(
        specialize(t,"add_succ_left",*t.terms(("j","e"))),EqSym(instantiate(Axiom("PA4"),*t.terms(("j","e")))),t.hyp("index")))


def _below(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.terms import Succ
    return introduce(s,("j","e","N"),("index",),lambda t:witness((t.term("e"),),
        _chain(specialize(t,"add_comm",t.term("e"),Succ(t.term("j"))),t.hyp("index"))))


def _complement(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Succ,Zero
    def base(t):
        jN = _chain(EqSym(instantiate(Axiom("PA3"),t.term("j"))),t.hyp("index"))
        at_end = _subst(t,registry,"BetaAt(wb,wc,slot,w)",jN,t.hyp("weight"))
        w1 = apply(specialize(t,"beta_unique",*t.terms(W+("N","w")),Succ(Zero())),at_end,AndElimL(t.hyp("weights")))
        q1 = apply(specialize(t,"power_zero",t.term("t"),Zero(),t.term("q")),EqRefl(Zero()),t.hyp("power"))
        return _chain(w1,EqSym(q1))
    def successor(t):
        def chosen(u):
            j,e,N,w,w0,t0 = u.terms(("j","e","N","w","w0","t"))
            index = apply(specialize(u,"next_index",j,e,N),u.hyp("index"))
            bound = apply(specialize(u,"below",j,e,N),index)
            previous = apply(specialize(u,"IH",Succ(j),w0,u.term("q0")),index,u.hyp("next_weight"),AndElimL(u.hyp("power_data")))
            adjacent = apply(instantiate(AndElimR(u.hyp("weights")),j,w,w0),bound,u.hyp("weight"),u.hyp("next_weight"))
            return _chain(adjacent,CongMul(EqRefl(t0),previous),specialize(u,"mul_comm",t0,u.term("q0")),EqSym(AndElimR(u.hyp("power_data"))))
        power = apply(specialize(t,"power_step",*t.terms(("t","e")),Succ(t.term("e")),t.term("q")),EqRefl(Succ(t.term("e"))),t.hyp("power"))
        return eliminate(t,power,("q0",),"power_data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(W),Succ(u.term("j"))),("w0",),"next_weight",chosen))
    motive = target.body.body.body.body.right.body
    return introduce(s,("t","N")+W,("weights",),lambda t:Ind(motive,
        introduce(t,("j","w","q"),("index","weight","power"),base),
        introduce(t,("e",),("IH",),lambda u:introduce(u,("j","w","q"),("index","weight","power"),successor))))


def _monomials(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        bound = apply(specialize(t,"below",*t.terms(("j","e","N"))),t.hyp("index"))
        product = apply(specialize(t,"products",*t.terms(("j","a","w","c"))),bound,t.hyp("coefficient"),t.hyp("weight"),t.hyp("value"))
        all_weights = apply(specialize(t,"complement",*t.terms(("t","N")+W)),t.hyp("weights"))
        weight = apply(instantiate(all_weights,t.term("e"),Succ(t.term("j")),*t.terms(("w","q"))),t.hyp("index"),t.hyp("weight"),t.hyp("power"))
        return _chain(product,CongMul(EqRefl(t.term("a")),weight))
    return introduce(s,A+("t","N")+W+Q,("weights","products"),lambda t:
        introduce(t,("j","e","a","q","c"),("index","coefficient","power","value"),lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(W),Succ(u.term("j"))),("w",),"weight",chosen)))


def _root(s):
    def chosen(t):
        table = field(field(t.hyp("data"),0,5),0,4)
        complement = apply(specialize(t,"complement",*t.terms(("t","N")+W)),table)
        monomials = apply(specialize(t,"monomials",*t.terms(A+("t","N")+W+Q)),table,field(t.hyp("data"),1,5))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("data"),complement,monomials))
    return introduce(s,A+("t","N"),(),lambda t:
        eliminate(t,specialize(t,"constructed_exists",*t.terms(A+("t","N"))),OUTPUTS,"data",chosen))


def prove_horner_monomials(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"next_index":_next_index,"below":_below,
        "complement":lambda s:_complement(s,parse_named(HELPER_SOURCES["complement"],registry=registry),registry),
        "monomials":_monomials,"CV040":_root}
    return assemble_mixed_certificate(code="CV040",target=frozen_horner_monomials_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,
        pins=horner_monomials_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
