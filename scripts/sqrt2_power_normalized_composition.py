"""CV031: factorial normalization of the same constructed composition.

Preserves all actual CV029 witnesses and proves z=N!*d^N and
(w[j]*j!)*d^j=z for their very same weight table. This finite polynomial
certificate does not yet assert a rational evaluation or analytic limit.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_composition_coefficients import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,OUTPUTS as COMPOSITION_OUTPUTS,RESULT,RECURRENCE,SOLUTION,
    NAMED_SOURCE as COEFFICIENT_SOURCE,definition_registry as coefficient_registry,
    composition_coefficients_source_pins,
)
from sqrt2_power_weight_factorials import (
    definition_registry as factorial_registry,weight_factorials_source_pins,
    HELPER_SOURCES as FACTORIAL_HELPERS,ENDPOINT_SOURCES as FACTORIAL_ENDPOINTS,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-normalized-composition-v1"
OUTPUTS = COMPOSITION_OUTPUTS+("fn","pn")
COEFFICIENT_DATA = "("+RESULT+") /\\ (BetaAt(wb,wc,0,z) /\\ (~z=0 /\\ ("+RECURRENCE+" /\\ ("+SOLUTION+"))))"
INVARIANT = "forall j w f p. Le(j,N) -> BetaAt(wb,wc,j,w) -> Factorial(j,f) -> Pow(d,j,p) -> (w*f)*p=z"
NAMED_SOURCE = "forall N. Lt(1,N) -> exists "+" ".join(OUTPUTS)+". ("+COEFFICIENT_DATA+") /\\ (Factorial(N,fn) /\\ (Pow(d,N,pn) /\\ (z=fn*pn /\\ ("+INVARIANT+"))))"
TARGET_SHA256 = "255502b20ed9e685e90c18c8a121a614c14ffe23ae181d749f51ced7a170f19e"
COEFFICIENT_ARCHIVE = dict(case="CV029",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-composition-coefficients-v1/generation-process.json.gz",
    bytes=74463,sha256="bbb051bb73e7d02ba5b0d1db51e3c2b1fcc53333ca9eaf78ad61ec2a27bfa7d5",
    raw_bytes=2031688,raw_sha256="1334a5a34dcc526920c8768297fea44139be46abf68c2ce475bb15d29a72a28a",
    bundle_bytes=1247644,bundle_sha256="401c29b8458ca2615288aa3d695825d8ecc57b021ecce5e677c0920c4df360d9",
    nodes=252,root=251,target_ast_sha256="88f055686ab9620a1835d315530f9884d4bbd0626a5b97d2524141ff1701f83b")
FACTORIAL_ARCHIVE = dict(case="CV030",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-weight-factorials-v1/generation-process.json.gz",
    bytes=26536,sha256="7072741c479df5824535354ab78b0741927a9831d12627fdacf0f9e62da8a699",
    raw_bytes=473986,raw_sha256="2268b324fa5cb98ec8b1b6a1e9630e2b94ff2cf1137eb144516fe7a0df345527",
    bundle_bytes=281234,bundle_sha256="c7972044ee20c85a4f3cf7cff03b6217745c4a16071999769c4714bf6d940e10",
    nodes=130,root=129,target_ast_sha256="7416c0350bc9ea0e640eccd8e16eeb667dc7c4ae78dfb37bc2abd3442cdaa923")
ARCHIVES = (COEFFICIENT_ARCHIVE,FACTORIAL_ARCHIVE)
ENDPOINT_SOURCES = {"composition_exists":COEFFICIENT_SOURCE,
    "invariant":FACTORIAL_HELPERS["invariant"],
    **{name:FACTORIAL_ENDPOINTS[name] for name in ("factorial_exists","power_exists","le_refl","one_mul")}}
ENDPOINT_OWNERS = {name:"CV030" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["composition_exists"] = "CV029"
HELPER_SOURCES,HELPER_TARGET_SHA256 = {},{}
HELPER_DEPENDENCIES = {"CV031":tuple(ENDPOINT_SOURCES)}


class NormalizedCompositionError(ValueError):
    """Changed same-witness normalization, exact definitions or proof sources."""


def definition_registry():
    result = dict(coefficient_registry())
    for name,d in factorial_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise NormalizedCompositionError("shared definition DAG mismatch")
        result[name] = d
    return MappingProxyType(result)


def frozen_normalized_composition_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=1 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise NormalizedCompositionError("CV031 exact same-witness normalized composition changed")
    return target


def source_contract():
    return dict(code="CV031",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,width_at_least_two_required=True,
        whole_actual_computation_constructed=True,same_composition_weight_witnesses=True,
        nonzero_common_denominator_constructed=True,factorial_and_power_values_constructed=True,
        all_in_range_coefficients_identified=True,all_weight_factorial_identities_proved=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",rational_evaluation_identity=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def normalized_composition_source_pins():
    result = composition_coefficients_source_pins()
    for name,pin in weight_factorials_source_pins().items():
        if name in result and result[name]!=pin:
            raise NormalizedCompositionError("source pin disagreement")
        result[name] = pin
    expected = {
        "scripts/sqrt2_power_composition_coefficients.py":"865eb25ee91d89922a5fec9b510f98babc39bf47f5160dc5e2fc4c65558158a4",
        "scripts/sqrt2_power_weight_factorials.py":"cabf5acbe76204dc59c64130a45172440713577d2859f1672635d3a4cf6aacd7",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_normalized_composition.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise NormalizedCompositionError("actual normalized composition source changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        table = field(field(t.hyp("data"),0,5),2,10)
        invariant = apply(specialize(t,"invariant",*t.terms(("d","N","wb","wc","z"))),table,field(t.hyp("data"),1,5))
        terminal = apply(instantiate(invariant,t.term("N"),Succ(Zero()),*t.terms(("fn","pn"))),
            specialize(t,"le_refl",t.term("N")),AndElimL(table),t.hyp("factorial"),t.hyp("power"))
        norm = _chain(EqSym(terminal),CongMul(specialize(t,"one_mul",t.term("fn")),EqRefl(t.term("pn"))))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp("data"),t.hyp("factorial"),t.hyp("power"),norm,invariant))
    return introduce(s,("N",),("width",),lambda t:
        eliminate(t,apply(specialize(t,"composition_exists",t.term("N")),t.hyp("width")),COMPOSITION_OUTPUTS,"data",lambda u:
            eliminate(u,specialize(u,"factorial_exists",u.term("N")),("fn",),"factorial",lambda v:
                eliminate(v,specialize(v,"power_exists",*v.terms(("d","N"))),("pn",),"power",chosen))))


def prove_normalized_composition(*,limits=None):
    return assemble_mixed_certificate(code="CV031",target=frozen_normalized_composition_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories={"CV031":_root},
        pins=normalized_composition_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
