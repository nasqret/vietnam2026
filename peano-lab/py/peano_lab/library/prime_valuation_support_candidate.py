"""Finite, distinct prime-exponent support over unchanged Heyting arithmetic.

The scalar power-valuation interface and the finite support construction are
shared mathematical prerequisites, independent of totients, LTE, squarefree
kernels and perfect-power profiles.  Authoring helpers expand existing PA
relations; they neither enroll theorems nor confer proof authority.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from ..kernel.formulas import parse_formula_in_context
from ..kernel.terms import parse_term_in_context, pretty_term
from .bertrand_power_divisibility_candidate import _power_valuation_terms
from .finite_fold_surface import _beta_at_term, _identifier, _product_relation_term
from .power_algebra_theorems import _power_terms
from .prime_factorization_permutation_candidate import (
    _injective as _inherited_injective, _preserve as _inherited_preserve,
)


def _safe(tag: str) -> str:
    return _identifier(tag, "prime valuation support binder tag")


def _and(*formulas: str) -> str:
    return formulas[0] if len(formulas) == 1 else f"(({formulas[0]}) /\\ ({_and(*formulas[1:])}))"


def _lt(a: str, b: str, tag: str) -> str:
    return f"exists pvs_gap_{tag}. pvs_gap_{tag} + S ({a}) = ({b})"


def _le(a: str, b: str, tag: str) -> str:
    return f"exists pvs_le_gap_{tag}. pvs_le_gap_{tag} + ({a}) = ({b})"


def _dvd(d: str, n: str, tag: str) -> str:
    return f"exists pvs_factor_{tag}. ({n}) = ({d}) * pvs_factor_{tag}"


def _prime(p: str, tag: str) -> str:
    a, b = f"pvs_left_{tag}", f"pvs_right_{tag}"
    return f"~(({p}) = 1) /\\ forall {a} {b}. ({p}) = {a} * {b} -> {a} = 1 \\/ {b} = 1"


def _pow(a: str, k: str, n: str, tag: str) -> str:
    return _power_terms(a, k, n, tag=f"pvs_{tag}")


def _val(p: str, n: str, e: str, tag: str) -> str:
    return _power_valuation_terms(p, n, e, tag=f"pvs_{tag}")


def _at(b: str, c: str, i: str, a: str, tag: str) -> str:
    return _beta_at_term(b, c, i, a, tag=f"pvs_{tag}", avoid=())


def _product(b: str, c: str, l: str, n: str, tag: str) -> str:
    return _product_relation_term(b, c, l, n, tag=f"pvs_{tag}", avoid=())


def _injective(b: str, c: str, l: str, tag: str) -> str:
    return _inherited_injective(b, c, l, f"pvs_{tag}")


def _preserve(b: str, c: str, d: str, e: str, l: str, tag: str) -> str:
    return _inherited_preserve(b, c, d, e, l, f"pvs_{tag}")


def _entry(n: str, pb: str, pc: str, eb: str, ec: str, vb: str, vc: str,
           i: str, p: str, e: str, v: str, tag: str) -> str:
    return _and(
        _at(pb, pc, i, p, tag + "prime"),
        _at(eb, ec, i, e, tag + "exponent"),
        _at(vb, vc, i, v, tag + "power"),
        _prime(p, tag + "domain"), f"~({e} = 0)",
        _val(p, n, e, tag + "valuation"), _pow(p, e, v, tag + "value"),
    )


def _entries(n: str, pb: str, pc: str, eb: str, ec: str, vb: str, vc: str, l: str, tag: str) -> str:
    i, p, e, v = (f"pvs_{role}_{tag}" for role in ("index", "prime", "exponent", "power"))
    row = _entry(n, pb, pc, eb, ec, vb, vc, i, p, e, v, tag)
    return f"forall {i}. ({_lt(i, l, tag + 'index')}) -> exists {p} {e} {v}. ({row})"


def _cover(n: str, pb: str, pc: str, l: str, tag: str) -> str:
    p, i = f"pvs_divisor_{tag}", f"pvs_position_{tag}"
    return (
        f"forall {p}. ({_prime(p, tag + 'prime')}) -> ({_dvd(p, n, tag + 'divides')}) -> "
        f"exists {i}. ({_lt(i, l, tag + 'bound')}) /\\ ({_at(pb, pc, i, p, tag + 'entry')})"
    )


def _support(n: str, pb: str, pc: str, eb: str, ec: str, vb: str, vc: str, l: str, tag: str) -> str:
    return _and(
        f"~(({n}) = 0)", _injective(pb, pc, l, tag + "distinct"),
        _entries(n, pb, pc, eb, ec, vb, vc, l, tag + "entries"),
        _cover(n, pb, pc, l, tag + "cover"), _product(vb, vc, l, n, tag + "product"),
    )


def _strict_cofactor(n: str, p: str, e: str, P: str, u: str, tag: str) -> str:
    return _and(
        _prime(p, tag + "prime"), f"~({e} = 0)", _val(p, n, e, tag + "valuation"),
        _pow(p, e, P, tag + "power"), f"({n}) = ({P}) * ({u})", f"~({u} = 0)",
        f"~({_dvd(p,u,tag+'nondivisor')})", _lt(u, n, tag + "descent"),
    )


def _support_exists(n: str, tag: str) -> str:
    return f"exists pb pc eb ec vb vc l. ({_support(n,'pb','pc','eb','ec','vb','vc','l',tag)})"


def _public(builder: Callable[..., str], arguments: tuple[str, ...], *, tag: str, variables: tuple[str, ...]) -> str:
    if not isinstance(variables, tuple) or not variables:
        raise ValueError("prime support context must be a nonempty tuple")
    context = tuple(_identifier(value, "prime support context variable") for value in variables)
    if len(set(context)) != len(context):
        raise ValueError("prime support context variables must be distinct")
    terms = tuple(parse_term_in_context(value, list(context)) for value in arguments)
    sources = tuple("(" + pretty_term(value, list(context)).replace("·", "*") + ")" for value in terms)
    formula = builder(*sources, _safe(tag))
    binders = {
        name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", formula)
        for name in clause.split()
    }
    if binders.intersection(context):
        raise ValueError("generated prime support binder captures a context variable")
    parse_formula_in_context(formula, list(context))
    return formula


def prime_exponent_entries_relation(
    n: str, pb: str, pc: str, eb: str, ec: str, vb: str, vc: str, l: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Actual prime, positive valuation and corresponding power at each index."""
    return _public(_entries, (n, pb, pc, eb, ec, vb, vc, l), tag=tag, variables=variables)


def prime_divisor_support_relation(
    n: str, pb: str, pc: str, l: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Every prime divisor of n has an actual position in the finite prefix."""
    return _public(_cover, (n, pb, pc, l), tag=tag, variables=variables)


def prime_valuation_support_relation(
    n: str, pb: str, pc: str, eb: str, ec: str, vb: str, vc: str, l: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Positive n, distinct actual prime valuations, full support and product n."""
    return _public(_support, (n, pb, pc, eb, ec, vb, vc, l), tag=tag, variables=variables)


def _call(name: str, *terms: str) -> tuple[str, ...]:
    return tuple(f"specialize {name} ({term})" for term in terms) + (f"apply {name}",)


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _cases(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_witness" * i for i in range(count))


def _parts(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_right" * i for i in range(count - 1))


def _part(name: str, count: int, index: int) -> str:
    return name + "_right" * index + ("_left" if index < count - 1 else "")


def _rewrite(equation: str, formula: str, variable: str, at: str | None = None) -> tuple[str, ...]:
    count = len(re.findall(rf"\b{re.escape(variable)}\b", formula))
    return (f"rewrite {equation}" + (f" at {at}" if at else ""),) * count


def _scalar_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "prime_valuation_exponent_eq_transport",
            f"forall p n e f. e = f -> ({_val('p','n','e','transport_source')}) -> ({_val('p','n','f','transport_target')})",
            (),
            _intro("p", "n", "e", "f", "heq", "hval")
            + _rewrite("heq", _val('p','n','e','transport_source'), "e", "hval") + ("exact hval",),
            "Equality transports an actual bounded valuation exponent without changing its prime or value.",
        ),
        spec(
            "prime_valuation_zero_of_nondivisor",
            f"forall p n. ({_prime('p','zero_domain')}) -> ~(n = 0) -> ~({_dvd('p','n','zero_nondivisor')}) -> ({_val('p','n','0','zero_value')})",
            ("power_valuation_exists", "prime_power_valuation_zero_iff_not_divides", "prime_valuation_exponent_eq_transport"),
            _intro("p", "n", "hp", "hn", "hnot")
            + (f"have hex : exists e. ({_val('p','n','e','zero_exists')})",)
            + _call("power_valuation_exists", "p", "n") + ("cases hex",)
            + (f"have hiff : (x = 0 -> ~({_dvd('p','n','zero_forward')})) /\\ (~({_dvd('p','n','zero_reverse')}) -> x = 0)",)
            + _call("prime_power_valuation_zero_iff_not_divides", "p", "n", "x")
            + ("exact hp", "exact hn", "exact hex_witness", "cases hiff")
            + _call("prime_valuation_exponent_eq_transport", "p", "n", "x", "0")
            + ("apply hiff_right", "exact hnot", "exact hex_witness"),
            "Construct valuation zero for a positive value not divisible by the actual prime.",
        ),
        spec(
            "prime_valuation_nondivisor_of_zero",
            f"forall p n. ({_prime('p','nondivisor_domain')}) -> ~(n = 0) -> ({_val('p','n','0','nondivisor_value')}) -> ~({_dvd('p','n','nondivisor_result')})",
            ("prime_power_valuation_zero_iff_not_divides",),
            _intro("p", "n", "hp", "hn", "hval")
            + (f"have hiff : (0 = 0 -> ~({_dvd('p','n','nondivisor_forward')})) /\\ (~({_dvd('p','n','nondivisor_reverse')}) -> 0 = 0)",)
            + _call("prime_power_valuation_zero_iff_not_divides", "p", "n", "0")
            + ("exact hp", "exact hn", "exact hval", "cases hiff", "intro hdiv", "apply hiff_left", "refl", "exact hdiv"),
            "Valuation zero excludes divisibility, with both intended domain guards explicit.",
        ),
        spec(
            "prime_power_valuation_pow_value",
            f"forall p a k e z f. ({_prime('p','pow_domain')}) -> ~(a = 0) -> ({_val('p','a','e','pow_base')}) -> ({_pow('a','k','z','pow_source')}) -> ({_val('p','z','f','pow_output')}) -> f = k * e",
            ("pow_zero", "prime_power_valuation_one_zero", "mul_zero_left", "pow_successor_decompose", "power_valuation_exists", "one_le_of_ne_zero", "pow_nonzero_of_one_le", "power_valuation_value_eq_transport", "prime_power_valuation_mul", "mul_succ_left"),
            _intro("p", "a", "k") + ("induction k",)
            + _intro("e", "z", "f", "hp", "ha", "hbase", "hpow", "hval")
            + ("have hz : z = 1",) + _call("pow_zero", "a", "0", "z") + ("refl", "exact hpow", "trans 0")
            + _call("prime_power_valuation_one_zero", "p", "z", "f")
            + ("exact hz", "exact hp", "exact hval", "symm", "apply mul_zero_left")
            + _intro("e", "z", "f", "hp", "ha", "hbase", "hpow", "hval")
            + (f"have hprev : exists r. ({_pow('a','k','r','pow_predecessor')}) /\\ z = r * a",)
            + _call("pow_successor_decompose", "a", "k", "S k", "z")
            + ("refl", "exact hpow", "cases hprev", "cases hprev_witness")
            + (f"have hv : exists j. ({_val('p','x','j','pow_predecessor_val')})",)
            + _call("power_valuation_exists", "p", "x") + ("cases hv", "have hindex : x1 = k * e")
            + _call("IH", "e", "x", "x1")
            + ("exact hp", "exact ha", "exact hbase", "exact hprev_witness_left", "exact hv_witness")
            + ("have hx : ~(x = 0)", "intro hxzero")
            + _call("pow_nonzero_of_one_le", "a", "k", "x")
            + _call("one_le_of_ne_zero", "a")
            + ("exact ha", "exact hprev_witness_left", "exact hxzero")
            + (f"have hproduct : {_val('p','x * a','f','pow_product')}",)
            + _call("power_valuation_value_eq_transport", "p", "z", "x * a", "f")
            + ("exact hprev_witness_right", "exact hval", "trans x1 + e")
            + _call("prime_power_valuation_mul", "p", "x", "a", "x1", "e", "f")
            + ("exact hp", "exact hx", "exact ha", "exact hv_witness", "exact hbase", "exact hproduct",
               "rewrite hindex", "symm", "apply mul_succ_left"),
            "The exact valuation of any witnessed nonnegative power is its exponent times the base valuation; zero powers are included.",
        ),
        spec(
            "prime_power_valuation_pow",
            f"forall p a k e z. ({_prime('p','pow_construct_domain')}) -> ~(a = 0) -> ({_val('p','a','e','pow_construct_base')}) -> ({_pow('a','k','z','pow_construct_source')}) -> ({_val('p','z','k * e','pow_construct_output')})",
            ("power_valuation_exists", "prime_power_valuation_pow_value", "prime_valuation_exponent_eq_transport"),
            _intro("p", "a", "k", "e", "z", "hp", "ha", "hbase", "hpow")
            + (f"have hv : exists f. ({_val('p','z','f','pow_construct_exists')})",)
            + _call("power_valuation_exists", "p", "z") + ("cases hv",)
            + _call("prime_valuation_exponent_eq_transport", "p", "z", "x", "k * e")
            + _call("prime_power_valuation_pow_value", "p", "a", "k", "e", "z", "x")
            + ("exact hp", "exact ha", "exact hbase", "exact hpow", "exact hv_witness", "exact hv_witness"),
            "Construct the actual maximal valuation graph of a witnessed power, not merely an equation between supplied output valuations.",
        ),
    )


def _prime_power_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "pow_positive_exponent_base_divides",
            f"forall a k z. ~(k = 0) -> ({_pow('a','k','z','positive_power')}) -> ({_dvd('a','z','positive_divides')})",
            ("nonzero_is_succ", "pow_successor_decompose", "mul_comm"),
            _intro("a", "k", "z", "hk", "hpow")
            + ("have hs : exists j. k = S j",) + _call("nonzero_is_succ", "k") + ("exact hk", "cases hs",)
            + (f"have hprev : exists r. ({_pow('a','x','r','positive_previous')}) /\\ z = r * a",)
            + _call("pow_successor_decompose", "a", "x", "k", "z")
            + ("exact hs_witness", "exact hpow", "cases hprev", "cases hprev_witness", "exists x1", "trans x1 * a", "exact hprev_witness_right", "apply mul_comm"),
            "Every positive power has its base as an actual divisor; no prime or positivity oracle is needed.",
        ),
        spec(
            "prime_valuation_distinct_prime_power_zero",
            f"forall p q k z. ({_prime('p','distinct_base')}) -> ({_prime('q','distinct_valuation')}) -> ~(q = p) -> ({_pow('p','k','z','distinct_power')}) -> ({_val('q','z','0','distinct_zero')})",
            ("prime_nonzero", "distinct_primes_left_not_divide_right", "prime_valuation_zero_of_nondivisor", "prime_power_valuation_pow", "prime_valuation_exponent_eq_transport"),
            _intro("p", "q", "k", "z", "hp", "hq", "hne", "hpow")
            + ("have hpzero : ~(p = 0)", "intro hz") + _call("prime_nonzero", "p") + ("exact hp", "exact hz")
            + (f"have hbase : {_val('q','p','0','distinct_base_zero')}",)
            + _call("prime_valuation_zero_of_nondivisor", "q", "p") + ("exact hq", "exact hpzero", "intro hdiv")
            + _call("distinct_primes_left_not_divide_right", "q", "p") + ("exact hq", "exact hp", "exact hne", "exact hdiv")
            + _call("prime_valuation_exponent_eq_transport", "q", "z", "k * 0", "0")
            + ("apply PA5",) + _call("prime_power_valuation_pow", "q", "p", "k", "0", "z")
            + ("exact hq", "exact hpzero", "exact hbase", "exact hpow"),
            "A power of a prime has zero valuation at every genuinely distinct prime, including exponent zero.",
        ),
        spec(
            "prime_divisor_of_prime_power",
            f"forall p q k z. ({_prime('p','prime_power_base')}) -> ({_prime('q','prime_power_divisor')}) -> ({_pow('p','k','z','prime_power_value')}) -> ({_dvd('q','z','prime_power_divides')}) -> q = p",
            ("eq_decidable", "prime_nonzero", "one_le_of_ne_zero", "pow_nonzero_of_one_le", "prime_valuation_distinct_prime_power_zero", "prime_valuation_nondivisor_of_zero"),
            _intro("p", "q", "k", "z", "hp", "hq", "hpow", "hdiv")
            + ("specialize eq_decidable q", "specialize eq_decidable p", "cases eq_decidable", "exact eq_decidable_left", "exfalso")
            + _call("prime_valuation_nondivisor_of_zero", "q", "z") + ("exact hq", "intro hz")
            + _call("pow_nonzero_of_one_le", "p", "k", "z") + _call("one_le_of_ne_zero", "p")
            + ("intro hpzero",) + _call("prime_nonzero", "p") + ("exact hp", "exact hpzero", "exact hpow", "exact hz")
            + _call("prime_valuation_distinct_prime_power_zero", "p", "q", "k", "z")
            + ("exact hp", "exact hq", "exact eq_decidable_right", "exact hpow", "exact hdiv"),
            "Every actual prime divisor of a witnessed prime power is its base prime.",
        ),
        spec(
            "prime_valuation_product_zero_left",
            f"forall p a b e. ({_prime('p','zero_product_domain')}) -> ~(a = 0) -> ~(b = 0) -> ({_val('p','a','0','zero_product_left')}) -> ({_val('p','b','e','zero_product_right')}) -> ({_val('p','a * b','e','zero_product_result')})",
            ("power_valuation_exists", "prime_power_valuation_mul", "zero_add", "prime_valuation_exponent_eq_transport"),
            _intro("p", "a", "b", "e", "hp", "ha", "hb", "hleft", "hright")
            + (f"have hv : exists f. ({_val('p','a * b','f','zero_product_exists')})",)
            + _call("power_valuation_exists", "p", "a * b") + ("cases hv",)
            + _call("prime_valuation_exponent_eq_transport", "p", "a * b", "x", "e")
            + ("trans 0 + e",) + _call("prime_power_valuation_mul", "p", "a", "b", "0", "e", "x")
            + ("exact hp", "exact ha", "exact hb", "exact hleft", "exact hright", "exact hv_witness", "apply zero_add", "exact hv_witness"),
            "Multiplying by a positive valuation-zero factor preserves the actual maximal exponent.",
        ),
        spec(
            "prime_valuation_strip_other_prime",
            f"forall p q k z u e. ({_prime('p','strip_base')}) -> ({_prime('q','strip_other')}) -> ~(q = p) -> ~(u = 0) -> ({_pow('p','k','z','strip_power')}) -> ({_val('q','u','e','strip_source')}) -> ({_val('q','z * u','e','strip_result')})",
            ("prime_valuation_product_zero_left", "prime_nonzero", "one_le_of_ne_zero", "pow_nonzero_of_one_le", "prime_valuation_distinct_prime_power_zero"),
            _intro("p", "q", "k", "z", "u", "e", "hp", "hq", "hne", "hu", "hpow", "hval")
            + _call("prime_valuation_product_zero_left", "q", "z", "u", "e") + ("exact hq", "intro hz")
            + _call("pow_nonzero_of_one_le", "p", "k", "z") + _call("one_le_of_ne_zero", "p")
            + ("intro hpzero",) + _call("prime_nonzero", "p") + ("exact hp", "exact hpzero", "exact hpow", "exact hz", "exact hu")
            + _call("prime_valuation_distinct_prime_power_zero", "p", "q", "k", "z")
            + ("exact hp", "exact hq", "exact hne", "exact hpow", "exact hval"),
            "Removing a full prime power does not change any other prime valuation of the remaining positive cofactor.",
        ),
    )


def _support_entry_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    codes = ("pb", "pc", "eb", "ec", "vb", "vc", "l")
    chosen = _entry("n", *codes[:6], "i", "p", "e", "v", "chosen")
    unpack = _cases("hrow", 3) + _parts("hrow_witness_witness_witness", 7)
    fields = tuple(_part("hrow_witness_witness_witness", 7, i) for i in range(7))
    copy_first_five = tuple(command for field in fields[:5] for command in ("split", f"exact {field}"))
    return (
        spec(
            "prime_exponent_entries_prime_divides",
            f"forall n pb pc eb ec vb vc l i q. ({_entries('n',*codes,'divisor_entries')}) -> ({_lt('i','l','divisor_index')}) -> ({_at('pb','pc','i','q','divisor_at')}) -> ({_prime('q','entry_prime')}) /\\ ({_dvd('q','n','entry_divisor')})",
            ("beta_at_unique", "power_valuation_nonzero_exponent_divides_base"),
            _intro("n", *codes, "i", "q", "hentries", "hi", "hat")
            + (f"have hrow : exists p e v. ({chosen})",) + _call("hentries", "i") + ("exact hi",) + unpack
            + ("have heq : q = x",) + _call("beta_at_unique", "pb", "pc", "i", "q", "x")
            + ("exact hat", f"exact {fields[0]}", "split")
            + _rewrite("heq", _prime("q", "entry_prime"), "q") + (f"exact {fields[3]}", "rewrite heq")
            + _call("power_valuation_nonzero_exponent_divides_base", "x", "n", "x1")
            + (f"exact {fields[5]}", f"exact {fields[4]}"),
            "Every decoded support entry is a prime that genuinely divides the supported value.",
        ),
        spec(
            "prime_exponent_entries_restore_prime_power",
            f"forall n u p k P pb pc eb ec vb vc l. ({_prime('p','restore_domain')}) -> ~(u = 0) -> n = P * u -> ({_pow('p','k','P','restore_power')}) -> ~({_dvd('p','u','restore_fresh')}) -> ({_entries('u',*codes,'restore_source')}) -> ({_entries('n',*codes,'restore_target')})",
            ("power_valuation_nonzero_exponent_divides_base", "power_valuation_value_eq_transport", "prime_valuation_strip_other_prime"),
            _intro("n", "u", "p", "k", "P", *codes, "hp", "hu", "hn", "hpow", "hfresh", "hentries", "i", "hi")
            + (f"have hrow : exists p e v. ({_entry('u',*codes[:6],'i','p','e','v','restore_chosen')})",)
            + _call("hentries", "i") + ("exact hi",) + unpack
            + ("have hneq : ~(x = p)", "intro heq", f"have hdiv : {_dvd('x','u','restore_entry_divisor')}")
            + _call("power_valuation_nonzero_exponent_divides_base", "x", "u", "x1")
            + (f"exact {fields[5]}", f"exact {fields[4]}", "rewrite heq at hdiv", "apply hfresh", "exact hdiv", "exists x", "exists x1", "exists x2") + copy_first_five
            + ("split",) + _call("power_valuation_value_eq_transport", "x", "P * u", "n", "x1")
            + ("symm", "exact hn",) + _call("prime_valuation_strip_other_prime", "p", "x", "k", "P", "u", "x1")
            + ("exact hp", f"exact {fields[3]}", "exact hneq", "exact hu", "exact hpow", f"exact {fields[5]}", f"exact {fields[6]}"),
            "Restoring a removed full prime power preserves every old positive valuation, because its base prime is absent from the cofactor.",
        ),
        spec(
            "prime_exponent_entries_recode",
            f"forall n pb pc eb ec vb vc l qb qc fb fc wb wc. ({_entries('n',*codes,'recode_source')}) -> ({_preserve('pb','pc','qb','qc','l','recode_primes')}) -> ({_preserve('eb','ec','fb','fc','l','recode_exponents')}) -> ({_preserve('vb','vc','wb','wc','l','recode_powers')}) -> ({_entries('n','qb','qc','fb','fc','wb','wc','l','recode_target')})",
            (),
            _intro("n", *codes, "qb", "qc", "fb", "fc", "wb", "wc", "hentries", "hprimes", "hexponents", "hpowers", "i", "hi")
            + (f"have hrow : exists p e v. ({chosen})",) + _call("hentries", "i") + ("exact hi",) + unpack
            + ("exists x", "exists x1", "exists x2", "split") + _call("hprimes", "i", "x") + ("exact hi", f"exact {fields[0]}", "split")
            + _call("hexponents", "i", "x1") + ("exact hi", f"exact {fields[1]}", "split")
            + _call("hpowers", "i", "x2") + ("exact hi", f"exact {fields[2]}")
            + tuple(command for field in fields[3:6] for command in ("split", f"exact {field}")) + (f"exact {fields[6]}",),
            "Actual prefix-preserving beta recodings preserve all prime/exponent/power data, without a sequence oracle.",
        ),
        spec(
            "prime_exponent_entries_append",
            f"forall n pb pc eb ec vb vc l p e v. ({_entries('n',*codes,'append_old')}) -> ({_entry('n',*codes[:6],'l','p','e','v','append_last')}) -> ({_entries('n',*codes[:6],'S l','append_next')})",
            ("finite_lt_succ_eq_or_lt",),
            _intro("n", *codes, "p", "e", "v", "hentries", "hlast", "i", "hi")
            + (f"have hcase : i = l \\/ ({_lt('i','l','append_case')})",) + _call("finite_lt_succ_eq_or_lt", "l", "i")
            + ("exact hi", "cases hcase", "exists p", "exists e", "exists v")
            + _rewrite("hcase_left", _entry("n",*codes[:6],"i","p","e","v","append_result"), "i")
            + ("exact hlast",) + _call("hentries", "i") + ("exact hcase_right",),
            "A real final beta entry extends the prime-exponent data by one, including the empty-prefix boundary.",
        ),
        spec(
            "prime_valuation_support_one",
            _support("1", "0", "0", "0", "0", "0", "0", "0", "unit_support"),
            ("factor_permutation_below_zero_impossible", "divisor_one", "factor_permutation_product_exists", "beta_product_zero"),
            ("split", "intro hz", "apply PA1", "exact hz", "split")
            + _intro("i", "j", "p", "hi", "hj", "hleft", "hright")
            + ("exfalso",) + _call("factor_permutation_below_zero_impossible", "i") + ("exact hi", "split", "intro i", "intro hi", "exfalso")
            + _call("factor_permutation_below_zero_impossible", "i") + ("exact hi", "split", "intro p", "intro hp", "intro hdiv", "exfalso", "cases hp", "apply hp_left")
            + _call("divisor_one", "p") + ("exact hdiv", f"have hprod : exists v. ({_product('0','0','0','v','unit_product')})")
            + _call("factor_permutation_product_exists", "0", "0", "0") + ("cases hprod", "have heq : x = 1")
            + _call("beta_product_zero", "0", "0", "x") + ("exact hprod_witness",)
            + _rewrite("heq", _product("0","0","0","x","unit_product_witness"), "x", "hprod_witness") + ("exact hprod_witness",),
            "One has the actual empty distinct-prime support and empty product one, with no fictitious prime or positive valuation.",
        ),
    )


def _support_descent_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    codes = ("pb", "pc", "eb", "ec", "vb", "vc", "l")
    cofactor_formula = _and(_pow("x","x1","P","strict_exact_power"), "n = P * u", "~(u = 0)", "~(" + _dvd("x","u","strict_exact_fresh") + ")")
    return (
        spec(
            "prime_valuation_support_value_eq_transport",
            f"forall n m pb pc eb ec vb vc l. n = m -> ({_support('n',*codes,'support_equal_source')}) -> ({_support('m',*codes,'support_equal_target')})",
            (),
            _intro("n", "m", *codes, "heq", "hsupport")
            + _rewrite("heq", _support("n",*codes,"support_equal"), "n", "hsupport") + ("exact hsupport",),
            "An equal positive value retains exactly the same actual prime, exponent and product codes.",
        ),
        spec(
            "prime_valuation_strict_cofactor_exists",
            f"forall n. ~(n = 0) -> ~(n = 1) -> exists p e P u. ({_strict_cofactor('n','p','e','P','u','strict_cofactor')})",
            ("prime_divisor_exists", "power_valuation_exists", "prime_divisor_power_valuation_nonzero", "power_valuation_exact_cofactor", "pow_positive_exponent_base_divides", "divisor_one", "proper_factor_lt", "mul_comm"),
            _intro("n", "hn", "hunit")
            + (f"have hp : exists p. ({_prime('p','strict_prime')}) /\\ ({_dvd('p','n','strict_divisor')})",)
            + _call("prime_divisor_exists", "n") + ("exact hn", "exact hunit", "cases hp", "cases hp_witness")
            + (f"have he : exists e. ({_val('x','n','e','strict_valuation')})",)
            + _call("power_valuation_exists", "x", "n") + ("cases he", "have henz : ~(x1 = 0)", "intro hezero")
            + _call("prime_divisor_power_valuation_nonzero", "x", "n", "x1")
            + ("exact hp_witness_left", "exact hn", "exact he_witness", "exact hp_witness_right", "exact hezero")
            + (f"have hc : exists P u. {cofactor_formula}",)
            + _call("power_valuation_exact_cofactor", "x", "n", "x1")
            + ("exact hp_witness_left", "exact hn", "exact he_witness") + _cases("hc", 2) + _parts("hc_witness_witness", 4)
            + ("have hpnonunit : ~(x2 = 1)", "intro hPone", f"have hbase : {_dvd('x','x2','strict_base_divisor')}")
            + _call("pow_positive_exponent_base_divides", "x", "x1", "x2")
            + ("exact henz", "exact hc_witness_witness_left", "rewrite hPone at hbase", "cases hp_witness_left", "apply hp_witness_left_left")
            + _call("divisor_one", "x") + ("exact hbase", "exists x", "exists x1", "exists x2", "exists x3", "split", "exact hp_witness_left", "split", "exact henz", "split", "exact he_witness", "split", "exact hc_witness_witness_left", "split", "exact hc_witness_witness_right_left", "split", "exact hc_witness_witness_right_right_left", "split", "exact hc_witness_witness_right_right_right")
            + _call("proper_factor_lt", "n", "x3", "x2")
            + ("exact hn", "trans x2 * x3", "exact hc_witness_witness_right_left", "apply mul_comm", "exact hpnonunit"),
            "Every positive nonunit has an actual full prime-power cofactor strictly smaller than itself; the exponent, power and nondivisibility are all constructed.",
        ),
    )


def _support_extend_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    old = ("pb", "pc", "eb", "ec", "vb", "vc", "l")
    new = ("x", "x1", "x2", "x3", "x4", "x5", "l")
    h = tuple(_part("hsupport", 5, i) for i in range(5))
    script = list(_intro("n", "u", "p", "k", "P", *old, "hn", "hp", "hk", "hval", "hpow", "hfresh", "heq", "hsupport") + _parts("hsupport", 5))
    for label, source, value in (("hprimecode", ("pb","pc"), "p"), ("hexpcode", ("eb","ec"), "k")):
        formula = _and(_at("a","b","l",value,label+"last"),_preserve(*source,"a","b","l",label+"prefix"))
        script += [f"have {label} : exists a b. ({formula})", *_call("beta_prefix_extend", "l", *source, value), *_cases(label,2), f"cases {label}_witness_witness"]
    formula = _and(_at("a","b","l","P","new_power_last"),_preserve("vb","vc","a","b","l","new_power_prefix"),_product("a","b","S l","u * P","new_power_product"))
    script += [f"have hpowercode : exists a b. ({formula})", *_call("beta_factor_prefix_product_append","vb","vc","l","u","P"), f"exact {h[4]}", *_cases("hpowercode",2), *_parts("hpowercode_witness_witness",3)]
    script += [f"have hrestored : {_entries('n',*old,'extend_restored')}", *_call("prime_exponent_entries_restore_prime_power","n","u","p","k","P",*old), "exact hp", f"exact {h[0]}", "exact heq", "exact hpow", "exact hfresh", f"exact {h[2]}"]
    script += [f"have hnewentries : {_entries('n',*new,'extend_recoded')}", *_call("prime_exponent_entries_recode","n",*old,*new[:6]), "exact hrestored", "exact hprimecode_witness_witness_right", "exact hexpcode_witness_witness_right", "exact hpowercode_witness_witness_right_left"]
    script += [f"have hinjective : {_injective('x','x1','l','extend_old_injective')}", *_intro("i","j","a","hi","hj","hfirst","hsecond"), *_call(h[1],"i","j","a"), "exact hi", "exact hj"]
    for index, bound, entry in (("i","hi","hfirst"),("j","hj","hsecond")):
        script += [*_call("factor_permutation_prefix_reflect","pb","pc","x","x1","l",index,"a"), "exact hprimecode_witness_witness_right", f"exact {bound}", f"exact {entry}"]
    contains = f"exists i. ({_lt('i','l','extend_contains_index')}) /\\ ({_at('x','x1','i','p','extend_contains_at')})"
    script += [f"have hnewfresh : ~({contains})", "intro hcontains", "cases hcontains", "cases hcontains_witness", f"have hdiv : ({_prime('p','extend_old_prime')}) /\\ ({_dvd('p','u','extend_old_divisor')})", *_call("prime_exponent_entries_prime_divides","u",*old,"x6","p"), f"exact {h[2]}", "exact hcontains_witness_left", *_call("factor_permutation_prefix_reflect","pb","pc","x","x1","l","x6","p"), "exact hprimecode_witness_witness_right", "exact hcontains_witness_left", "exact hcontains_witness_right", "cases hdiv", "apply hfresh", "exact hdiv_right"]
    script += [*(f"exists {value}" for value in new[:6]), "split", "exact hn", "split", *_call("finite_prefix_injective_extend_fresh","x","x1","l","p"), "exact hinjective", "exact hprimecode_witness_witness_left", "exact hnewfresh", "split", *_call("prime_exponent_entries_append","n",*new,"p","k","P"), "exact hnewentries"]
    for field in ("hprimecode_witness_witness_left", "hexpcode_witness_witness_left", "hpowercode_witness_witness_left", "hp", "hk", "hval"):
        script += ["split", f"exact {field}"]
    script += ["exact hpow", "split", *_intro("q","hq","hdiv"), "rewrite heq at hdiv", f"have hcase : ({_dvd('q','P','extend_divides_power')}) \\/ ({_dvd('q','u','extend_divides_cofactor')})", *_call("euclid_prime_dvd_product","q","P","u"), "exact hq", "exact hdiv", "cases hcase", "have hqeq : q = p", *_call("prime_divisor_of_prime_power","p","q","k","P"), "exact hp", "exact hq", "exact hpow", "exact hcase_left", "exists l", "split", *_call("le_refl","S l"), *_rewrite("hqeq",_at("x","x1","l","q","extend_cover_last"),"q"), "exact hprimecode_witness_witness_left"]
    old_member = f"exists i. ({_lt('i','l','extend_cover_old_index')}) /\\ ({_at('pb','pc','i','q','extend_cover_old_at')})"
    script += [f"have hmember : {old_member}", *_call(h[3],"q"), "exact hq", "exact hcase_right", "cases hmember", "cases hmember_witness", "exists x6", "split", *_call("le_succ","S x6","l"), "exact hmember_witness_left", *_call("hprimecode_witness_witness_right","x6","q"), "exact hmember_witness_left", "exact hmember_witness_right", "have hproducteq : u * P = n", "trans P * u", "apply mul_comm", "symm", "exact heq", *_rewrite("hproducteq",_product("x4","x5","S l","t","extend_product_value"),"t","hpowercode_witness_witness_right_right"), "exact hpowercode_witness_witness_right_right"]
    return (spec(
        "prime_valuation_support_append_full_power",
        f"forall n u p k P pb pc eb ec vb vc l. ~(n = 0) -> ({_prime('p','extend_prime')}) -> ~(k = 0) -> ({_val('p','n','k','extend_valuation')}) -> ({_pow('p','k','P','extend_power')}) -> ~({_dvd('p','u','extend_fresh')}) -> n = P * u -> ({_support('u',*old,'extend_source')}) -> exists qb qc fb fc wb wc. ({_support('n','qb','qc','fb','fc','wb','wc','S l','extend_target')})",
        ("beta_prefix_extend", "beta_factor_prefix_product_append", "prime_exponent_entries_restore_prime_power", "prime_exponent_entries_recode", "factor_permutation_prefix_reflect", "prime_exponent_entries_prime_divides", "finite_prefix_injective_extend_fresh", "prime_exponent_entries_append", "euclid_prime_dvd_product", "prime_divisor_of_prime_power", "le_refl", "le_succ", "mul_comm"),
        tuple(script),
        "Append an actual new full prime power to three beta prefixes, preserving distinctness, all exact valuations, complete divisor support and the literal finite product.",
    ),)


def _support_totality_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    factor = "hfactor_witness_witness_witness_witness"
    fields = tuple(_part(factor, 8, i) for i in range(8))
    previous = tuple(f"x{i}" for i in range(4, 11))
    rec = "hrec" + "_witness" * 7
    final_codes = tuple(f"x{i}" for i in range(11, 17))
    extended = _support("n", "a", "b", "c", "d", "e", "f", "S x10", "totality_extended")
    script = (
        _intro("B") + ("induction B",) + _intro("n", "hn", "hbound")
        + ("exfalso",) + _call("factor_permutation_below_zero_impossible", "n") + ("exact hbound",)
        + _intro("n", "hn", "hbound")
        + ("specialize eq_decidable n", "specialize eq_decidable 1", "cases eq_decidable")
        + ("exists 0",) * 7 + _call("prime_valuation_support_value_eq_transport", "1", "n", *("0",)*7)
        + ("symm", "exact eq_decidable_left", "apply prime_valuation_support_one")
        + (f"have hfactor : exists p e P u. ({_strict_cofactor('n','p','e','P','u','totality_factor')})",)
        + _call("prime_valuation_strict_cofactor_exists", "n") + ("exact hn", "exact eq_decidable_right")
        + _cases("hfactor", 4) + _parts(factor, 8)
        + (f"have hrec : {_support_exists('x3','totality_recursive')}",) + _call("IH", "x3")
        + (f"exact {fields[5]}",) + _call("lt_of_lt_of_le", "x3", "n", "B") + (f"exact {fields[7]}",)
        + _call("le_of_succ_le_succ", "n", "B") + ("exact hbound",) + _cases("hrec", 7)
        + (f"have hextended : exists a b c d e f. ({extended})",)
        + _call("prime_valuation_support_append_full_power", "n", "x3", "x", "x1", "x2", *previous)
        + ("exact hn", f"exact {fields[0]}", f"exact {fields[1]}", f"exact {fields[2]}", f"exact {fields[3]}", f"exact {fields[6]}", f"exact {fields[4]}", f"exact {rec}")
        + _cases("hextended", 6) + tuple(f"exists {code}" for code in final_codes) + ("exists S x10", "exact hextended" + "_witness"*6)
    )
    return (
        spec(
            "prime_valuation_support_bounded_exists",
            f"forall B n. ~(n = 0) -> ({_lt('n','B','totality_bound')}) -> ({_support_exists('n','totality_result')})",
            ("factor_permutation_below_zero_impossible", "eq_decidable", "prime_valuation_support_value_eq_transport", "prime_valuation_support_one", "prime_valuation_strict_cofactor_exists", "lt_of_lt_of_le", "le_of_succ_le_succ", "prime_valuation_support_append_full_power"),
            script,
            "Ordinary natural induction on an explicit upper bound constructs the whole distinct-prime support; every recursive cofactor is strictly smaller.",
        ),
        spec(
            "prime_valuation_support_exists",
            f"forall n. ~(n = 0) -> ({_support_exists('n','unrestricted_support')})",
            ("prime_valuation_support_bounded_exists", "le_refl"),
            _intro("n", "hn") + _call("prime_valuation_support_bounded_exists", "S n", "n")
            + ("exact hn",) + _call("le_refl", "S n"),
            "Every positive natural has a genuinely constructed finite list of distinct prime divisors, their positive exact valuations, corresponding powers and product equal to the input.",
        ),
    )


def make_prime_valuation_support_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Ordinary dependency-ordered candidates; separate replay/admission required."""
    return (_scalar_rows(spec) + _prime_power_rows(spec) + _support_entry_rows(spec)
            + _support_descent_rows(spec) + _support_extend_rows(spec) + _support_totality_rows(spec))


__all__ = [
    "prime_exponent_entries_relation", "prime_divisor_support_relation",
    "prime_valuation_support_relation", "make_prime_valuation_support_candidate_theorems",
]
