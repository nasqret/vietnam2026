"""Contracts for conservative, opt-in defined predicate syntax."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Imp,
    Or,
    parse_formula,
    parse_formula_in_context,
    pretty_formula,
)
from peano_lab.kernel.terms import Add, Mul, ParseError, Succ, Var, Zero
from peano_lab.library.defined_syntax import (
    DEFINITIONS,
    DEFINITIONS_BY_NAME,
    DEFINED_SYNTAX_REGISTRY_ID,
    DEFINED_SYNTAX_REGISTRY_SHA256,
    DEFINED_SYNTAX_VERSION,
    DefinitionSpec,
    parse_defined_formula,
    parse_defined_formula_in_context,
    parse_defined_formula_with_names,
)


EXPANSIONS = (
    ("Dvd(d,n)", "exists q. n = d * q"),
    ("Lt(a,b)", "exists k. k + S a = b"),
    (
        "DivRem(n,d,q,r)",
        "n = d * q + r /\\ exists k. k + S r = d",
    ),
    (
        "Prime(p)",
        "~(p = 1) /\\ forall a b. p = a * b -> a = 1 \\/ b = 1",
    ),
    (
        "IsGCD(g,a,b)",
        "(exists x. a = g * x) /\\ (exists y. b = g * y) /\\ "
        "forall c. (exists u. a = c * u) -> "
        "(exists v. b = c * v) -> exists w. g = c * w",
    ),
    (
        "Coprime(a,b)",
        "forall c. (exists u. a = c * u) -> "
        "(exists v. b = c * v) -> c = 1",
    ),
    ("ModEq(m,a,b)", "exists u v. a + m * u = b + m * v"),
)


def test_registry_is_ordered_immutable_versioned_and_self_describing() -> None:
    assert DEFINED_SYNTAX_REGISTRY_ID == "peano-lab.defined-predicates"
    assert DEFINED_SYNTAX_VERSION == 1
    assert len(DEFINED_SYNTAX_REGISTRY_SHA256) == 64
    assert tuple(definition.name for definition in DEFINITIONS) == (
        "Dvd",
        "Lt",
        "DivRem",
        "Prime",
        "IsGCD",
        "Coprime",
        "ModEq",
    )
    assert tuple(DEFINITIONS_BY_NAME) == tuple(
        definition.name for definition in DEFINITIONS
    )
    assert len({definition.stable_id for definition in DEFINITIONS}) == len(
        DEFINITIONS
    )
    for definition in DEFINITIONS:
        assert isinstance(definition, DefinitionSpec)
        assert definition.summary
        assert definition.category
        assert definition.template_formula == parse_formula_in_context(
            definition.template_source, list(definition.parameters)
        )
        assert set(definition.conceptual_dependencies) <= set(DEFINITIONS_BY_NAME)

    with pytest.raises(FrozenInstanceError):
        DEFINITIONS[0].name = "Other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        DEFINITIONS_BY_NAME["Other"] = DEFINITIONS[0]  # type: ignore[index]


@pytest.mark.parametrize(("surface", "expanded"), EXPANSIONS)
def test_each_definition_is_exactly_its_reviewed_core_expansion(
    surface: str, expanded: str
) -> None:
    actual, names = parse_defined_formula_with_names(surface)
    expected = parse_formula_in_context(expanded, list(names))
    assert actual == expected


def test_compound_arguments_expand_simultaneously_without_capture() -> None:
    actual = parse_defined_formula(
        "forall q a. Dvd(q + a, S (q * a))"
    )
    expected = parse_formula(
        "forall q a. exists witness. S (q * a) = (q + a) * witness"
    )
    assert actual == expected

    repeated = parse_defined_formula("forall q. Dvd(q,q)")
    assert repeated == parse_formula("forall q. exists witness. q = q * witness")


def test_definitions_nest_under_all_formula_constructs() -> None:
    surface = (
        "forall n. Prime(n) -> "
        "(Dvd(2,n) \\/ (Lt(n,S n) /\\ ModEq(5,n,1)))"
    )
    expanded = (
        "forall n. "
        "(~(n = 1) /\\ forall a b. n = a * b -> a = 1 \\/ b = 1) -> "
        "((exists q. n = 2 * q) \\/ "
        "((exists k. k + S n = S n) /\\ "
        "exists u v. n + 5 * u = 1 + 5 * v))"
    )
    assert parse_defined_formula(surface) == parse_formula(expanded)


def test_with_names_preserves_surface_order_and_context_parser_is_exact() -> None:
    formula, names = parse_defined_formula_with_names("Dvd(d + n,n)")
    assert names == ("d", "n")
    rendered = pretty_formula(formula, list(names))
    assert parse_defined_formula_in_context(rendered, list(names)) == formula

    assert parse_defined_formula_in_context("Dvd(n,d)", ["d", "n"]) == (
        parse_formula_in_context("exists q. d = n * q", ["d", "n"])
    )
    with pytest.raises(ParseError, match="unknown term variable.*x"):
        parse_defined_formula_in_context("Dvd(d,x)", ["d", "n"])


def test_expansions_contain_only_the_original_kernel_ast_constructors() -> None:
    formula = parse_defined_formula(
        "forall n d q r. DivRem(n,d,q,r) -> Prime(d) -> Dvd(d,n)"
    )

    def visit_term(term: object) -> None:
        assert type(term) in {Var, Zero, Succ, Add, Mul}
        if isinstance(term, Succ):
            visit_term(term.term)
        elif isinstance(term, (Add, Mul)):
            visit_term(term.left)
            visit_term(term.right)

    def visit_formula(node: object) -> None:
        assert type(node) in {Eq, Bot, Imp, And, Or, Forall, Exists}
        if isinstance(node, Eq):
            visit_term(node.left)
            visit_term(node.right)
        elif isinstance(node, (Imp, And, Or)):
            visit_formula(node.left)
            visit_formula(node.right)
        elif isinstance(node, (Forall, Exists)):
            visit_formula(node.body)

    visit_formula(formula)


def test_core_parse_apis_do_not_enable_defined_predicates() -> None:
    with pytest.raises(ParseError):
        parse_formula("Dvd(a,b)")
    assert parse_formula("forall n. n = n") == parse_defined_formula(
        "forall n. n = n"
    )


@pytest.mark.parametrize(
    "source",
    (
        "Prime()",
        "Dvd(a)",
        "Dvd(a,b,c)",
        "DivRem(n,d,q)",
    ),
)
def test_arity_errors_are_final_and_position_bearing(source: str) -> None:
    with pytest.raises(ParseError, match=r"expects .* at column 1"):
        parse_defined_formula(source)


@pytest.mark.parametrize(
    "source",
    (
        "dvd(a,b)",
        "Unknown(a)",
        "Dvd(a b)",
        "Dvd(a,)",
        "Dvd(a,b",
    ),
)
def test_call_syntax_errors_are_final_and_position_bearing(source: str) -> None:
    with pytest.raises(ParseError, match=r"column"):
        parse_defined_formula(source)


def test_expansion_budget_is_typed_bounded_and_accumulates() -> None:
    with pytest.raises(ParseError, match=r"1-node budget.*column 1"):
        parse_defined_formula("Dvd(a,b)", expansion_budget=1)
    parse_defined_formula("Dvd(a,b)", expansion_budget=100)

    for invalid in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="positive integer"):
            parse_defined_formula("Dvd(a,b)", expansion_budget=invalid)  # type: ignore[arg-type]


def test_context_validation_matches_the_core_parser_contract() -> None:
    for invalid in (("a",), ["a", "a"], [1]):
        with pytest.raises(ValueError, match="distinct surface identifiers"):
            parse_defined_formula_in_context(  # type: ignore[arg-type]
                "Dvd(a,a)", invalid
            )
