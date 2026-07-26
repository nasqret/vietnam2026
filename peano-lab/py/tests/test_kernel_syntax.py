"""Surface syntax and canonical-printing tests for M0."""

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
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.kernel.terms import (
    Add,
    Mul,
    ParseError,
    Succ,
    Var,
    Zero,
    parse_term,
    parse_term_in_context,
    parse_term_with_names,
    pretty_term,
)


def test_numerals_and_term_precedence() -> None:
    three = Succ(Succ(Succ(Zero())))
    assert parse_term("3") == three
    assert parse_term("x + y * 3") == Add(Var(0), Mul(Var(1), three))
    assert pretty_term(Add(Var(0), Mul(Var(1), three)), ["x", "y"]) == "x + y · 3"
    assert pretty_term(Mul(Add(Var(0), Var(1)), Var(2)), ["x", "y", "z"]) == "(x + y) · z"


def test_free_names_use_deterministic_first_occurrence_indices() -> None:
    term, names = parse_term_with_names("b + a + b")
    assert names == ("b", "a")
    assert term == Add(Add(Var(0), Var(1)), Var(0))
    assert pretty_term(term, list(names)) == "b + a + b"


def test_raw_de_bruijn_fallback_is_explicit_and_round_trips() -> None:
    assert pretty_term(Var(3), []) == "#3"
    assert parse_term("#3") == Var(3)


def test_context_parser_is_inverse_when_context_slots_are_unused_or_reordered() -> None:
    names = ["a", "b"]
    term = Add(Var(1), Var(0))
    text = pretty_term(term, names)
    assert text == "b + a"
    assert parse_term_in_context(text, names) == term

    formula = Eq(Var(1), Var(1))
    formula_text = pretty_formula(formula, names)
    assert parse_formula_in_context(formula_text, names) == formula
    with pytest.raises(ParseError, match="unknown term variable"):
        parse_term_in_context("c", names)


def test_term_printer_preserves_non_associative_ast_shape() -> None:
    right_nested = Add(Var(0), Add(Var(1), Var(2)))
    text = pretty_term(right_nested, ["x", "y", "z"])
    assert text == "x + (y + z)"
    assert parse_term(text) == right_nested


def test_ascii_and_unicode_formula_aliases_parse_identically() -> None:
    ascii_formula = "forall x. ~(S x = 0) /\\ exists y. x = y \\/ x = 0"
    unicode_formula = "∀ x. ¬(S x = 0) ∧ ∃ y. x = y ∨ x = 0"
    assert parse_formula(ascii_formula) == parse_formula(unicode_formula)


def test_quantifiers_resolve_bound_and_free_names_without_capture() -> None:
    formula, names = parse_formula_with_names(
        "forall x. x = y -> exists z. z = y"
    )
    assert names == ("y",)
    assert formula == Forall(
        Imp(Eq(Var(0), Var(1)), Exists(Eq(Var(0), Var(2))))
    )
    assert pretty_formula(formula, list(names)) == "∀ x. x = y → ∃ z. z = y"


@pytest.mark.parametrize(
    "source",
    [
        "x = x -> y = y -> z = z",
        "(x = x -> y = y) -> z = z",
        "x = x /\\ (y = y /\\ z = z)",
        "(x = x \\/ y = y) /\\ z = z",
        "forall x y. S x + y = S (x + y)",
        "exists x. false -> x = x",
    ],
)
def test_canonical_formula_round_trip(source: str) -> None:
    formula, names = parse_formula_with_names(source)
    canonical = pretty_formula(formula, list(names))
    reparsed, reparsed_names = parse_formula_with_names(canonical)
    assert reparsed == formula
    assert reparsed_names == names


def test_canonical_connective_spelling_and_precedence() -> None:
    p = Eq(Var(0), Zero())
    q = Eq(Var(1), Zero())
    r = Eq(Var(2), Zero())
    formula = Imp(And(p, Or(q, r)), Bot())
    assert pretty_formula(formula, ["p", "q", "r"]) == "¬(p = 0 ∧ (q = 0 ∨ r = 0))"


def test_ast_nodes_are_frozen() -> None:
    variable = Var(0)
    formula = Forall(Eq(variable, variable))
    with pytest.raises(FrozenInstanceError):
        variable.index = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        formula.body = Bot()  # type: ignore[misc]


def test_implication_keyword_fields_match_the_rule_names() -> None:
    atom = Eq(Zero(), Zero())
    implication = Imp(antecedent=atom, consequent=Bot())
    assert implication.left == atom
    assert implication.right == Bot()


@pytest.mark.parametrize(
    "source",
    ["", "x +", "S", "x =", "forall . x = x", "exists x x = x", "x == x"],
)
def test_parse_errors_are_final_and_position_bearing(source: str) -> None:
    parser = parse_formula if "=" in source or source.startswith(("forall", "exists")) else parse_term
    with pytest.raises(ParseError, match=r"column"):
        parser(source)


def test_formula_constructor_shapes_cover_the_object_logic() -> None:
    atom = Eq(Zero(), Zero())
    formula = Forall(Exists(Imp(And(atom, atom), Or(atom, Bot()))))
    assert parse_formula(pretty_formula(formula, [])) == formula
