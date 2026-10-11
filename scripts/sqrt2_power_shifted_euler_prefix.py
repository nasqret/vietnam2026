"""CV020: construct the finite coefficient operator D(A)[i]=(i+1)A[i+1].

Compose an actually constructed Euler table with an actual affine slice.
No analytic derivative or chain rule is asserted. Every index and value
transport is an ordinary equality proof, including the empty output prefix.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_euler_product import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,
    canonical,json_hash,read_archive,euler_product_source_pins,
    definition_registry as euler_registry,HELPER_SOURCES as EULER_HELPERS,
)
from sqrt2_power_natural_fubini import (
    definition_registry as affine_registry,natural_fubini_source_pins,
    HELPER_SOURCES as AFFINE_HELPERS,
)
from sqrt2_power_sum_splitting import FUBINI_ARCHIVE
from sqrt2_power_series_power_euler import EULER_ARCHIVE
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst,_one_plus

SCHEMA = "sqrt2-power-shifted-euler-prefix-v1"
PARAMETERS = ("ab","ac","db","dc","N")
DEFINITION_SOURCE = "forall i a. Lt(i,N) -> BetaAt(ab,ac,S i,a) -> BetaAt(db,dc,i,(S i)*a)"
DEFINITION_SHA256 = "cd05103da32cd6d17098196920e25e46bf0e29ecedaf07931db164d2b9304874"
GRAPH = "NatShiftedEulerPrefix(ab,ac,db,dc,N)"
NAMED_SOURCE = "forall ab ac N. exists db dc. "+GRAPH
TARGET_SHA256 = "a653a577dc205366278791e1c5bb895d21bdb2ea525bea07c4494276a051b832"
HELPER_SOURCES = {"from_slice":"forall ab ac eb ec db dc N. NatEulerPrefix(ab,ac,eb,ec,S N) -> NatAffineSlice(eb,ec,1,1,db,dc,N) -> "+GRAPH}
HELPER_TARGET_SHA256 = {"from_slice":"778a4823275a2ee8d53c98e36b18c1875e06e9dc14e3aa754dec68a75c53fcf6"}
ARCHIVES = (EULER_ARCHIVE,FUBINI_ARCHIVE)
ENDPOINT_SOURCES = {
    "zero_add":"forall a. 0+a=a",
    "add_succ_left":"forall a b. S a+b=S(a+b)",
    "one_mul":"forall a. 1*a=a",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "euler_exists":EULER_HELPERS["euler_exists"],
    "slice_exists":AFFINE_HELPERS["slice_exists"],
}
HELPER_DEPENDENCIES = {
    "from_slice":("zero_add","add_succ_left","one_mul","succ_le_succ","beta_exists","beta_unique"),
    "CV020":("euler_exists","slice_exists","from_slice"),
}


class ShiftedEulerError(ValueError):
    """Changed exact computation, conservative alias, source or proof body."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry = dict(euler_registry())
    for name,d in affine_registry().items():
        if name in registry and (registry[name].template_formula!=d.template_formula or registry[name].stable_id!=d.stable_id):
            raise ShiftedEulerError("shared conservative definition mismatch")
        registry[name] = d
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    name,identifier = "NatShiftedEulerPrefix","ND0422"
    if name in registry or identifier in {d.stable_id for d in registry.values()} or any(d["name"]==name or d["id"]==identifier for d in parent):
        raise ShiftedEulerError("shifted-Euler conservative alias collision")
    formula = parse_named(DEFINITION_SOURCE,PARAMETERS,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_SHA256:
        raise ShiftedEulerError("shifted-Euler exact computation changed")
    text = pretty_formula(formula,list(PARAMETERS))
    d = _definition(stable_id=identifier,name=name,parameters=PARAMETERS,template_source=text,
        summary="Actual shifted index multiplication on coefficient tables; no chain rule or analytic derivative assertion.",
        category="irrationality_formal_series",conceptual_dependencies=("Lt","BetaAt"))
    if d.template_formula!=formula or parse_formula_in_context(text,list(PARAMETERS))!=formula:
        raise ShiftedEulerError("shifted-Euler exact expansion failed roundtrip")
    registry[name] = d
    return MappingProxyType(registry)


def frozen_shifted_euler_prefix_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=3 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ShiftedEulerError("CV020 exact shifted-Euler construction target changed")
    return target


def source_contract():
    return dict(code="CV020",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_shifted_euler_table_constructed=True,arbitrary_input_codes_and_length=True,
        operator="D(A)[i]=(i+1)*A[i+1]",new_definition_ids=["ND0422"],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        finite_composition_chain_rule=False,exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def shifted_euler_prefix_source_pins():
    result = euler_product_source_pins()
    for name,pin in natural_fubini_source_pins().items():
        if name in result and result[name]!=pin:
            raise ShiftedEulerError("source dependency disagreement")
        result[name] = pin
    expected = {
        "scripts/sqrt2_power_euler_product.py":"c26512518de941c9f8c54bfe682732d601158748f25955166b3ea6d8290afa10",
        "scripts/sqrt2_power_natural_fubini.py":"d5cc2e21ccbe1f266cad6b535db62601f8e8ba1aa3209a7f89d794285e3805ac",
        "scripts/sqrt2_power_sum_splitting.py":"aa629a6c5eddabbd880ccf615b0bc897fa77da7965c1a37b056016a9611c3c3c",
        "scripts/sqrt2_power_series_power_euler.py":"f00d1180a96ba497a5c961b850e660941d6c608d70ebc7071a51e53344b5205c",
        "scripts/sqrt2_power_convolution_unit.py":"d058762fb3641d5bb1e90c764c4581801feeaf0a103901811b3e82dbe3db8f16",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_shifted_euler_prefix.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ShiftedEulerError("shifted-Euler source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _from_slice(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqTrans
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def output(t):
        i,a,v = t.terms(("i","a","v"))
        bound = apply(specialize(t,"succ_le_succ",Succ(i),t.term("N")),t.hyp("bound"))
        actual = apply(specialize(t,"euler",Succ(i),a),bound,t.hyp("input"))
        sliced = apply(specialize(t,"slice",i,v),t.hyp("bound"),t.hyp("value"))
        address = EqTrans(CongAdd(EqRefl(Succ(Zero())),specialize(t,"one_mul",i)),_one_plus(t,i))
        shifted = _subst(t,registry,"BetaAt(eb,ec,slot,v)",address,sliced)
        equal = apply(specialize(t,"beta_unique",*t.terms(("eb","ec")),Succ(i),v,Mul(Succ(i),a)),shifted,actual)
        return _subst(t,registry,"BetaAt(db,dc,i,slot)",equal,t.hyp("value"))
    return introduce(s,("ab","ac","eb","ec","db","dc","N"),("euler","slice"),lambda t:
        introduce(t,("i","a"),("bound","input"),lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(("db","dc","i"))),("v",),"value",output)))


def _root(s):
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        result = apply(specialize(t,"from_slice",*t.terms(("ab","ac","eb","ec","db","dc","N"))),t.hyp("euler"),t.hyp("slice"))
        return witness(t.terms(("db","dc")),result)
    return introduce(s,("ab","ac","N"),(),lambda t:
        eliminate(t,specialize(t,"euler_exists",*t.terms(("ab","ac")),Succ(t.term("N"))),("eb","ec"),"euler",lambda u:
            eliminate(u,specialize(u,"slice_exists",*u.terms(("eb","ec")),Succ(Zero()),Succ(Zero()),u.term("N")),("db","dc"),"slice",chosen)))


def prove_shifted_euler_prefix(*,limits=None):
    registry = definition_registry()
    factories = {"from_slice":lambda s:_from_slice(s,registry),"CV020":_root}
    return assemble_actual_certificate(code="CV020",target=frozen_shifted_euler_prefix_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=shifted_euler_prefix_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
