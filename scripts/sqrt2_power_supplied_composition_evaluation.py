"""CV081: evaluate supplied full power and weighted-accumulation tables.

Only the new evaluation data are constructed. The caller's input, weights,
power trace, accumulation and its terminal rows remain the same at every
evaluation base, including zero. This is finite algebra, not a limit claim.
"""
from hashlib import sha256

from sqrt2_power_full_composition_evaluation import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,full_composition_evaluation_source_pins,
    A,P,HA,W,R,V,Z,U,WIDTH,POWER_TRACE,ACCUMULATION_TRACE,
    PARTS as ORIGINAL_PARTS,HELPER_SOURCES as COMPOSITION_HELPERS,conjoin,
)
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE
from sqrt2_power_weighted_accumulation_evaluation import HELPER_SOURCES as ACCUMULATION_HELPERS,ENDPOINT_SOURCES as ACCUMULATION_ENDPOINTS
from sqrt2_power_row_horner_values import HELPER_SOURCES as ROW_HELPERS
from sqrt2_power_horner_trace import NAMED_SOURCE as HORNER_SOURCE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-supplied-composition-evaluation-v1"
PARAMETERS = A+("t","J","K")+W+P+R
OUTPUTS = HA+("x","p","v")+V+Z+("s",)
PREMISES = (WIDTH,POWER_TRACE,ACCUMULATION_TRACE)
PARTS = tuple(ORIGINAL_PARTS[i] for i in (1,2,3,4,6,7,8,9,10))
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256 = "afd8a2cb3249c998e8a875e5136ae8ea7ce51566569fff1a737c3bb58e6fb097"
HELPER_SOURCES,HELPER_TARGET_SHA256 = {},{}
ARCHIVES = (COMPOSITION_ARCHIVE,)
ENDPOINT_SOURCES = {
    "horner_exists":HORNER_SOURCE,"row_values_exists":ROW_HELPERS["prefix_exists"],
    "products_exists":ACCUMULATION_HELPERS["products_exists"],
    "sum_exists":ACCUMULATION_ENDPOINTS["sum_exists"],
    "value_exists":ROW_HELPERS["value_exists"],"accumulation_rows":ACCUMULATION_HELPERS["all_rows"],
    "monomials":COMPOSITION_HELPERS["monomials"],
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "power_exists":"forall a n. exists p. Pow(a,n,p)","le_refl":"forall a. Le(a,a)",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {"CV081":tuple(ENDPOINT_SOURCES)}


class SuppliedCompositionEvaluationError(ValueError):
    """Changed supplied traces, support bound or actual evaluated values."""


def frozen_supplied_composition_evaluation_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=16 or len(premises)!=3 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SuppliedCompositionEvaluationError("CV081 exact supplied-computation evaluation changed")
    return target


def source_contract():
    return dict(code="CV081",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,support_complete_width="1+K*L <= J+1",supplied_input_weights_power_and_accumulation_preserved=True,
        actual_input_horner_scaling_powers_row_values_products_and_sum_constructed=True,
        every_supplied_terminal_row_has_same_sum_as_value=True,all_row_values_satisfy_monomial_law=True,
        arbitrary_evaluation_base=True,zero_base_and_empty_lengths_allowed=True,
        power_or_accumulation_trace_replaced=False,no_nonzero_factor_cancelled=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def supplied_composition_evaluation_source_pins():
    result = full_composition_evaluation_source_pins()
    expected = {"scripts/sqrt2_power_full_composition_evaluation.py":"1f072083655a535b2116b2e6f7dcac7c5459fb83e15899b485347b456bb6f544",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_supplied_composition_evaluation.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SuppliedCompositionEvaluationError("supplied evaluation source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        def terminal(u):
            def evaluated(v):
                H = Succ(v.term("J"))
                rows = apply(specialize(v,"accumulation_rows",H,*v.terms(("t",)+W+P+R+V+Z+("K",))),
                    v.hyp("accumulation"),v.hyp("row_values"),v.hyp("products"))
                same = apply(instantiate(rows,*v.terms(("K",)+U+("y","s"))),specialize(v,"le_refl",v.term("K")),
                    v.hyp("row"),v.hyp("value"),v.hyp("sum"))
                return _subst(v,registry,"NatHornerValue(ub,uc,t,S J,slot)",same,v.hyp("value"))
            return eliminate(u,specialize(u,"value_exists",*u.terms(U+("t",)),Succ(u.term("J"))),("y",),"value",evaluated)
        monomials = apply(specialize(t,"monomials",*t.terms(A+("t","J","K")+P+HA+("x","p","v")+V)),
            t.hyp("width"),t.hyp("powers"),AndElimL(t.hyp("input_trace")),t.hyp("input_value"),t.hyp("power_p"),t.hyp("power_v"),t.hyp("row_values"))
        return witness(t.terms(OUTPUTS),conjunction(AndElimL(t.hyp("input_trace")),t.hyp("input_value"),t.hyp("power_p"),t.hyp("power_v"),
            t.hyp("row_values"),t.hyp("products"),t.hyp("sum"),introduce(t,U,("row",),terminal),monomials))
    return introduce(s,PARAMETERS,("width","powers","accumulation"),lambda t:
        eliminate(t,specialize(t,"horner_exists",*t.terms(("ab","ac","t","L"))),HA,"input_trace",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(HA+("L",))),("x",),"input_value",lambda v:
                eliminate(v,specialize(v,"power_exists",*v.terms(("t","L"))),("p",),"power_p",lambda w:
                    eliminate(w,specialize(w,"power_exists",*w.terms(("t","J"))),("v",),"power_v",lambda a:
                        eliminate(a,specialize(a,"row_values_exists",*a.terms(P+("t",)),Succ(a.term("J")),a.term("K")),V,"row_values",lambda b:
                            eliminate(b,specialize(b,"products_exists",*b.terms(W+V+("K",))),Z,"products",lambda c:
                                eliminate(c,specialize(c,"sum_exists",*c.terms(Z+("K",))),("s",),"sum",chosen))))))))


def prove_supplied_composition_evaluation(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV081",target=frozen_supplied_composition_evaluation_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"CV081":lambda s:_root(s,registry)},pins=supplied_composition_evaluation_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
