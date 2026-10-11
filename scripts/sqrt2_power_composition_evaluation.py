"""CV034: construct the normalized composition and its exact Horner value.

For N=K+2, preserve all finite composition, factorial and coefficient data;
construct the very same coefficient table's Horner trace at 3, its endpoint r
and p=3^(K+1), with r+z=(2*z)*p and z*p nonzero. No analytic limit is asserted.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_normalized_composition import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,OUTPUTS as NORMALIZED_OUTPUTS,COEFFICIENT_DATA,INVARIANT,
    NAMED_SOURCE as NORMALIZED_SOURCE,definition_registry as normalized_registry,
    normalized_composition_source_pins,
)
from sqrt2_power_geometric_horner import (
    definition_registry as geometric_registry,geometric_horner_source_pins,
    NAMED_SOURCE as GEOMETRIC_SOURCE,ENDPOINT_SOURCES as GEOMETRIC_ENDPOINTS,
)
from sqrt2_power_exponential_weights import ENDPOINT_SOURCES as WEIGHT_ENDPOINTS
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-composition-evaluation-v1"
H = ("hb","hc")
OUTPUTS = ("N",)+NORMALIZED_OUTPUTS+H+("r","p")
NORMALIZED_DATA = "("+COEFFICIENT_DATA+") /\\ (Factorial(N,fn) /\\ (Pow(d,N,pn) /\\ (z=fn*pn /\\ ("+INVARIANT+"))))"
RESULTS = ("N=S(S K)","("+NORMALIZED_DATA+")","NatScaledHornerTrace(cb,cc,3,N,hb,hc)",
    "BetaAt(hb,hc,N,r)","Pow(3,S K,p)","~p=0","r+z=(2*z)*p","~(z*p=0)")
RESULT = RESULTS[-1]
for _part in reversed(RESULTS[:-1]):
    RESULT = _part+" /\\ ("+RESULT+")"
NAMED_SOURCE = "forall K. exists "+" ".join(OUTPUTS)+". "+RESULT
TARGET_SHA256 = "11b40acf4f70651db35615b86f321bc4dc95ea05a8e711c8a3f41d9c2fd3ed34"
NORMALIZED_ARCHIVE = dict(case="CV031",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-normalized-composition-v1/generation-process.json.gz",
    bytes=80278,sha256="e21504adfe27bd23d0a6a884637d126199d7a49c42167c1d46ced4be1e9bff0d",
    raw_bytes=2232469,raw_sha256="ef072eda9d22b6a37049e89e428022b37af6967ce004e986393616bfeb037ab0",
    bundle_bytes=1369285,bundle_sha256="37a4fbb48c282439ac816d0efea5198bc6905ad57e7736aad23242cd96f8be71",
    nodes=272,root=271,target_ast_sha256="255502b20ed9e685e90c18c8a121a614c14ffe23ae181d749f51ced7a170f19e")
GEOMETRIC_ARCHIVE = dict(case="CV033",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-geometric-horner-v1/generation-process.json.gz",
    bytes=25732,sha256="0968c2c9430a59392536efdec3161a10c0990bea60e7ba62df172669946876cc",
    raw_bytes=417769,raw_sha256="a0273514b5bd4d4999f4f0d58cfc7cb8dad7614147e54d641df69b2b5a86c2a0",
    bundle_bytes=245286,bundle_sha256="d21aa29f793a9af547b2a92db2057ac2e272fb688da7b44c6bf1226b24b72ca9",
    nodes=126,root=125,target_ast_sha256="fbb3d37960c61bdda6f6242ac8a1ea3bd5ea98c9d28b11ee26556b39dce16fd6")
ARCHIVES = (NORMALIZED_ARCHIVE,GEOMETRIC_ARCHIVE)
ENDPOINT_SOURCES = dict(normalized_exists=NORMALIZED_SOURCE,geometric_exists=GEOMETRIC_SOURCE,
    zero_le=WEIGHT_ENDPOINTS["zero_le"],succ_le_succ=WEIGHT_ENDPOINTS["succ_le_succ"],mul_ne_zero=GEOMETRIC_ENDPOINTS["mul_ne_zero"])
ENDPOINT_OWNERS = dict(normalized_exists="CV031",geometric_exists="CV033",zero_le="CV031",succ_le_succ="CV031",mul_ne_zero="CV033")
HELPER_SOURCES,HELPER_TARGET_SHA256 = {},{}
HELPER_DEPENDENCIES = {"CV034":tuple(ENDPOINT_SOURCES)}


class CompositionEvaluationError(ValueError):
    """Changed same-witness coefficient evaluation or archived actual proof."""


def definition_registry():
    result = dict(normalized_registry())
    for name,d in geometric_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise CompositionEvaluationError("normalized composition/Horner definition mismatch")
        result[name] = d
    return MappingProxyType(result)


def frozen_composition_evaluation_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CompositionEvaluationError("CV034 exact constructed composition evaluation changed")
    return target


def source_contract():
    return dict(code="CV034",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,width_constructed_as_index_plus_two=True,whole_actual_composition_constructed=True,
        same_coefficients_used_for_horner=True,factorial_normalization_preserved=True,
        coefficient_pattern_is_proved_output=True,actual_horner_and_nonzero_power_constructed=True,
        exact_integer_remainder_identity=True,normalized_denominator_nonzero=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def composition_evaluation_source_pins():
    result = normalized_composition_source_pins()
    for name,pin in geometric_horner_source_pins().items():
        if name in result and result[name]!=pin:
            raise CompositionEvaluationError("source pin disagreement")
        result[name] = pin
    expected = {"scripts/sqrt2_power_geometric_horner.py":"6179fa42c4437ed53db78fdc4f806d281d4774b58544150c7007dcfa3b656adc",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_composition_evaluation.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CompositionEvaluationError("composition evaluation source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        def evaluated(u):
            z_nonzero = field(field(u.hyp("composition"),0,5),2,5)
            denom = apply(specialize(u,"mul_ne_zero",*u.terms(("z","p"))),z_nonzero,field(u.hyp("evaluation"),3,5))
            N = Succ(Succ(u.term("K")))
            return witness((N,)+u.terms(NORMALIZED_OUTPUTS+H+("r","p")),conjunction(EqRefl(N),u.hyp("composition"),
                *(field(u.hyp("evaluation"),i,5) for i in range(5)),denom))
        pattern = field(field(t.hyp("composition"),0,5),4,5)
        evaluation = apply(specialize(t,"geometric_exists",*t.terms(("cb","cc","z")),Succ(t.term("K"))),pattern)
        return eliminate(t,evaluation,H+("r","p"),"evaluation",evaluated)
    def begin(t):
        K = t.term("K")
        one = apply(specialize(t,"succ_le_succ",Zero(),K),specialize(t,"zero_le",K))
        width = apply(specialize(t,"succ_le_succ",Succ(Zero()),Succ(K)),one)
        normalized = apply(specialize(t,"normalized_exists",Succ(Succ(K))),width)
        return eliminate(t,normalized,NORMALIZED_OUTPUTS,"composition",chosen)
    return introduce(s,("K",),(),begin)


def prove_composition_evaluation(*,limits=None):
    return assemble_mixed_certificate(code="CV034",target=frozen_composition_evaluation_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories={"CV034":_root},
        pins=composition_evaluation_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
