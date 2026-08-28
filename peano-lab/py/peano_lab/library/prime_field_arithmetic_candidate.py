"""Canonical arithmetic of the prime field, as conservative HA relations.

An operation is its actual bounded congruence graph, not a supplied field-law
certificate.  The field interpretation requires the separate Prime(p) guard;
several algebraic consequences are valid already for arbitrary moduli.  This
candidate layer is k=1 infrastructure, not the prime-power extension theorem.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from ..kernel.formulas import parse_formula_in_context
from ..kernel.terms import parse_term_in_context, pretty_term
from .finite_fold_surface import _identifier


def _and(*parts: str) -> str:
    result = f"({parts[-1]})"
    for part in reversed(parts[:-1]):
        result = f"(({part}) /\\ ({result}))"
    return result


def _lt(a: str, b: str, tag: str) -> str:
    return f"exists pfa_gap_{tag}. pfa_gap_{tag} + S ({a}) = ({b})"


def _mod(p: str, a: str, b: str, tag: str) -> str:
    u, v = f"pfa_offset_left_{tag}", f"pfa_offset_right_{tag}"
    return f"exists {u} {v}. ({a}) + ({p}) * {u} = ({b}) + ({p}) * {v}"


def _prime(p: str, tag: str) -> str:
    a, b = f"pfa_factor_left_{tag}", f"pfa_factor_right_{tag}"
    return f"~(({p}) = 1) /\\ forall {a} {b}. ({p}) = {a} * {b} -> {a} = 1 \\/ {b} = 1"


def _coprime(a: str, b: str, tag: str) -> str:
    d, x, y = (f"pfa_{role}_{tag}" for role in ("divisor", "left_factor", "right_factor"))
    return f"forall {d}. (exists {x}. ({a}) = {d} * {x}) -> (exists {y}. ({b}) = {d} * {y}) -> {d} = 1"


def _carrier(p: str, a: str, tag: str) -> str:
    return _and(_prime(p, tag + "prime"), _lt(a, p, tag + "bound"))


def _residue(p: str, n: str, r: str, tag: str) -> str:
    return _and(_lt(r, p, tag + "bound"), _mod(p, n, r, tag + "congruence"))


def _add(p: str, a: str, b: str, c: str, tag: str) -> str:
    return _and(_lt(a, p, tag + "left"), _lt(b, p, tag + "right"),
                _residue(p, f"({a}) + ({b})", c, tag + "result"))


def _mul(p: str, a: str, b: str, c: str, tag: str) -> str:
    return _and(_lt(a, p, tag + "left"), _lt(b, p, tag + "right"),
                _residue(p, f"({a}) * ({b})", c, tag + "result"))


def _neg(p: str, a: str, b: str, tag: str) -> str:
    return _add(p, a, b, "0", tag + "addition")


def _inv(p: str, a: str, b: str, tag: str) -> str:
    return _and(f"~(({a}) = 0)", _mul(p, a, b, "1", tag + "multiplication"))


def _public(builder: Callable[..., str], arguments: tuple[str, ...], *,
            tag: str, variables: tuple[str, ...]) -> str:
    if not isinstance(variables, tuple) or not variables:
        raise ValueError("prime-field context must be a nonempty tuple")
    context = tuple(_identifier(v, "prime-field context variable") for v in variables)
    if len(set(context)) != len(context):
        raise ValueError("prime-field context variables must be distinct")
    safe_tag = _identifier(tag, "prime-field binder tag")
    if any(not isinstance(value, str) for value in arguments):
        raise ValueError("prime-field arguments must be Peano term strings")
    terms = tuple(parse_term_in_context(value, list(context)) for value in arguments)
    sources = tuple("(" + pretty_term(term, list(context)).replace("·", "*") + ")" for term in terms)
    formula = builder(*sources, safe_tag)
    binders = {name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", formula)
               for name in clause.split()}
    if binders.intersection(context):
        raise ValueError("generated prime-field binder captures a context variable")
    parse_formula_in_context(formula, list(context))
    return formula


def prime_field_carrier_relation(p: str, a: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Actual prime modulus and canonical natural representative 0 <= a < p."""
    return _public(_carrier, (p, a), tag=tag, variables=variables)


def prime_field_residue_relation(p: str, n: str, r: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Canonical bounded representative of a natural number modulo p."""
    return _public(_residue, (p, n, r), tag=tag, variables=variables)


def prime_field_add_relation(p: str, a: str, b: str, c: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Bounded operands and result, with actual a+b congruent to c."""
    return _public(_add, (p, a, b, c), tag=tag, variables=variables)


def prime_field_multiply_relation(p: str, a: str, b: str, c: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Bounded operands and result, with actual a*b congruent to c."""
    return _public(_mul, (p, a, b, c), tag=tag, variables=variables)


def prime_field_negate_relation(p: str, a: str, b: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Actual bounded additive inverse: Add(p,a,b,0)."""
    return _public(_neg, (p, a, b), tag=tag, variables=variables)


def prime_field_inverse_relation(p: str, a: str, b: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Actual bounded multiplicative inverse, with the nonzero input explicit."""
    return _public(_inv, (p, a, b), tag=tag, variables=variables)


def _call(name: str, *terms: str) -> tuple[str, ...]:
    return tuple(f"specialize {name} ({term})" for term in terms) + (f"apply {name}",)


def _intro(*names: str) -> tuple[str, ...]:
    return tuple("intro " + name for name in names)


def _parts(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_right" * i for i in range(count - 1))


def _part(name: str, count: int, index: int) -> str:
    return name + "_right" * index + ("_left" if index < count - 1 else "")


def _residue_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    # Reuse the exact inherited Hensel residue-existence and binary
    # residue-functionality statements; do not enroll renamed copies.
    return (
        spec(
            "prime_field_mod_of_equal",
            f"forall p a b. a = b -> ({_mod('p','a','b','equal')})",
            ("mod_eq_refl",),
            _intro("p", "a", "b", "heq") + ("rewrite heq",) + _call("mod_eq_refl", "p", "b"),
            "Equality gives genuine balanced modular congruence.",
        ),
        spec(
            "prime_field_zero_below_prime",
            f"forall p. ({_prime('p','zero_domain')}) -> ({_lt('0','p','zero_bound')})",
            ("prime_nonzero", "one_le_of_ne_zero"),
            _intro("p", "hp") + _call("one_le_of_ne_zero", "p") + ("intro hz",)
            + _call("prime_nonzero", "p") + ("exact hp", "exact hz"),
            "Zero is a canonical representative at every prime, including two.",
        ),
        spec(
            "prime_field_residue_reflexive",
            f"forall p a. ({_lt('a','p','reflexive_bound')}) -> ({_residue('p','a','a','reflexive')})",
            ("mod_eq_refl",),
            _intro("p", "a", "ha") + ("split", "exact ha") + _call("mod_eq_refl", "p", "a"),
            "Every bounded representative represents itself, including zero.",
        ),
        spec(
            "prime_field_residue_input_equal",
            f"forall p n m r. n = m -> ({_residue('p','m','r','input_equal_source')}) -> ({_residue('p','n','r','input_equal_target')})",
            (), _intro("p", "n", "m", "r", "heq", "hr") + ("rewrite heq", "exact hr"),
            "Equality transports the dividend of an actual residue graph.",
        ),
        spec(
            "prime_field_residue_congruence_transport",
            f"forall p n m r. ({_mod('p','n','m','transport')}) -> ({_residue('p','m','r','transport_source')}) -> ({_residue('p','n','r','transport_result')})",
            ("mod_eq_trans",),
            _intro("p", "n", "m", "r", "hmod", "hr") + ("cases hr", "split", "exact hr_left")
            + _call("mod_eq_trans", "p", "n", "m", "r") + ("exact hmod", "exact hr_right"),
            "Balanced congruence transports canonical residues; no quotient oracle is assumed.",
        ),
        spec(
            "prime_field_residue_bounded_value",
            f"forall p a r. ({_lt('a','p','bounded_value')}) -> ({_residue('p','a','r','bounded_result')}) -> r = a",
            ("binary_canonical_residue_functional", "prime_field_residue_reflexive"),
            _intro("p", "a", "r", "ha", "hr")
            + _call("binary_canonical_residue_functional", "p", "a", "r", "a") + ("exact hr",)
            + _call("prime_field_residue_reflexive", "p", "a") + ("exact ha",),
            "No two distinct representatives below p denote the same residue class.",
        ),
        spec(
            "prime_field_residue_modulus_zero",
            f"forall p. ({_prime('p','modulus_domain')}) -> ({_residue('p','p','0','modulus_zero')})",
            ("prime_field_zero_below_prime", "zero_add"),
            _intro("p", "hp") + ("split",)
            + _call("prime_field_zero_below_prime", "p") + ("exact hp", "exists 0", "exists 1", "simp [zero_add]"),
            "The modulus itself has canonical residue zero, the characteristic-p boundary.",
        ),
    )


def _binary_rows(spec: Callable[..., Any], operation: str) -> tuple[Any, ...]:
    graph, symbol, comm = (_add, "+", "add_comm") if operation == "add" else (_mul, "*", "mul_comm")
    name = "prime_field_" + operation
    expression = "a " + symbol + " b"
    return (
        spec(
            name + "_exists",
            f"forall p a b. ({_prime('p',operation+'domain')}) -> ({_lt('a','p',operation+'left')}) -> ({_lt('b','p',operation+'right')}) -> exists c. ({graph('p','a','b','c',operation+'exists')})",
            ("prime_nonzero", "hensel_canonical_residue_exists"),
            _intro("p", "a", "b", "hp", "ha", "hb")
            + (f"have hr : exists c. ({_residue('p',expression,'c',operation+'residue')})",)
            + _call("hensel_canonical_residue_exists", "p", expression) + ("intro hz",)
            + _call("prime_nonzero", "p") + ("exact hp", "exact hz", "cases hr", "exists x", "split", "exact ha", "split", "exact hb", "exact hr_witness"),
            f"Construct the unique canonical {operation} output for every pair of residues.",
        ),
        spec(
            name + "_functional",
            f"forall p a b c d. ({graph('p','a','b','c',operation+'first')}) -> ({graph('p','a','b','d',operation+'second')}) -> c = d",
            ("binary_canonical_residue_functional",),
            _intro("p", "a", "b", "c", "d", "hc", "hd") + _parts("hc", 3) + _parts("hd", 3)
            + _call("binary_canonical_residue_functional", "p", expression, "c", "d")
            + ("exact hc_right_right", "exact hd_right_right"),
            f"The actual bounded {operation} graph is functional without any field-law premise.",
        ),
        spec(
            name + "_exists_unique",
            f"forall p a b. ({_prime('p',operation+'unique_domain')}) -> ({_lt('a','p',operation+'unique_left')}) -> ({_lt('b','p',operation+'unique_right')}) -> exists c. ({graph('p','a','b','c',operation+'chosen')}) /\\ forall d. ({graph('p','a','b','d',operation+'comparison')}) -> d = c",
            (name + "_exists", name + "_functional"),
            _intro("p", "a", "b", "hp", "ha", "hb")
            + (f"have hc : exists c. ({graph('p','a','b','c',operation+'choice')})",)
            + _call(name + "_exists", "p", "a", "b") + ("exact hp", "exact ha", "exact hb", "cases hc", "exists x", "split", "exact hc_witness")
            + _intro("d", "hd") + _call(name + "_functional", "p", "a", "b", "d", "x")
            + ("exact hd", "exact hc_witness"),
            f"Existence and uniqueness of canonical prime-field {operation} are both proved.",
        ),
        spec(
            name + "_commutative",
            f"forall p a b c. ({graph('p','a','b','c',operation+'comm_source')}) -> ({graph('p','b','a','c',operation+'comm_target')})",
            (comm, "prime_field_residue_input_equal"),
            _intro("p", "a", "b", "c", "h") + _parts("h", 3)
            + ("split", "exact h_right_left", "split", "exact h_left")
            + _call("prime_field_residue_input_equal", "p", "b " + symbol + " a", expression, "c")
            + _call(comm, "b", "a") + ("exact h_right_right",),
            f"Commutativity of actual canonical {operation}, not an assumed table axiom.",
        ),
    )


def _associative_row(spec: Callable[..., Any], operation: str) -> Any:
    graph, symbol, assoc, congruence = ((_add, "+", "add_assoc", "mod_eq_add") if operation == "add"
                                      else (_mul, "*", "mul_assoc", "mod_eq_mul"))
    left, right = f"(a {symbol} b) {symbol} c", f"a {symbol} (b {symbol} c)"
    relations = (graph("p", "a", "b", "x", operation + "assoc_first"),
                 graph("p", "x", "c", "u", operation + "assoc_left"),
                 graph("p", "b", "c", "y", operation + "assoc_second"),
                 graph("p", "a", "y", "v", operation + "assoc_right"))
    body = _intro("p", "a", "b", "c", "x", "y", "u", "v", "hfirst", "hleft", "hsecond", "hright")
    for h in ("hfirst", "hleft", "hsecond", "hright"):
        body += _parts(h, 4)
    body += (f"have hl : {_residue('p',left,'u',operation+'assoc_raw_left')}", "split", "exact hleft_right_right_left")
    body += _call("mod_eq_trans", "p", left, f"x {symbol} c", "u")
    body += _call(congruence, "p", f"a {symbol} b", "x", "c", "c")
    body += ("exact hfirst_right_right_right",) + _call("mod_eq_refl", "p", "c")
    body += ("exact hleft_right_right_right",)
    body += (f"have hr : {_residue('p',right,'v',operation+'assoc_raw_right')}", "split", "exact hright_right_right_left")
    body += _call("mod_eq_trans", "p", right, f"a {symbol} y", "v")
    body += _call(congruence, "p", "a", "a", f"b {symbol} c", "y")
    body += _call("mod_eq_refl", "p", "a") + ("exact hsecond_right_right_right", "exact hright_right_right_right")
    body += _call("binary_canonical_residue_functional", "p", left, "u", "v") + ("exact hl",)
    body += _call("prime_field_residue_input_equal", "p", left, right, "v")
    body += _call(assoc, "a", "b", "c") + ("exact hr",)
    return spec(
        "prime_field_" + operation + "_associative",
        "forall p a b c x y u v. " + " -> ".join(f"({r})" for r in relations) + " -> u = v",
        (congruence, "mod_eq_refl", "mod_eq_trans", assoc,
         "binary_canonical_residue_functional", "prime_field_residue_input_equal"),
        body,
        f"Both bracketings of three canonical {operation} operands give the same actual result.",
    )


def _distributive_row(spec: Callable[..., Any], side: str) -> Any:
    left = side == "left"
    raw_left = "a * (b + c)" if left else "(b + c) * a"
    raw_right = "a * b + a * c" if left else "b * a + c * a"
    multiplier = ("a", "s") if left else ("s", "a")
    factors1 = ("a", "b") if left else ("b", "a")
    factors2 = ("a", "c") if left else ("c", "a")
    mulcong, distributive = ("mod_eq_mul_left", "mul_add") if left else ("mod_eq_mul_right", "add_mul")
    relations = (_add("p", "b", "c", "s", side + "distribution_sum"),
                 _mul("p", *multiplier, "u", side + "distribution_left"),
                 _mul("p", *factors1, "x", side + "distribution_first"),
                 _mul("p", *factors2, "y", side + "distribution_second"),
                 _add("p", "x", "y", "v", side + "distribution_right"))
    body = _intro("p", "a", "b", "c", "s", "x", "y", "u", "v", "hsum", "hleft", "hfirst", "hsecond", "hright")
    for h in ("hsum", "hleft", "hfirst", "hsecond", "hright"):
        body += _parts(h, 4)
    body += (f"have hl : {_residue('p',raw_left,'u',side+'distribution_raw_left')}", "split", "exact hleft_right_right_left")
    body += _call("mod_eq_trans", "p", raw_left, " * ".join(multiplier), "u")
    body += _call(mulcong, "p", "b + c", "s", "a") + ("exact hsum_right_right_right", "exact hleft_right_right_right")
    body += (f"have hr : {_residue('p',raw_right,'v',side+'distribution_raw_right')}", "split", "exact hright_right_right_left")
    body += _call("mod_eq_trans", "p", raw_right, "x + y", "v")
    body += _call("mod_eq_add", "p", " * ".join(factors1), "x", " * ".join(factors2), "y")
    body += ("exact hfirst_right_right_right", "exact hsecond_right_right_right", "exact hright_right_right_right")
    body += _call("binary_canonical_residue_functional", "p", raw_left, "u", "v") + ("exact hl",)
    body += _call("prime_field_residue_input_equal", "p", raw_left, raw_right, "v")
    body += _call(distributive, *(('a', 'b', 'c') if left else ('b', 'c', 'a'))) + ("exact hr",)
    return spec(
        "prime_field_" + side + "_distributive",
        "forall p a b c s x y u v. " + " -> ".join(f"({r})" for r in relations) + " -> u = v",
        (mulcong, "mod_eq_trans", "mod_eq_add", distributive,
         "binary_canonical_residue_functional", "prime_field_residue_input_equal"),
        body,
        f"Actual {side} distributivity of multiplication over addition on bounded representatives.",
    )


def _identity_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "prime_field_add_zero_right",
            f"forall p a. ({_prime('p','add_zero_domain')}) -> ({_lt('a','p','add_zero_bound')}) -> ({_add('p','a','0','a','add_zero')})",
            ("prime_field_zero_below_prime", "prime_field_mod_of_equal"),
            _intro("p", "a", "hp", "ha") + ("split", "exact ha", "split")
            + _call("prime_field_zero_below_prime", "p") + ("exact hp", "split", "exact ha")
            + _call("prime_field_mod_of_equal", "p", "a + 0", "a") + ("apply PA3",),
            "Natural zero is the actual additive identity, not an arbitrary chosen code.",
        ),
        spec(
            "prime_field_add_zero_left",
            f"forall p a. ({_prime('p','zero_add_domain')}) -> ({_lt('a','p','zero_add_bound')}) -> ({_add('p','0','a','a','zero_add')})",
            ("prime_field_add_commutative", "prime_field_add_zero_right"),
            _intro("p", "a", "hp", "ha") + _call("prime_field_add_commutative", "p", "a", "0", "a")
            + _call("prime_field_add_zero_right", "p", "a") + ("exact hp", "exact ha"),
            "Zero is also the left additive identity on every canonical representative.",
        ),
        spec(
            "prime_field_multiply_one_right",
            f"forall p a. ({_prime('p','multiply_one_domain')}) -> ({_lt('a','p','multiply_one_bound')}) -> ({_mul('p','a','1','a','multiply_one')})",
            ("prime_two_le", "prime_field_mod_of_equal", "mul_one"),
            _intro("p", "a", "hp", "ha") + ("split", "exact ha", "split")
            + _call("prime_two_le", "p") + ("exact hp", "split", "exact ha")
            + _call("prime_field_mod_of_equal", "p", "a * 1", "a") + _call("mul_one", "a"),
            "Natural one is the actual multiplicative identity, including at p=2.",
        ),
        spec(
            "prime_field_multiply_one_left",
            f"forall p a. ({_prime('p','one_multiply_domain')}) -> ({_lt('a','p','one_multiply_bound')}) -> ({_mul('p','1','a','a','one_multiply')})",
            ("prime_field_multiply_commutative", "prime_field_multiply_one_right"),
            _intro("p", "a", "hp", "ha") + _call("prime_field_multiply_commutative", "p", "a", "1", "a")
            + _call("prime_field_multiply_one_right", "p", "a") + ("exact hp", "exact ha"),
            "One is also the left multiplicative identity.",
        ),
        spec(
            "prime_field_multiply_zero_right",
            f"forall p a. ({_prime('p','multiply_zero_domain')}) -> ({_lt('a','p','multiply_zero_bound')}) -> ({_mul('p','a','0','0','multiply_zero')})",
            ("prime_field_zero_below_prime", "prime_field_mod_of_equal"),
            _intro("p", "a", "hp", "ha")
            + (f"have hz : {_lt('0','p','multiply_zero_canonical')}",)
            + _call("prime_field_zero_below_prime", "p") + ("exact hp", "split", "exact ha", "split", "exact hz", "split", "exact hz")
            + _call("prime_field_mod_of_equal", "p", "a * 0", "0") + ("apply PA5",),
            "Multiplication by the actual zero representative produces zero.",
        ),
        spec(
            "prime_field_multiply_zero_left",
            f"forall p a. ({_prime('p','zero_multiply_domain')}) -> ({_lt('a','p','zero_multiply_bound')}) -> ({_mul('p','0','a','0','zero_multiply')})",
            ("prime_field_multiply_commutative", "prime_field_multiply_zero_right"),
            _intro("p", "a", "hp", "ha") + _call("prime_field_multiply_commutative", "p", "a", "0", "0")
            + _call("prime_field_multiply_zero_right", "p", "a") + ("exact hp", "exact ha"),
            "Zero is absorbing on both sides of multiplication.",
        ),
        spec(
            "prime_field_add_cancel_left",
            f"forall p a b c z. ({_add('p','a','b','z','cancel_add_first')}) -> ({_add('p','a','c','z','cancel_add_second')}) -> b = c",
            ("mod_eq_bounded_unique", "mod_eq_add_cancel_left", "mod_eq_trans", "mod_eq_symm"),
            _intro("p", "a", "b", "c", "z", "hb", "hc") + _parts("hb", 4) + _parts("hc", 4)
            + _call("mod_eq_bounded_unique", "p", "b", "c") + ("exact hb_right_left", "exact hc_right_left")
            + _call("mod_eq_add_cancel_left", "p", "a", "b", "c")
            + _call("mod_eq_trans", "p", "a + b", "z", "a + c") + ("exact hb_right_right_right",)
            + _call("mod_eq_symm", "p", "a + c", "z") + ("exact hc_right_right_right",),
            "Additive cancellation follows from genuine balanced congruence cancellation and canonical bounds.",
        ),
    )


def _inverse_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "prime_field_negate_exists",
            f"forall p a. ({_prime('p','negate_domain')}) -> ({_lt('a','p','negate_input')}) -> exists b. ({_neg('p','a','b','negate_exists')})",
            ("signed_integer_floor_exists", "prime_nonzero", "prime_field_zero_below_prime", "add_assoc", "add_comm"),
            _intro("p", "a", "hp", "ha")
            + (f"have hf : exists q n r. (0 + p * n = (a + p * q) + r /\\ ({_lt('r','p','negate_floor')}))",)
            + _call("signed_integer_floor_exists", "0", "a", "p") + ("intro hz",)
            + _call("prime_nonzero", "p") + ("exact hp", "exact hz", "cases hf", "cases hf_witness", "cases hf_witness_witness", "cases hf_witness_witness_witness",
              "exists x2", "split", "exact ha", "split", "exact hf_witness_witness_witness_right", "split")
            + _call("prime_field_zero_below_prime", "p") + ("exact hp", "exists x", "exists x1", "trans (a + p * x) + x2", "simp [add_assoc, add_comm]", "symm", "exact hf_witness_witness_witness_left"),
            "Construct a bounded additive inverse by actual signed floor division; the zero input is included.",
        ),
        spec(
            "prime_field_negate_functional",
            f"forall p a b c. ({_neg('p','a','b','negate_first')}) -> ({_neg('p','a','c','negate_second')}) -> b = c",
            ("prime_field_add_cancel_left",),
            _intro("p", "a", "b", "c", "hb", "hc") + _call("prime_field_add_cancel_left", "p", "a", "b", "c", "0")
            + ("exact hb", "exact hc"),
            "Actual additive inverses are unique among canonical representatives.",
        ),
        spec(
            "prime_field_negate_exists_unique",
            f"forall p a. ({_prime('p','negate_unique_domain')}) -> ({_lt('a','p','negate_unique_input')}) -> exists b. ({_neg('p','a','b','negate_chosen')}) /\\ forall c. ({_neg('p','a','c','negate_other')}) -> c = b",
            ("prime_field_negate_exists", "prime_field_negate_functional"),
            _intro("p", "a", "hp", "ha") + (f"have hb : exists b. ({_neg('p','a','b','negate_choice')})",)
            + _call("prime_field_negate_exists", "p", "a") + ("exact hp", "exact ha", "cases hb", "exists x", "split", "exact hb_witness")
            + _intro("c", "hc") + _call("prime_field_negate_functional", "p", "a", "c", "x") + ("exact hc", "exact hb_witness"),
            "Every element, including zero, has a unique actual additive inverse.",
        ),
        spec(
            "prime_field_inverse_exists",
            f"forall p a. ({_prime('p','inverse_domain')}) -> ({_lt('a','p','inverse_input')}) -> ~(a = 0) -> exists b. ({_inv('p','a','b','inverse_exists')})",
            ("prime_bounded_nonzero_mod_inverse", "prime_two_le"),
            _intro("p", "a", "hp", "ha", "hn")
            + (f"have hi : exists b. ~(b = 0) /\\ (({_lt('b','p','inverse_bound')}) /\\ ({_mod('p','a*b','1','inverse_mod')}))",)
            + _call("prime_bounded_nonzero_mod_inverse", "p", "a")
            + ("exact hp", "exact hn", "exact ha", "cases hi", "cases hi_witness", "cases hi_witness_right", "exists x", "split", "exact hn", "split", "exact ha", "split", "exact hi_witness_right_left", "split")
            + _call("prime_two_le", "p") + ("exact hp", "exact hi_witness_right_right"),
            "Every nonzero representative has an actual bounded multiplicative inverse, uniformly at every prime.",
        ),
        spec(
            "prime_field_inverse_functional",
            f"forall p a b c. ({_inv('p','a','b','inverse_first')}) -> ({_inv('p','a','c','inverse_second')}) -> b = c",
            ("bounded_mod_inverse_unique",),
            _intro("p", "a", "b", "c", "hb", "hc") + _parts("hb", 5) + _parts("hc", 5)
            + _call("bounded_mod_inverse_unique", "p", "a", "b", "c")
            + ("exact hb_right_right_left", "exact hc_right_right_left", "exact hb_right_right_right_right", "exact hc_right_right_right_right"),
            "Multiplicative inverses are unique as bounded natural representatives.",
        ),
        spec(
            "prime_field_inverse_exists_unique",
            f"forall p a. ({_prime('p','inverse_unique_domain')}) -> ({_lt('a','p','inverse_unique_input')}) -> ~(a = 0) -> exists b. ({_inv('p','a','b','inverse_chosen')}) /\\ forall c. ({_inv('p','a','c','inverse_other')}) -> c = b",
            ("prime_field_inverse_exists", "prime_field_inverse_functional"),
            _intro("p", "a", "hp", "ha", "hn") + (f"have hb : exists b. ({_inv('p','a','b','inverse_choice')})",)
            + _call("prime_field_inverse_exists", "p", "a") + ("exact hp", "exact ha", "exact hn", "cases hb", "exists x", "split", "exact hb_witness")
            + _intro("c", "hc") + _call("prime_field_inverse_functional", "p", "a", "c", "x") + ("exact hc", "exact hb_witness"),
            "Proved unique inverse existence has exactly the nonzero carrier domain, not an odd-prime or supplied-inverse premise.",
        ),
        spec(
            "prime_field_zero_has_no_multiplicative_inverse",
            f"forall p b. ({_prime('p','zero_inverse_domain')}) -> ~({_mul('p','0','b','1','zero_inverse')})",
            ("prime_field_multiply_zero_left", "prime_field_multiply_functional", "succ_ne_zero"),
            _intro("p", "b", "hp", "hm") + ("have hcopy : " + _mul('p','0','b','1','zero_inverse_copy'), "exact hm")
            + _parts("hcopy", 3) + ("have hbad : 1 = 0",)
            + _call("prime_field_multiply_functional", "p", "0", "b", "1", "0") + ("exact hm",)
            + _call("prime_field_multiply_zero_left", "p", "b") + ("exact hp", "exact hcopy_right_left")
            + _call("succ_ne_zero", "0") + ("exact hbad",),
            "Zero has no product equal to one; this follows from multiplication, not from the inverse definition's guard.",
        ),
        spec(
            "prime_field_inverse_output_nonzero",
            f"forall p a b. ({_prime('p','inverse_output_domain')}) -> ({_inv('p','a','b','inverse_output')}) -> ~(b = 0)",
            ("prime_field_zero_has_no_multiplicative_inverse", "prime_field_multiply_commutative"),
            _intro("p", "a", "b", "hp", "hi", "hz") + ("cases hi",)
            + _call("prime_field_zero_has_no_multiplicative_inverse", "p", "a") + ("exact hp",)
            + (f"have hm : {_mul('p','b','a','1','inverse_swapped')}",)
            + _call("prime_field_multiply_commutative", "p", "a", "b", "1") + ("exact hi_right", "rewrite hz at hm", "rewrite hz at hm", "exact hm"),
            "An actual inverse is itself nonzero, so reciprocal inversion has the correct domain.",
        ),
        spec(
            "prime_field_inverse_symmetric",
            f"forall p a b. ({_prime('p','inverse_symmetric_domain')}) -> ({_inv('p','a','b','inverse_symmetric_source')}) -> ({_inv('p','b','a','inverse_symmetric_target')})",
            ("prime_field_inverse_output_nonzero", "prime_field_multiply_commutative"),
            _intro("p", "a", "b", "hp", "hi") + ("split", "intro hz")
            + _call("prime_field_inverse_output_nonzero", "p", "a", "b") + ("exact hp", "exact hi", "exact hz", "cases hi")
            + _call("prime_field_multiply_commutative", "p", "a", "b", "1") + ("exact hi_right",),
            "Inversion is symmetric on the nonzero elements, with both domains proved.",
        ),
        spec(
            "prime_field_nonzero_coprime",
            f"forall p a. ({_prime('p','coprime_domain')}) -> ({_lt('a','p','coprime_bound')}) -> ~(a = 0) -> ({_coprime('a','p','coprime_result')})",
            ("prime_field_inverse_exists", "mod_inverse_implies_coprime"),
            _intro("p", "a", "hp", "ha", "hn") + (f"have hi : exists b. ({_inv('p','a','b','coprime_inverse')})",)
            + _call("prime_field_inverse_exists", "p", "a") + ("exact hp", "exact ha", "exact hn", "cases hi") + _parts("hi_witness", 5)
            + _call("mod_inverse_implies_coprime", "a", "p", "x")
            + ("exact hi_witness_right_right_right_right",),
            "Every nonzero canonical element is genuinely coprime to its prime modulus.",
        ),
        spec(
            "prime_field_multiply_cancel_nonzero_left",
            f"forall p a b c z. ({_prime('p','cancel_mul_domain')}) -> ~(a = 0) -> ({_mul('p','a','b','z','cancel_mul_first')}) -> ({_mul('p','a','c','z','cancel_mul_second')}) -> b = c",
            ("mod_eq_bounded_unique", "mod_eq_cancel_coprime", "prime_nonzero", "prime_field_nonzero_coprime", "mod_eq_trans", "mod_eq_symm"),
            _intro("p", "a", "b", "c", "z", "hp", "hn", "hb", "hc") + _parts("hb", 4) + _parts("hc", 4)
            + _call("mod_eq_bounded_unique", "p", "b", "c") + ("exact hb_right_left", "exact hc_right_left")
            + _call("mod_eq_cancel_coprime", "p", "a", "b", "c") + ("intro hz",)
            + _call("prime_nonzero", "p") + ("exact hp", "exact hz")
            + _call("prime_field_nonzero_coprime", "p", "a")
            + ("exact hp", "exact hb_left", "exact hn")
            + _call("mod_eq_trans", "p", "a * b", "z", "a * c") + ("exact hb_right_right_right",)
            + _call("mod_eq_symm", "p", "a * c", "z") + ("exact hc_right_right_right",),
            "Cancellation by any nonzero element is proved, not assumed from a field certificate.",
        ),
        spec(
            "prime_field_no_zero_divisors",
            f"forall p a b. ({_prime('p','no_zero_divisors_domain')}) -> ({_mul('p','a','b','0','no_zero_divisors_product')}) -> a = 0 \\/ b = 0",
            ("eq_decidable", "prime_field_multiply_cancel_nonzero_left", "prime_field_multiply_zero_right"),
            _intro("p", "a", "b", "hp", "hm") + ("have hcases : a = 0 \\/ ~(a = 0)",)
            + _call("eq_decidable", "a", "0") + ("cases hcases", "left", "exact hcases_left", "right")
            + _call("prime_field_multiply_cancel_nonzero_left", "p", "a", "b", "0", "0")
            + ("exact hp", "exact hcases_right", "exact hm")
            + _call("prime_field_multiply_zero_right", "p", "a") + ("exact hp", "cases hm", "exact hm_left"),
            "A zero canonical product has a zero factor, including the characteristic-two case.",
        ),
    )


def _natural_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    result = []
    for operation, symbol, graph, congruence in (("add", "+", _add, "mod_eq_add"),
                                                ("multiply", "*", _mul, "mod_eq_mul")):
        result.append(spec(
            "prime_field_residue_" + operation,
            f"forall p a b x y z. ({_residue('p','a','x',operation+'natural_left')}) -> ({_residue('p','b','y',operation+'natural_right')}) -> ({graph('p','x','y','z',operation+'natural_result')}) -> ({_residue('p','a '+symbol+' b','z',operation+'natural_homomorphism')})",
            ("mod_eq_trans", congruence),
            _intro("p", "a", "b", "x", "y", "z", "ha", "hb", "hz")
            + ("cases ha", "cases hb") + _parts("hz", 4)
            + ("split", "exact hz_right_right_left")
            + _call("mod_eq_trans", "p", "a " + symbol + " b", "x " + symbol + " y", "z")
            + _call(congruence, "p", "a", "x", "b", "y") + ("exact ha_right", "exact hb_right", "exact hz_right_right_right"),
            f"The natural-number residue map preserves actual canonical {operation}.",
        ))
    result.append(spec(
        "prime_field_positive_below_modulus_not_zero",
        f"forall p n. ({_lt('n','p','small_nonzero_bound')}) -> ~(n = 0) -> ~({_residue('p','n','0','small_nonzero')})",
        ("prime_field_residue_bounded_value",),
        _intro("p", "n", "hn", "hpositive", "hzero") + ("have heq : 0 = n",)
        + _call("prime_field_residue_bounded_value", "p", "n", "0") + ("exact hn", "exact hzero", "apply hpositive", "symm", "exact heq"),
        "No positive natural below p has residue zero; the modulus boundary is sharp.",
    ))
    return tuple(result)


def _law_clauses(p: str, tag: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Explicit field laws and their independent ordinary proof invocations.

    This relation is a conclusion of prime_field_arithmetic_laws.  It is never
    a premise of an operation constructor or of any of the component laws.
    """
    a, b, c, d, s, x, y, u, v, z = (f"pfa_law_{name}_{tag}" for name in ("a", "b", "c", "d", "s", "x", "y", "u", "v", "z"))
    clauses: list[tuple[str, tuple[str, ...]]] = [
        (_lt("0", p, tag + "zero"), _call("prime_field_zero_below_prime", p) + ("exact hp",)),
        (_lt("1", p, tag + "one"), _call("prime_two_le", p) + ("exact hp",)),
        ("~(0 = 1)", ("intro hzero_one", "have hone_zero : 1 = 0", "symm", "exact hzero_one") + _call("succ_ne_zero", "0") + ("exact hone_zero",)),
    ]
    for operation, graph in (("add", _add), ("multiply", _mul)):
        clauses.append((
            f"forall {a} {b}. ({_lt(a,p,tag+operation+'left')}) -> ({_lt(b,p,tag+operation+'right')}) -> exists {c}. ({graph(p,a,b,c,tag+operation+'chosen')}) /\\ forall {d}. ({graph(p,a,b,d,tag+operation+'other')}) -> {d} = {c}",
            _intro(a, b, "ha", "hb") + _call("prime_field_" + operation + "_exists_unique", p, a, b) + ("exact hp", "exact ha", "exact hb"),
        ))
        clauses.append((
            f"forall {a} {b} {c}. ({graph(p,a,b,c,tag+operation+'comm_first')}) -> ({graph(p,b,a,c,tag+operation+'comm_second')})",
            _call("prime_field_" + operation + "_commutative", p),
        ))
        rels = (graph(p,a,b,x,tag+operation+'assoc_first'),graph(p,x,c,u,tag+operation+'assoc_left'),
                graph(p,b,c,y,tag+operation+'assoc_second'),graph(p,a,y,v,tag+operation+'assoc_right'))
        clauses.append((
            f"forall {a} {b} {c} {x} {y} {u} {v}. " + " -> ".join(f"({r})" for r in rels) + f" -> {u} = {v}",
            _call("prime_field_" + operation + "_associative", p),
        ))
    for side in ("left", "right"):
        factors = ((a,s),(a,b),(a,c)) if side == "left" else ((s,a),(b,a),(c,a))
        rels = (_add(p,b,c,s,tag+side+'distribution_sum'),_mul(p,*factors[0],u,tag+side+'distribution_left'),
                _mul(p,*factors[1],x,tag+side+'distribution_first'),_mul(p,*factors[2],y,tag+side+'distribution_second'),
                _add(p,x,y,v,tag+side+'distribution_right'))
        clauses.append((
            f"forall {a} {b} {c} {s} {x} {y} {u} {v}. " + " -> ".join(f"({r})" for r in rels) + f" -> {u} = {v}",
            _call("prime_field_" + side + "_distributive", p),
        ))
    for label, graph in (("add_zero_right", _add(p,a,"0",a,tag+'add_zero_right')),
                         ("add_zero_left", _add(p,"0",a,a,tag+'add_zero_left')),
                         ("multiply_one_right", _mul(p,a,"1",a,tag+'multiply_one_right')),
                         ("multiply_one_left", _mul(p,"1",a,a,tag+'multiply_one_left')),
                         ("multiply_zero_right", _mul(p,a,"0","0",tag+'multiply_zero_right')),
                         ("multiply_zero_left", _mul(p,"0",a,"0",tag+'multiply_zero_left'))):
        clauses.append((f"forall {a}. ({_lt(a,p,tag+label+'input')}) -> ({graph})",
                        _intro(a,"ha") + _call("prime_field_" + label,p,a) + ("exact hp","exact ha")))
    for label, graph in (("negate", _neg), ("inverse", _inv)):
        nonzero = f"~({a} = 0) -> " if label == "inverse" else ""
        clauses.append((
            f"forall {a}. ({_lt(a,p,tag+label+'input')}) -> {nonzero}exists {b}. ({graph(p,a,b,tag+label+'chosen')}) /\\ forall {c}. ({graph(p,a,c,tag+label+'other')}) -> {c} = {b}",
            _intro(a,"ha",*(('hn',) if nonzero else ())) + _call("prime_field_" + label + "_exists_unique",p,a)
            + ("exact hp","exact ha") + (("exact hn",) if nonzero else ()),
        ))
    clauses.append((
        f"forall {a} {b}. ({_mul(p,a,b,'0',tag+'nozero')}) -> {a} = 0 \\/ {b} = 0",
        _intro(a,b,"hm") + _call("prime_field_no_zero_divisors",p,a,b) + ("exact hp","exact hm"),
    ))
    return tuple(clauses)


def _laws(p: str, tag: str) -> str:
    return _and(*(formula for formula, _ in _law_clauses(p, tag)))


def prime_field_laws_relation(p: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Explicit field laws, proved from primality and never assumed by construction."""
    return _public(_laws, (p,), tag=tag, variables=variables)


def _laws_row(spec: Callable[..., Any]) -> Any:
    clauses = _law_clauses("p", "complete_laws")
    script = _intro("p", "hp")
    for index, (_, proof) in enumerate(clauses):
        if index < len(clauses) - 1:
            script += ("split",)
        script += proof
    dependencies = (
        "prime_field_zero_below_prime", "prime_two_le", "succ_ne_zero",
        "prime_field_add_exists_unique", "prime_field_add_commutative", "prime_field_add_associative",
        "prime_field_multiply_exists_unique", "prime_field_multiply_commutative", "prime_field_multiply_associative",
        "prime_field_left_distributive", "prime_field_right_distributive",
        "prime_field_add_zero_right", "prime_field_add_zero_left", "prime_field_multiply_one_right",
        "prime_field_multiply_one_left", "prime_field_multiply_zero_right", "prime_field_multiply_zero_left",
        "prime_field_negate_exists_unique", "prime_field_inverse_exists_unique", "prime_field_no_zero_divisors",
    )
    return spec(
        "prime_field_arithmetic_laws", f"forall p. ({_prime('p','complete_laws_domain')}) -> ({_laws('p','complete_laws')})",
        dependencies, script,
        "Every prime has genuine canonical field arithmetic with distinct zero/one, total unique operations, both distributive laws, additive inverses and precisely nonzero multiplicative inverses.",
    )


def make_prime_field_arithmetic_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_residue_rows(spec) + _binary_rows(spec, "add") + _binary_rows(spec, "multiply")
            + tuple(_associative_row(spec, operation) for operation in ("add", "multiply"))
            + tuple(_distributive_row(spec, side) for side in ("left", "right"))
            + _identity_rows(spec) + _inverse_rows(spec) + _natural_rows(spec) + (_laws_row(spec),))


__all__ = [
    "prime_field_carrier_relation", "prime_field_residue_relation", "prime_field_add_relation",
    "prime_field_multiply_relation", "prime_field_negate_relation", "prime_field_inverse_relation",
    "prime_field_laws_relation",
    "make_prime_field_arithmetic_candidate_theorems",
]
