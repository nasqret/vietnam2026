"""Two local conservative component relations for multiplication in Z[sqrt(2)].

They abbreviate separate balance equations, not a conjunction of hypotheses.
No totality, norm identity, theorem, global registry entry or new axiom is added.
The six existing rational templates and historical definition parent are left
unchanged; presentation roundtrips bind these aliases to the exact SN003 target.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_definitions import DEFINITIONS, PARENT, PARENT_SHA256, parse_named
from peano_lab.kernel.formulas import parse_formula_in_context, pretty_formula
from peano_lab.library.defined_syntax import _definition
from peano_lab.library.proof_bundle import encode_formula


ROWS = (
    (388, "IQuadProductReal", ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn", "rp", "rn"),
     "rp+((ap*cn+an*cp)+(S(S 0))*(bp*dn+bn*dp))="
     "((ap*cp+an*cn)+(S(S 0))*(bp*dp+bn*dn))+rn",
     "The signed pair rp,rn represents the real component AC+2BD of (A+B sqrt(2))(C+D sqrt(2))."),
    (389, "IQuadProductRadical", ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn", "sp", "sn"),
     "sp+((ap*dn+an*dp)+(bp*cn+bn*cp))="
     "((ap*dp+an*dn)+(bp*cp+bn*cn))+sn",
     "The signed pair sp,sn represents the radical component AD+BC of (A+B sqrt(2))(C+D sqrt(2))."),
)


def quadratic_definitions():
    raw = PARENT.read_bytes()
    if sha256(raw).hexdigest() != PARENT_SHA256:
        raise ValueError("immutable quadratic definition parent changed")
    historical = json.loads(raw)["reviewed_definitions"]
    used_names = {row["name"] for row in historical} | set(DEFINITIONS)
    used_ids = {row["id"] for row in historical} | {d.stable_id for d in DEFINITIONS.values()}
    result = {}
    for number, name, parameters, source, summary in ROWS:
        identifier = f"ND{number:04d}"
        if name in used_names or identifier in used_ids:
            raise ValueError("quadratic alias shadows an existing definition")
        formula = parse_named(source, parameters, registry={})
        expanded = pretty_formula(formula, list(parameters))
        definition = _definition(stable_id=identifier, name=name, parameters=parameters,
            template_source=expanded, summary=summary, category="irrationality_quadratic_integers",
            priority="P2", conceptual_dependencies=())
        if (definition.template_formula != formula or
                parse_formula_in_context(expanded, list(parameters)) != formula):
            raise ValueError("quadratic alias changed under exact expansion")
        result[name] = definition
        used_names.add(name)
        used_ids.add(identifier)
    return MappingProxyType(result)


QUADRATIC_DEFINITIONS = quadratic_definitions()


def quadratic_definition_manifest():
    return dict(authority="local_conservative_templates_not_Alpha_admissions",
        historical_sha256=PARENT_SHA256,
        nodes=[dict(id=d.stable_id, name=d.name, parameters=list(d.parameters),
                    source=d.template_source, ast=encode_formula(d.template_formula),
                    dependencies=list(d.conceptual_dependencies))
               for d in QUADRATIC_DEFINITIONS.values()],
        edges=[])
