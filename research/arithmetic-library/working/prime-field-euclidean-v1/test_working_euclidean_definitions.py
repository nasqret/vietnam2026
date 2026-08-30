"""Actual conservative syntax tests; no theorem/admission acceptance fixture."""

from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
import importlib.util
from pathlib import Path
import re
import sys

import pytest

import constructive_polynomial_division_definitions as previous
import constructive_polynomial_division_definition_graph as previous_graph

_OLD_MODULES = {name: module for name, module in sys.modules.items()
                if name.startswith("constructive_") and name.endswith(("_definitions", "_definition_graph"))}
_OLD_BYTES = {Path(module.__file__): sha256(Path(module.__file__).read_bytes()).hexdigest()
              for module in _OLD_MODULES.values()}

import working_euclidean_definitions as definitions
import working_euclidean_definition_graph as graph
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.kernel.terms import ParseError
from peano_lab.library.formula_dag import FormulaArena


PRIOR = previous.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
ALL = definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
NEW = definitions.EUCLIDEAN_DEFINITIONS
EXPECTED = (
    ("PolynomialLeftPad", ("b", "c", "L", "t", "d", "e"),
     definitions.representation.prime_field_polynomial_left_pad_relation, ("Lt", "BetaAt")),
    ("PolynomialPowerCoefficient", ("b", "c", "L", "k", "a"),
     definitions.representation.prime_field_polynomial_power_coefficient_relation, ("BetaAt", "Le")),
    ("PolynomialEquivalent", ("b", "c", "L", "d", "e", "M"),
     definitions.representation.prime_field_polynomial_equivalent_relation, ("PolynomialPowerCoefficient",)),
    ("FpPolynomialQuotientStep", ("p", "k", "ab", "ac", "bb", "bc", "M", "qb", "qc", "i", "q"),
     definitions.division.prime_field_polynomial_quotient_step_relation,
     ("BetaAt", "FpConvolutionCoefficient", "FpAdd", "FpMul")),
    ("FpPolynomialQuotientPrefix", ("p", "k", "ab", "ac", "bb", "bc", "M", "qb", "qc", "N"),
     definitions.division.prime_field_polynomial_quotient_prefix_relation,
     ("Lt", "BetaAt", "FpPolynomialQuotientStep")),
    ("PolynomialQuotientLength", ("L", "d", "q"),
     definitions.division.prime_field_polynomial_quotient_length_relation, ("Le",)),
    ("FpPolynomialDivisionExecution", ("p", "ab", "ac", "L", "bb", "bc", "d", "qb", "qc", "q", "rb", "rc", "R"),
     definitions.division.prime_field_polynomial_division_execution_relation,
     ("BetaPrefixInto", "PolynomialQuotientLength", "BetaAt", "FpInv", "FpPolynomialQuotientPrefix",
      "FpConvolutionPrefix", "FpCoefficientSubtraction", "FpPolynomialTrim")),
)


def _authority_modules():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(("peano_lab.library.editions", "check_alpha_v32", "build_peano_library_channels"))}


@pytest.fixture(autouse=True)
def preserve_historical_source_and_proof_authority():
    before = _authority_modules()
    yield
    assert _authority_modules() == before
    assert all(sys.modules[name] is module for name, module in _OLD_MODULES.items())
    assert all(sha256(path.read_bytes()).hexdigest() == digest for path, digest in _OLD_BYTES.items())


def _same_ast(left, right):
    pending, seen = [(left, right)], set()
    while pending:
        a, b = pending.pop()
        assert type(a) is type(b)
        if (id(a), id(b)) in seen:
            continue
        seen.add((id(a), id(b)))
        if is_dataclass(a):
            pending.extend((getattr(a, field.name), getattr(b, field.name)) for field in fields(a))
        else:
            assert a == b


def _parse(source, context=(), registry=ALL):
    parser = _LocalDefinedParser(source, registry)
    parser.free = list(context)
    result = parser.parse()
    assert tuple(parser.free) == tuple(context)
    return result


def _call(name, *arguments):
    return name + "(" + ",".join(arguments) + ")"


def _and(*parts):
    result = "(" + parts[-1] + ")"
    for part in reversed(parts[:-1]):
        result = "(" + part + ") /\\ (" + result + ")"
    return result


def _independent(name, arguments, context=()):
    """Hand-assembled contracts in strictly lower named vocabulary."""
    used = set(context) | set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", " ".join(arguments)))
    counter = 0

    def fresh(count):
        nonlocal counter
        result = []
        while len(result) < count:
            value = "independent_euclidean_" + str(counter)
            counter += 1
            if value not in used:
                used.add(value)
                result.append(value)
        return tuple(result)

    if name == "PolynomialLeftPad":
        b, c, L, t, d, e = arguments
        i, j, a = fresh(3)
        return _and(f"forall {i}. Lt({i},{t}) -> BetaAt({d},{e},{i},0)",
            f"forall {j} {a}. Lt({j},{L}) -> BetaAt({b},{c},{j},{a}) -> BetaAt({d},{e},({t})+{j},{a})")
    if name == "PolynomialPowerCoefficient":
        b, c, L, k, a = arguments
        i, = fresh(1)
        return (f"(exists {i}. " + _and(f"{i}+S ({k})=({L})", f"BetaAt({b},{c},{i},{a})")
                + ") \\/ (" + _and(f"Le({L},{k})", f"({a})=0") + ")")
    if name == "PolynomialEquivalent":
        b, c, L, d, e, M = arguments
        k, a, r = fresh(3)
        return (f"forall {k} {a} {r}. PolynomialPowerCoefficient({b},{c},{L},{k},{a}) -> "
                f"PolynomialPowerCoefficient({d},{e},{M},{k},{r}) -> {a}={r}")
    if name == "FpPolynomialQuotientStep":
        p, k, ab, ac, bb, bc, M, qb, qc, i, q = arguments
        a, c, s = fresh(3)
        return f"exists {a} {c} {s}. " + _and(f"BetaAt({ab},{ac},{i},{a})",
            f"FpConvolutionCoefficient({p},{qb},{qc},{i},{bb},{bc},{M},{i},{c})",
            f"FpAdd({p},{c},{s},{a})", f"FpMul({p},{k},{s},{q})")
    if name == "FpPolynomialQuotientPrefix":
        p, k, ab, ac, bb, bc, M, qb, qc, N = arguments
        i, q = fresh(2)
        return f"forall {i}. Lt({i},{N}) -> exists {q}. " + _and(
            f"BetaAt({qb},{qc},{i},{q})", f"FpPolynomialQuotientStep({p},{k},{ab},{ac},{bb},{bc},{M},{qb},{qc},{i},{q})")
    if name == "PolynomialQuotientLength":
        L, d, q = arguments
        return ("(" + _and(f"({q})=0", f"Le({L},{d})") + ") \\/ ("
                + _and(f"~(({q})=0)", f"({q})+({d})=({L})") + ")")
    if name == "FpPolynomialDivisionExecution":
        p, ab, ac, L, bb, bc, d, qb, qc, q, rb, rc, R = arguments
        b, k, pb, pc, ub, uc, t = fresh(7)
        data = _and(f"BetaAt({bb},{bc},0,{b})", f"FpInv({p},{b},{k})",
            f"FpPolynomialQuotientPrefix({p},{k},{ab},{ac},{bb},{bc},S ({d}),{qb},{qc},{q})",
            f"FpConvolutionPrefix({p},{qb},{qc},{q},{bb},{bc},S ({d}),{pb},{pc},{L})",
            f"FpCoefficientSubtraction({p},{ab},{ac},{pb},{pc},{ub},{uc},{L})",
            f"FpPolynomialTrim({p},{ub},{uc},{L},{t},{rb},{rc},{R})")
        return _and(f"BetaPrefixInto({ab},{ac},{L},{p})", f"BetaPrefixInto({bb},{bc},S ({d}),{p})",
            f"PolynomialQuotientLength({L},{d},{q})", f"exists {b} {k} {pb} {pc} {ub} {uc} {t}. {data}")
    raise AssertionError("unreviewed working definition: " + name)


def test_all_historical_objects_routes_and_expansion_arrows_are_literal():
    prior, _, _ = previous_graph.reviewed_registry()
    current, order, layers = graph.reviewed_registry()
    assert definitions.HISTORICAL_DEFINITIONS_BY_NAME is PRIOR
    assert len(PRIOR) == len(prior) == 390
    assert len(ALL) == len(current) == len({item.stable_id for item in ALL.values()}) == 397
    assert all(ALL[name] is item for name, item in PRIOR.items())
    assert all(current[name] == record for name, record in prior.items())
    assert sum(len(item["dependencies"]) for item in prior.values()) == 844
    assert sum(len(item["dependencies"]) for item in current.values()) == 865
    seen = set()
    for name in order:
        assert set(current[name]["dependencies"]) <= seen
        assert layers[name] == max((layers[parent] + 1 for parent in current[name]["dependencies"]), default=0)
        seen.add(name)
    assert tuple(item.stable_id for item in NEW) == tuple(f"ND{i:04d}" for i in range(334, 341))
    assert tuple(item.name for item in NEW) == tuple(row[0] for row in EXPECTED)
    assert definitions.EUCLIDEAN_REGISTRIES == (("polynomial-euclidean-division", NEW),)
    assert graph.DEFAULT_REGISTRIES == previous_graph.DEFAULT_REGISTRIES + definitions.EUCLIDEAN_REGISTRIES
    with pytest.raises(TypeError):
        ALL["Unreviewed"] = NEW[0]


def test_notation_import_cannot_invoke_new_theorem_factories(monkeypatch):
    def reject(*args, **kwargs):
        pytest.fail("a definition import tried to construct theorem rows")
    for module in (definitions.representation, definitions.division):
        name = "make_" + module.__name__.removesuffix("_candidate") + "_candidate_theorems"
        assert callable(getattr(module, name))
        monkeypatch.setattr(module, name, reject)
    path = Path(definitions.__file__)
    spec = importlib.util.spec_from_file_location("_working_notation_import", path)
    private = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), private.__dict__)
    assert len(private.EUCLIDEAN_DEFINITIONS) == 7


def test_new_definition_asts_are_distinct_from_every_inherited_identity():
    prior = {}
    for item in PRIOR.values():
        prior.setdefault(item.arity, set()).add(FormulaArena().freeze(item.template_formula).to_json())
    for item in NEW:
        identity = FormulaArena().freeze(item.template_formula).to_json()
        assert identity not in prior.get(item.arity, set()), item.name
        prior.setdefault(item.arity, set()).add(identity)


@pytest.mark.parametrize("name,parameters,builder,dependencies", EXPECTED, ids=[row[0] for row in EXPECTED])
def test_exact_public_and_independent_lower_vocabulary_expansions(name, parameters, builder, dependencies):
    item = ALL[name]
    assert item.parameters == parameters and item.conceptual_dependencies == dependencies
    public = parse_formula_in_context(builder(*parameters, tag="independent_public", variables=parameters), list(parameters))
    _same_ast(public, item.template_formula)
    lower = dict(ALL)
    lower.pop(name)
    _same_ast(public, _parse(_independent(name, parameters, parameters), parameters, lower))
    _same_ast(public, _parse(_call(name, *parameters), parameters))


@pytest.mark.parametrize("name,parameters,builder,dependencies", EXPECTED, ids=[row[0] for row in EXPECTED])
@pytest.mark.parametrize("kind", ("compound", "large", "zero", "repeated", "reversed"))
def test_binder_safe_compound_and_double_and_add_numeral_roundtrips(name, parameters, builder, dependencies, kind):
    choices = {"compound": ("S (x+y)", "x*y", "x+y"), "large": (str(2**96 + 17), "x+y", "y"),
               "zero": ("0",), "repeated": ("x+y",), "reversed": ("y", "x")}[kind]
    arguments = tuple(choices[index % len(choices)] for index in range(len(parameters)))
    context = ("unused_outer", "x", "unused_middle", "y", "unused_last")
    public = builder(*arguments, tag="roundtrip", variables=context)
    _same_ast(parse_formula_in_context(public, list(context)), _parse(_call(name, *arguments), context))
    _same_ast(parse_formula_in_context(public, list(context)), _parse(_independent(name, arguments, context), context))
    _same_ast(parse_formula_in_context("forall unused_outer. forall x. exists y. (" + public + ")", []),
              _parse("forall unused_outer. forall x. exists y. " + _call(name, *arguments)))


@pytest.mark.parametrize("name,parameters,builder,dependencies", EXPECTED, ids=[row[0] for row in EXPECTED])
def test_generated_public_binders_reject_capture(name, parameters, builder, dependencies):
    source = builder(*parameters, tag="capture_audit", variables=parameters)
    binders = sorted({name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", source) for name in clause.split()})
    assert binders and not set(binders) & set(parameters)
    for binder in dict.fromkeys((binders[0], binders[len(binders)//2], binders[-1])):
        with pytest.raises(ValueError, match="captures"):
            builder(*parameters, tag="capture_audit", variables=(*parameters, binder))
        arguments = (binder,) * len(parameters)
        context = ("unused", binder, "other_unused")
        _same_ast(_parse(_call(name, *arguments), context), _parse(_independent(name, arguments, context), context))


@pytest.mark.parametrize("item", NEW, ids=lambda item: item.name)
def test_every_expansion_arrow_is_present_in_the_actual_formula(item):
    for name in item.conceptual_dependencies:
        child = ALL[name]
        compact = _FormulaCompactor((child,)).compact(item.template_source)
        assert compact["exact_ast_equivalence"] is True
        assert child.stable_id in compact["statement_definition_uses"], (item.name, name)


@pytest.mark.parametrize("item", NEW, ids=lambda item: item.name)
def test_new_template_compaction_reexpands_to_exact_original_ast(item):
    compact = _FormulaCompactor(NEW).compact(item.template_source)
    assert compact["exact_ast_equivalence"] is True
    assert item.stable_id in compact["statement_definition_uses"]
    _same_ast(_parse(compact["defined_statement"], tuple(compact["free_names"])),
              parse_formula_in_context(item.template_source, list(compact["free_names"])))


@pytest.mark.parametrize("name", ("Prime", "FpRepresentedDegree", "PolynomialEquivalent", "FpPolyProduct"))
def test_division_execution_does_not_assume_its_correctness_or_degree_conclusions(name):
    item = ALL["FpPolynomialDivisionExecution"]
    assert name not in item.conceptual_dependencies
    compact = _FormulaCompactor((ALL[name],)).compact(item.template_source)
    assert ALL[name].stable_id not in compact["statement_definition_uses"]


@pytest.mark.parametrize("item", NEW, ids=lambda item: item.name)
@pytest.mark.parametrize("delta", (-1, 1))
def test_named_arities_reject_missing_or_implicit_parameters(item, delta):
    with pytest.raises(ParseError, match="expects"):
        _LocalDefinedParser(_call(item.name, *(("x",) * (item.arity + delta))), ALL).parse()


@pytest.mark.parametrize("bad", (None, True, "PolynomialEquivalent", ["PolynomialEquivalent"], ("",), (True,)))
def test_closure_input_contract_is_strict(bad):
    with pytest.raises(ValueError, match="exact tuple"):
        definitions.definition_closure(bad)


def test_definition_closure_has_no_forward_edges_and_rejects_unknown_names():
    ordered = definitions.definition_closure(tuple(item.name for item in NEW))
    seen = set()
    for item in ordered:
        assert set(item.conceptual_dependencies) <= seen
        seen.add(item.name)
    assert len(ordered) == len(seen) and set(item.name for item in NEW) <= seen
    with pytest.raises(ValueError, match="unknown or cyclic"):
        definitions.definition_closure(("Absent",))


@dataclass(frozen=True)
class SyntaxRow:
    name: str
    statement: str
    dependencies: tuple[str, ...]
    body: tuple[str, ...]
    summary: str


def test_each_new_name_actually_compacts_a_working_theorem_statement():
    # Factories produce source syntax only. This is not a kernel proof test.
    rows = (*definitions.representation.make_prime_field_polynomial_representation_candidate_theorems(SyntaxRow),
            *definitions.division.make_prime_field_polynomial_division_candidate_theorems(SyntaxRow))
    compactor = _FormulaCompactor(NEW)
    remaining = {item.stable_id for item in NEW}
    for row in rows:
        compact = compactor.compact(row.statement)
        assert compact["exact_ast_equivalence"] is True
        _same_ast(_parse(compact["defined_statement"], tuple(compact["free_names"])),
                  parse_formula_in_context(row.statement, list(compact["free_names"])))
        remaining.difference_update(compact["statement_definition_uses"])
        if not remaining:
            break
    assert not remaining
