"""Local, conservative rational notation for the irrationality campaign.

These callable DefinitionSpecs are not Alpha admissions. The existing global
registry is neither imported nor mutated. Only already-expanded HA templates
enter proof workers; the scoped parser uses the existing capture-safe expander.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import MappingProxyType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "peano-lab/py"))
from peano_lab.kernel.formulas import _FormulaParser, parse_formula_in_context, pretty_formula
from peano_lab.kernel.terms import ParseError, _is_identifier, _parse_term_from
from peano_lab.library.defined_syntax import (
    _definition, _DefinedFormulaParser, _instantiate_formula,
)
from peano_lab.library.proof_bundle import encode_formula

PARENT = ROOT / "book/_static/constructive-jordan-campaign-v35/definitions.json"
PARENT_SHA256 = "32da2185fd21fb1d0b400404f9b832425a4c35e75be392a3f5b5f73f8464aebf"


class ScopedParser(_DefinedFormulaParser):
    def __init__(self, source, registry, budget=32768):
        super().__init__(source, budget)
        self.registry = registry

    def _atom(self):
        token, position = self.stream.peek(), self.stream.position
        call = (position+1 < len(self.stream.tokens) and
                self.stream.tokens[position+1].text == "(")
        if _is_identifier(token) and token != "S" and call:
            column, name = self.stream.column(), self.stream.take()
            definition = self.registry.get(name)
            if definition is None:
                raise ParseError("unknown campaign definition: " + name)
            self.stream.expect("(")
            arguments = []
            if self.stream.accept(")") is None:
                while True:
                    arguments.append(_parse_term_from(self.stream, self.bound, self.free))
                    if self.stream.accept(")") is not None:
                        break
                    self.stream.expect(",")
            if len(arguments) != definition.arity:
                raise ParseError("wrong campaign definition arity: " + name)
            return _instantiate_formula(definition.template_formula, tuple(arguments), 0,
                                        self.expansion_counter, definition, column)
        return _FormulaParser._atom(self)


def parse_named(source, names=(), registry=None, *, budget=32768):
    if len(names) != len(set(names)) or not all(_is_identifier(n) for n in names):
        raise ValueError("invalid definition binder map")
    parser = ScopedParser(source, DEFINITIONS if registry is None else registry, budget)
    parser.free = list(names)
    formula = parser.parse()
    if tuple(parser.free) != tuple(names):
        raise ValueError("free/captured name in campaign statement")
    return formula


ROWS = (
    (382, "IRatValid", ("p", "m", "d"), "~(d=0)", (),
     "The natural pair p,m is a signed numerator; its denominator d is positive. No accuracy or theorem is a clause."),
    (383, "IRatEq", ("p", "m", "d", "P", "M", "D"),
     "IRatValid(p,m,d) /\\ (IRatValid(P,M,D) /\\ (p*D+M*d=m*D+P*d))", ("IRatValid",),
     "Two valid signed-rational triples have equal cross-multiplied values."),
    (384, "IRatAdd", ("p", "m", "d", "q", "n", "e", "r", "s", "f"),
     "IRatValid(p,m,d) /\\ (IRatValid(q,n,e) /\\ IRatEq(r,s,f,p*e+q*d,m*e+n*d,d*e))",
     ("IRatValid", "IRatEq"), "The output triple represents the ordinary sum, with all denominator validity explicit."),
    (385, "IRatMul", ("p", "m", "d", "q", "n", "e", "r", "s", "f"),
     "IRatValid(p,m,d) /\\ (IRatValid(q,n,e) /\\ IRatEq(r,s,f,p*q+m*n,p*n+m*q,d*e))",
     ("IRatValid", "IRatEq"), "The output triple represents the signed-pair product; no quotient or inverse is assumed."),
    (386, "IRatNeg", ("p", "m", "d", "r", "s", "f"),
     "IRatValid(p,m,d) /\\ IRatEq(r,s,f,m,p,d)", ("IRatValid", "IRatEq"),
     "Negation swaps the two numerator components and preserves positive denominators."),
    (387, "IRatLt", ("p", "m", "d", "P", "M", "D"),
     "IRatValid(p,m,d) /\\ (IRatValid(P,M,D) /\\ (exists gap. p*D+M*d+S gap=m*D+P*d))",
     ("IRatValid",), "Strict rational order has an explicit positive cross-product gap."),
)


def definitions():
    raw = PARENT.read_bytes()
    if sha256(raw).hexdigest() != PARENT_SHA256:
        raise ValueError("immutable definition parent changed")
    historical = json.loads(raw)["reviewed_definitions"]
    names = {r["name"] for r in historical}
    ids = {r["id"] for r in historical}
    result = {}
    for number, name, parameters, named, dependencies, summary in ROWS:
        identifier = f"ND{number:04d}"
        if name in names or name in result or identifier in ids:
            raise ValueError("campaign definition shadows an existing identity")
        if len(dependencies) != len(set(dependencies)) or not set(dependencies) <= result.keys():
            raise ValueError("missing/forward/cyclic definition prerequisite")
        formula = parse_named(named, parameters, result)
        source = pretty_formula(formula, list(parameters))
        definition = _definition(stable_id=identifier, name=name, parameters=parameters,
            template_source=source, summary=summary, category="irrationality_rationals",
            priority="P2", conceptual_dependencies=dependencies)
        if definition.template_formula != formula or parse_formula_in_context(source, list(parameters)) != formula:
            raise ValueError("definition changed under exact expansion")
        result[name] = definition
        ids.add(identifier)
    return MappingProxyType(result)


DEFINITIONS = definitions()


def definition_manifest():
    return dict(authority="local_conservative_templates_not_Alpha_admissions",
        historical_sha256=PARENT_SHA256,
        nodes=[dict(id=d.stable_id, name=d.name, parameters=list(d.parameters),
                    source=d.template_source, ast=encode_formula(d.template_formula),
                    dependencies=list(d.conceptual_dependencies)) for d in DEFINITIONS.values()],
        edges=[dict(source=DEFINITIONS[p].stable_id, target=d.stable_id,
                    kind="definition_uses_definition") for d in DEFINITIONS.values()
               for p in d.conceptual_dependencies])
