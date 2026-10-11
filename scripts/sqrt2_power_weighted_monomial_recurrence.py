"""CV073: the same weighted composition rows obey a scaled exp recurrence.

The denominator is d*p, the numerator is t*x, and the head is w0*v.
All three beta tables are supplied actual computations; zero d is allowed.
The necessary p!=0 guard belongs to monomial cancellation, not weighting.
"""
from hashlib import sha256

from sqrt2_power_monomial_recurrence import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,monomial_recurrence_source_pins,
    COMPOSITION_ARCHIVE,MONOMIALS,ADJACENT,
    NAMED_SOURCE as MONOMIAL_SOURCE,
)
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-weighted-monomial-recurrence-v1"
W,V,Z = ("wb","wc"),("vb","vc"),("zb","zc")
FIXED = ("d","p","t","x","v","N")+W+V+Z
PARAMETERS = FIXED+("w0",)
MONOMIAL_PREFIX = MONOMIALS.replace("Lt(k,K)","Lt(k,S N)")
ADJACENT_PREFIX = ADJACENT.replace("Lt(S k,K)","Lt(S k,S N)")
WEIGHTS = "NatExpWeightTable(d,N,wb,wc)"
PRODUCTS = "NatPointwiseProductPrefix(wb,wc,vb,vc,zb,zc,S N)"
RECURRENCE = "NatScaledExpRecurrence(d*p,t*x,zb,zc,N)"
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". ~p=0 -> ("+MONOMIAL_PREFIX+") -> "+WEIGHTS+" -> "+PRODUCTS+" -> BetaAt(wb,wc,0,w0) -> BetaAt(zb,zc,0,w0*v) /\\ "+RECURRENCE
TARGET_SHA256 = "e23d9c7bce72b64cec08978482e066d449fff7b4e18c3a1cfc5bc8dc55f9d6e5"
HELPER_SOURCES = {
    "head":"forall "+" ".join(PARAMETERS)+". "+PRODUCTS+" -> BetaAt(wb,wc,0,w0) -> BetaAt(vb,vc,0,v) -> BetaAt(zb,zc,0,w0*v)",
    "weighted_recurrence":"forall "+" ".join(FIXED)+". ("+ADJACENT_PREFIX+") -> "+WEIGHTS+" -> "+PRODUCTS+" -> "+RECURRENCE,
}
HELPER_TARGET_SHA256 = {
    "head":"fbb30506681933d9ed8434852061603bd9d8a4ca634b0ae0acccd493ecdf1626",
    "weighted_recurrence":"c898c28633e4440cf27cfe356bbcdef2817a361b731379e55d53707f4cff7249",
}
MONOMIAL_ARCHIVE = dict(case="CV072",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-monomial-recurrence-v1/generation-process.json.gz",
    bytes=29768,sha256="c327eda0a43adab66e3915f3d12f02d4a6217957b725f0dc82752df1cd3167a4",
    raw_bytes=437752,raw_sha256="a6e78b120087d9e75918a09956c1c37b528f19eaf4662ea62eea30b7812c9b6d",
    bundle_bytes=237052,bundle_sha256="8dbc3b54ee1dc9cca4b6031ae181390bd9d73fde574f8e0b26207e7f9615710f",
    nodes=119,root=118,target_ast_sha256="1cac9f24c8b7573372bdfab838b9e0b9248a42d1681fde0d65e7da2768df79c8")
ARCHIVES = (MONOMIAL_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES = {
    "monomial_recurrence":MONOMIAL_SOURCE,
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "zero_le":"forall a. Le(0,a)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["monomial_recurrence"] = "CV072"
HELPER_DEPENDENCIES = {
    "head":("beta_exists","zero_le","succ_le_succ"),
    "weighted_recurrence":("beta_exists","succ_le_succ","le_succ","mul_assoc","mul_comm"),
    "CV073":("monomial_recurrence","head","weighted_recurrence","zero_le","succ_le_succ"),
}


class WeightedMonomialRecurrenceError(ValueError):
    """Changed weight, value, product table or exact composite scale."""


def frozen_weighted_monomial_recurrence_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=13 or len(premises)!=5 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise WeightedMonomialRecurrenceError("CV073 exact same-table weighted recurrence changed")
    return target


def source_contract():
    return dict(code="CV073",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,nonzero_monomial_scale_required=True,zero_weight_denominator_allowed=True,
        actual_weight_value_and_product_tables_required=True,same_decoded_tables_throughout=True,
        numerator="t*x",denominator="d*p",initial_value="w0*v",horizon="N; N+1 terms",
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",actual_composition_constructed=False,
        finite_sum_bound_claimed=False,analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def weighted_monomial_recurrence_source_pins():
    result = monomial_recurrence_source_pins()
    expected = {"scripts/sqrt2_power_monomial_recurrence.py":"d9aa5c2631a9ddfff0d93b93a85181c8038f991afba42e38e109cbe87c9a9bb8",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_weighted_monomial_recurrence.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise WeightedMonomialRecurrenceError("weighted monomial source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _head(s,registry):
    from peano_lab.kernel.terms import Zero
    def chosen(u):
        bound = apply(specialize(u,"succ_le_succ",Zero(),u.term("N")),specialize(u,"zero_le",u.term("N")))
        eq = apply(specialize(u,"products",Zero(),*u.terms(("w0","v","z"))),bound,u.hyp("initial_weight"),u.hyp("initial_value"),u.hyp("entry"))
        return _subst(u,registry,"BetaAt(zb,zc,0,slot)",eq,u.hyp("entry"))
    return introduce(s,PARAMETERS,("products","initial_weight","initial_value"),lambda u:
        eliminate(u,specialize(u,"beta_exists",*u.terms(Z),Zero()),("z",),"entry",chosen))


def _weighted_recurrence(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimR,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def entry(u):
        def chosen(z):
            d,p,t,x,j,y,w,a,b,c,e = z.terms(("d","p","t","x","j","y","z","a","b","c","e"))
            sj = Succ(j);tx = Mul(t,x);jd = Mul(sj,d)
            jb = apply(specialize(z,"le_succ",sj,z.term("N")),z.hyp("bound"))
            sjb = apply(specialize(z,"succ_le_succ",sj,z.term("N")),z.hyp("bound"))
            old = apply(specialize(z,"products",j,a,c,y),jb,z.hyp("weight"),z.hyp("value"),z.hyp("entry_y"))
            new = apply(specialize(z,"products",sj,b,e,w),sjb,z.hyp("next_weight"),z.hyp("next_value"),z.hyp("entry_z"))
            weight = apply(instantiate(AndElimR(z.hyp("weights")),j,a,b),z.hyp("bound"),z.hyp("weight"),z.hyp("next_weight"))
            values = apply(specialize(z,"adjacent",j,c,e),sjb,z.hyp("value"),z.hyp("next_value"))
            scale = Mul(sj,Mul(d,p))
            return _chain(CongMul(EqRefl(scale),new),
                _multiplicative_equal(z,Mul(scale,Mul(b,e)),Mul(Mul(jd,b),Mul(p,e))),
                CongMul(EqSym(weight),values),_multiplicative_equal(z,Mul(a,Mul(tx,c)),Mul(tx,Mul(a,c))),
                CongMul(EqRefl(tx),EqSym(old)))
        return eliminate(u,specialize(u,"beta_exists",*u.terms(W+("j",))),("a",),"weight",lambda a:
            eliminate(a,specialize(a,"beta_exists",*a.terms(W),Succ(a.term("j"))),("b",),"next_weight",lambda b:
                eliminate(b,specialize(b,"beta_exists",*b.terms(V+("j",))),("c",),"value",lambda c:
                    eliminate(c,specialize(c,"beta_exists",*c.terms(V),Succ(c.term("j"))),("e",),"next_value",chosen))))
    return introduce(s,FIXED,("adjacent","weights","products"),lambda u:
        introduce(u,("j","y","z"),("bound","entry_y","entry_z"),entry))


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ,Zero
    def finish(u):
        values = apply(specialize(u,"monomial_recurrence",*u.terms(("p","t","x","v")),Succ(u.term("N")),*u.terms(V)),u.hyp("nonzero_p"),u.hyp("monomials"))
        bound = apply(specialize(u,"succ_le_succ",Zero(),u.term("N")),specialize(u,"zero_le",u.term("N")))
        head = apply(specialize(u,"head",*u.terms(PARAMETERS)),u.hyp("products"),u.hyp("initial_weight"),apply(AndElimL(values),bound))
        recurrence = apply(specialize(u,"weighted_recurrence",*u.terms(FIXED)),AndElimR(values),u.hyp("weights"),u.hyp("products"))
        return conjunction(head,recurrence)
    return introduce(s,PARAMETERS,("nonzero_p","monomials","weights","products","initial_weight"),finish)


def prove_weighted_monomial_recurrence(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV073",target=frozen_weighted_monomial_recurrence_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"head":lambda s:_head(s,registry),"weighted_recurrence":_weighted_recurrence,"CV073":_root},
        pins=weighted_monomial_recurrence_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
