"""Unsealed, genuine quotient-prefix convergent computations for G072.

The finite computation starts with the identity matrix and prepends actual
tagged quotient cells.  No determinant, coprimality, error inequality, or
best-approximation conclusion is part of the computation predicate.
"""

from __future__ import annotations

from typing import Any, Callable

from .continued_fraction_approximation_candidate import _and, _call, _context, _intro, _invariant, _le, _lt, _public_formula, _simp, _terms
from .continued_fraction_candidate import _pair_term, _packed_state, _state_at_term, _trace_term, continued_fraction
from .finite_fold_surface import _beta_at_term, _identifier
from .ha_pair_cell_seed_candidate import cell
from .matrix_lattice_data_candidate import _absolute
from .fermat_residue_product_candidate import coprime


def _names(tag: str, arguments: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    prefix = _identifier(tag, "convergent computation binder tag")
    names = tuple("cfc_" + role + "_" + prefix for role in roles)
    if set(names) & set(arguments):
        raise ValueError("convergent computation binder captures an input variable")
    return names


def _code(s: str, u: str, U: str, v: str, V: str, z: str, tag: str) -> str:
    l, r, m = _names(tag, _context(s, u, U, v, V, z), "left", "right", "matrix")
    return f"exists {l} {r} {m}. " + _and(
        f"{l} = {_pair_term(u, U)}", f"{r} = {_pair_term(v, V)}",
        f"{m} = {_pair_term(l, r)}", f"({z}) = {_pair_term(s, m)}",
    )


def _at(h: str, e: str, j: str, s: str, u: str, U: str, v: str, V: str, tag: str) -> str:
    context = _context(h, e, j, s, u, U, v, V)
    z, = _names(tag, context, "state")
    return f"exists {z}. " + _and(_code(s, u, U, v, V, z, tag + "code"),
                                  _beta_at_term(h, e, j, z, tag=tag + "entry", avoid=context + (z,)))


def _trace(s: str, h: str, e: str, k: str, u: str, U: str, v: str, V: str, tag: str) -> str:
    context = _context(s, h, e, k, u, U, v, V)
    tail, j, old, a, b, c, d, new, q = _names(tag, context, "tail", "index", "old", "a", "b", "c", "d", "new", "quotient")
    steps = f"forall {j}. ({_lt(j, k, tag + 'bound')}) -> exists {old} {a} {b} {c} {d} {new} {q}. " + _and(
        _at(h, e, j, old, a, b, c, d, tag + "previous"),
        _at(h, e, f"S {j}", new, f"({q} * {a} + {c})", f"({q} * {b} + {d})", a, b, tag + "following"),
        cell(new, q, old),
    )
    return f"exists {tail}. " + _and(
        _at(h, e, "0", tail, "1", "0", "0", "1", tag + "initial"),
        _at(h, e, k, s, u, U, v, V, tag + "terminal"), steps,
    )


def convergent_matrix_trace_relation(
    s: str, h: str, e: str, length: str, u: str, U: str, v: str, V: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Actual product of the first length quotient matrices in list s."""
    return _public_formula(_trace(*_terms((s, h, e, length, u, U, v, V), variables), tag), variables)


def convergent_matrix_state_code_relation(
    s: str, u: str, U: str, v: str, V: str, code: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Exact conservatively shared code of the tagged list and four entries."""
    return _public_formula(_code(*_terms((s, u, U, v, V, code), variables), tag), variables)


def convergent_matrix_state_at_relation(
    h: str, e: str, index: str, s: str, u: str, U: str, v: str, V: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Actual beta-decoded tagged-list/matrix state at the given index."""
    return _public_formula(_at(*_terms((h, e, index, s, u, U, v, V), variables), tag), variables)


def convergent_relation(
    s: str, index: str, numerator: str, denominator: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Actual (index+1)-step convergent; a zero numerator is permitted."""
    s, index, u, v = _terms((s, index, numerator, denominator), variables)
    U, V, h, e = _names(tag, variables, "previous_numerator", "previous_denominator", "code", "scale")
    return _public_formula(f"exists {U} {V} {h} {e}. " + _and(
        f"~({v} = 0)", _trace(s, h, e, f"S ({index})", u, U, v, V, tag + "computation"),
    ), variables)


def _best(a: str, b: str, u: str, v: str, tag: str, *, signed: bool) -> str:
    rp, rn, t, C, D = _names(tag, _context(a, b, u, v), "numerator", "negative_numerator", "denominator", "current_error", "candidate_error")
    binders = f"{rp} {rn} {t} {C} {D}" if signed else f"{rp} {t} {C} {D}"
    error_left = f"({a}) * {t} + ({b}) * {rn}" if signed else f"({a}) * {t}"
    return (f"forall {binders}. ~({t} = 0) -> ({_lt(t, v, tag + 'denominator')}) -> ("
            + _absolute(f"({a}) * ({v})", f"({b}) * ({u})", C) + ") -> ("
            + _absolute(error_left, f"({b}) * {rp}", D) + ") -> (" + _le(C, D, tag + "result") + ")")


def best_approximation_second_kind_relation(
    a: str, b: str, u: str, v: str, *, tag: str, variables: tuple[str, ...], signed: bool = False,
) -> str:
    """Actual cross-product error comparison with every smaller positive denominator."""
    if type(signed) is not bool:
        raise ValueError("signed candidate domain must be an exact Boolean")
    return _public_formula(_best(*_terms((a, b, u, v), variables), tag, signed=signed), variables)


def _old_at(h: str, e: str, j: str, a: str, b: str, s: str, tag: str) -> str:
    return _state_at_term(h, e, j, a, b, s, tag=tag, avoid=_context(h, e, j, a, b, s))


def _old_trace(a: str, b: str, s: str, h: str, e: str, k: str, tag: str) -> str:
    return _trace_term(a, b, s, h, e, k, tag=tag, arguments=_context(a, b, s, h, e, k))


def _old_step(h: str, e: str, j: str, tag: str) -> str:
    a, b, s, A, B, T, q = _names(tag, _context(h, e, j), "old_a", "old_b", "tail", "new_a", "new_b", "head", "q")
    return f"exists {a} {b} {s} {A} {B} {T} {q}. " + _and(
        _old_at(h, e, j, a, b, s, tag + "previous"),
        _old_at(h, e, f"S ({j})", A, B, T, tag + "following"),
        f"{B} = {a}", f"{A} = {B} * {q} + {b}",
        _lt(b, B, tag + "remainder"), cell(T, q, s),
    )


def _old_head(a: str, b: str, s: str, h: str, e: str, length: str, tag: str) -> str:
    q, r, t, k = _names(tag, _context(a, b, s, h, e, length), "q", "r", "tail", "length")
    return f"exists {q} {r} {t} {k}. " + _and(
        f"({length}) = S {k}", f"({a}) = ({b}) * {q} + {r}", _lt(r, b, tag + "bound"),
        cell(s, q, t), _old_trace(b, r, t, h, e, k, tag + "history"),
    )


def _step(h: str, e: str, j: str, tag: str) -> str:
    old, a, b, c, d, new, q = _names(tag, _context(h, e, j), "old", "a", "b", "c", "d", "new", "q")
    return f"exists {old} {a} {b} {c} {d} {new} {q}. " + _and(
        _at(h, e, j, old, a, b, c, d, tag + "previous"),
        _at(h, e, f"S ({j})", new, f"({q} * {a} + {c})", f"({q} * {b} + {d})", a, b, tag + "following"),
        cell(new, q, old),
    )


def _predecessor(s: str, h: str, e: str, k: str, u: str, U: str, v: str, V: str, tag: str) -> str:
    t, a, b, c, d, q = _names(tag, _context(s, h, e, k, u, U, v, V), "tail", "a", "b", "c", "d", "q")
    return f"exists {t} {a} {b} {c} {d} {q}. " + _and(
        _trace(t, h, e, k, a, b, c, d, tag + "prefix"), cell(s, q, t),
        f"({u}) = {q} * {a} + {c}", f"({U}) = {q} * {b} + {d}", f"({v}) = {a}", f"({V}) = {b}",
    )


def _aligned(a: str, b: str, s: str, h: str, e: str, length: str, H: str, E: str,
             k: str, u: str, U: str, v: str, V: str, tag: str) -> str:
    context = _context(a, b, s, h, e, length, H, E, k, u, U, v, V)
    r, t, l, q, p, P, n, N = _names(tag, context, "r", "tail", "length", "q", "p", "P", "n", "N")
    return f"exists {r} {t} {l} {q} {p} {P} {n} {N}. " + _and(
        f"({length}) = S {l}", f"({a}) = ({b}) * {q} + {r}", _lt(r, b, tag + "bound"),
        _old_trace(b, r, t, h, e, l, tag + "euclidean"),
        _trace(t, H, E, k, p, P, n, N, tag + "matrix"),
        f"({u}) = {q} * {p} + {n}", f"({U}) = {q} * {P} + {N}", f"({v}) = {p}", f"({V}) = {P}",
    )


def _beta(h: str, e: str, j: str, z: str, tag: str) -> str:
    return _beta_at_term(h, e, j, z, tag=tag, avoid=_context(h, e, j, z))


def _preserves(h: str, e: str, H: str, E: str, length: str, tag: str) -> str:
    j, z = _names(tag, _context(h, e, H, E, length), "index", "value")
    return f"forall {j} {z}. ({_lt(j, length, tag + 'bound')}) -> ({_beta(h, e, j, z, tag + 'source')}) -> ({_beta(H, E, j, z, tag + 'target')})"


def _matrix_exists(s: str, k: str, tag: str) -> str:
    h, e, u, U, v, V = _names(tag, _context(s, k), "h", "e", "u", "U", "v", "V")
    return f"exists {h} {e} {u} {U} {v} {V}. " + _trace(s, h, e, k, u, U, v, V, tag + "body")


def _previous_column(s: str, k: str, U: str, V: str, tag: str) -> str:
    H, E, p, q = _names(tag, _context(s, k, U, V), "h", "e", "p", "q")
    return f"exists {H} {E} {p} {q}. " + _trace(s, H, E, k, U, p, V, q, tag + "body")


def _cases_exists(name: str, number: int) -> tuple[tuple[str, ...], str]:
    script = ()
    for _ in range(number):
        script += ("cases " + name,)
        name += "_witness"
    return script, name


def _cases_and(name: str, number: int) -> tuple[tuple[str, ...], tuple[str, ...]]:
    script, names = (), ()
    for _ in range(number - 1):
        script += ("cases " + name,)
        names += (name + "_left",)
        name += "_right"
    return script, names + (name,)


def make_continued_fraction_convergents_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_old_history_rows(spec) + _state_rows(spec) + _trace_elimination_rows(spec)
            + _trace_construction_rows(spec) + _alignment_rows(spec) + _invariant_rows(spec)
            + _prefix_completeness_rows(spec) + _boundary_rows(spec) + _functionality_rows(spec)
            + _adjacent_columns_rows(spec) + _best_endpoint_rows(spec))


def _old_history_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    p1, p2 = _packed_state("a", "b", "s"), _packed_state("A", "B", "T")
    q1, q2 = _pair_term("b", "s"), _pair_term("B", "T")
    rows = [
        spec(
            "cf_convergent_old_history_state_unique",
            "forall h e j a b s A B T. (" + _old_at("h", "e", "j", "a", "b", "s", "old_unique_left")
            + ") -> (" + _old_at("h", "e", "j", "A", "B", "T", "old_unique_right")
            + ") -> " + _and("a = A", "b = B", "s = T"),
            ("beta_at_unique", "pair_code_injective"),
            _intro("h", "e", "j", "a", "b", "s", "A", "B", "T", "h1", "h2")
            + (f"have hz : {p1} = {p2}",) + _call("beta_at_unique", "h", "e", "j", p1, p2)
            + ("exact h1", "exact h2", f"have hp : a = A /\\ ({q1}) = ({q2})")
            + _call("pair_code_injective", p1, "a", q1, "A", q2)
            + ("refl", "exact hz", "cases hp", "split", "exact hp_left")
            + _call("pair_code_injective", q1, "b", "s", "B", "T") + ("refl", "exact hp_right"),
            "The existing G071 beta history has unique actual dividend, divisor, and forward quotient-list coordinates at each index.",
        ),
        spec(
            "cf_convergent_old_history_zero_elimination",
            "forall a b s h e. (" + _old_trace("a", "b", "s", "h", "e", "0", "old_zero") + ") -> b = 0 /\\ s = 0",
            ("cf_convergent_old_history_state_unique",),
            _intro("a", "b", "s", "h", "e", "ht")
            + ("cases ht", "cases ht_witness", "cases ht_witness_right", "have heq : " + _and("a = x", "b = 0", "s = 0"))
            + _call("cf_convergent_old_history_state_unique", "h", "e", "0", "a", "b", "s", "x", "0", "0")
            + ("exact ht_witness_right_left", "exact ht_witness_left", "cases heq", "exact heq_right"),
            "An empty actual Euclidean history has divisor zero and the empty quotient list, not a spurious convergent.",
        ),
    ]
    split_step, step_name = _cases_exists("hs", 7)
    split_fields, fields = _cases_and(step_name, 6)
    previous, following, divisor_eq, division_eq, remainder_bound, list_cell = fields
    result = "exists q r t. " + _and(
        "a = b * q + r", _lt("r", "b", "old_predecessor_bound"), cell("s", "q", "t"),
        _old_trace("b", "r", "t", "h", "e", "k", "old_predecessor_history"),
    )
    script = _intro("a", "b", "s", "h", "e", "k", "ht")
    script += ("cases ht", "cases ht_witness", "cases ht_witness_right", "have hs : " + _old_step("h", "e", "k", "old_last_step"))
    script += _call("ht_witness_right_right", "k") + ("exists 0", "apply zero_add")
    script += split_step + split_fields
    script += ("have heq : " + _and("a = x4", "b = x5", "s = x6"),)
    script += _call("cf_convergent_old_history_state_unique", "h", "e", "S k", "a", "b", "s", "x4", "x5", "x6")
    script += ("exact ht_witness_right_left", "exact " + following, "cases heq", "cases heq_right",
               "have hdivisor : b = x1", "trans x5", "exact heq_right_left", "exact " + divisor_eq,
               "have hprefix : " + _old_trace("x1", "x2", "x3", "h", "e", "k", "old_actual_prefix"),
               "exists x", "split", "exact ht_witness_left", "split", "exact " + previous,
               "intro j", "intro hj")
    script += _call("ht_witness_right_right", "j")
    script += _call("lt_of_lt_of_le", "j", "k", "S k") + ("exact hj",)
    script += _call("le_succ_self", "k")
    script += ("exists x7", "exists x2", "exists x3", "split", "rewrite heq_left", "rewrite heq_right_left", "exact " + division_eq,
               "split", "rewrite heq_right_left", "exact " + remainder_bound, "split", "rewrite heq_right_right", "exact " + list_cell)
    script += ("rewrite hdivisor",) * 4 + ("exact hprefix",)
    rows.append(spec(
        "cf_convergent_old_history_successor_elimination",
        "forall a b s h e k. (" + _old_trace("a", "b", "s", "h", "e", "S k", "old_successor") + ") -> " + result,
        ("cf_convergent_old_history_state_unique", "zero_add", "lt_of_lt_of_le", "le_succ_self"),
        script,
        "A complete G071 history exposes its actual first quotient, strict remainder, tagged tail, and predecessor Euclidean history.",
    ))
    rows.append(spec(
        "cf_convergent_no_index_below_zero",
        "forall j. (" + _lt("j", "0", "no_index_zero") + ") -> false",
        ("add_eq_zero_right", "succ_ne_zero"),
        _intro("j", "h") + ("cases h",) + _call("succ_ne_zero", "j")
        + _call("add_eq_zero_right", "x", "S j") + ("exact h_witness",),
        "No natural index or remainder is strictly below zero.",
    ))
    rows.append(spec(
        "cf_convergent_old_history_length_transport",
        "forall a b s h e k l. k = l -> (" + _old_trace("a", "b", "s", "h", "e", "k", "old_length_source")
        + ") -> (" + _old_trace("a", "b", "s", "h", "e", "l", "old_length_target") + ")",
        (),
        _intro("a", "b", "s", "h", "e", "k", "l", "hl", "ht") + ("rewrite <- hl",) * 3 + ("exact ht",),
        "Equality transport of the actual history length is ordinary substitution, not an index-membership assumption.",
    ))
    old_pred = "exists q r t. " + _and(
        "a = b * q + r", _lt("r", "b", "head_remainder"), cell("s", "q", "t"),
        _old_trace("b", "r", "t", "h", "e", "x", "head_predecessor"),
    )
    cases_pred, pred_name = _cases_exists("hp", 3)
    split_pred, pred_fields = _cases_and(pred_name, 4)
    script = _intro("a", "b", "s", "h", "e", "L", "ht", "hn")
    script += ("have hl : L = 0 \\/ exists k. L = S k",) + _call("zero_or_succ", "L")
    script += ("cases hl", "have hz : " + _old_trace("a", "b", "s", "h", "e", "0", "head_empty"),)
    script += _call("cf_convergent_old_history_length_transport", "a", "b", "s", "h", "e", "L", "0")
    script += ("exact hl_left", "exact ht", "have he : b = 0 /\\ s = 0")
    script += _call("cf_convergent_old_history_zero_elimination", "a", "b", "s", "h", "e")
    script += ("exact hz", "cases he", "exfalso", "apply hn", "exact he_right", "cases hl_right",
               "have hh : " + _old_trace("a", "b", "s", "h", "e", "S x", "head_nonempty"))
    script += _call("cf_convergent_old_history_length_transport", "a", "b", "s", "h", "e", "L", "S x")
    script += ("exact hl_right_witness", "exact ht", "have hp : " + old_pred)
    script += _call("cf_convergent_old_history_successor_elimination", "a", "b", "s", "h", "e", "x") + ("exact hh",)
    script += cases_pred + split_pred + ("exists x1", "exists x2", "exists x3", "exists x", "split", "exact hl_right_witness")
    for field in pred_fields[:-1]:
        script += ("split", "exact " + field)
    script += ("exact " + pred_fields[-1],)
    rows.append(spec(
        "cf_convergent_old_history_nonempty_head",
        "forall a b s h e L. (" + _old_trace("a", "b", "s", "h", "e", "L", "head_source")
        + ") -> ~(s = 0) -> (" + _old_head("a", "b", "s", "h", "e", "L", "head_result") + ")",
        ("zero_or_succ", "cf_convergent_old_history_length_transport", "cf_convergent_old_history_zero_elimination",
         "cf_convergent_old_history_successor_elimination"),
        script,
        "A genuine nonempty quotient list in G071 exposes an actual Euclidean first step and an actual shorter history length.",
    ))
    return tuple(rows)


def _state_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    rows = [
        spec(
            "cf_convergent_state_code_constructor",
            "forall s u U v V l r m z. l = " + _pair_term("u", "U") + " -> r = " + _pair_term("v", "V")
            + " -> m = " + _pair_term("l", "r") + " -> z = " + _pair_term("s", "m")
            + " -> (" + _code("s", "u", "U", "v", "V", "z", "state_constructor") + ")",
            (),
            _intro("s", "u", "U", "v", "V", "l", "r", "m", "z", "hl", "hr", "hm", "hz")
            + ("exists l", "exists r", "exists m", "split", "exact hl", "split", "exact hr", "split", "exact hm", "exact hz"),
            "Conservative existential sharing constructs the exact five-coordinate state without adding a pairing function to HA.",
        ),
        spec(
            "cf_convergent_state_code_exists",
            "forall s u U v V. exists z. (" + _code("s", "u", "U", "v", "V", "z", "state_exists") + ")",
            ("pair_code_constructor", "cf_convergent_state_code_constructor"),
            _intro("s", "u", "U", "v", "V")
            + ("have hl : exists l. l = " + _pair_term("u", "U"),) + _call("pair_code_constructor", "u", "U")
            + ("cases hl", "have hr : exists r. r = " + _pair_term("v", "V")) + _call("pair_code_constructor", "v", "V")
            + ("cases hr", "have hm : exists m. m = " + _pair_term("x", "x1")) + _call("pair_code_constructor", "x", "x1")
            + ("cases hm", "have hz : exists z. z = " + _pair_term("s", "x2")) + _call("pair_code_constructor", "s", "x2")
            + ("cases hz", "exists x3")
            + _call("cf_convergent_state_code_constructor", "s", "u", "U", "v", "V", "x", "x1", "x2", "x3")
            + ("exact hl_witness", "exact hr_witness", "exact hm_witness", "exact hz_witness"),
            "Every actual quotient-list/matrix state has a finite natural code with ordinary pairing witnesses.",
        ),
    ]
    ca, na = _cases_exists("h1", 3)
    cb, nb = _cases_exists("h2", 3)
    sa, fa = _cases_and(na, 4)
    sb, fb = _cases_and(nb, 4)
    script = _intro("s", "u", "U", "v", "V", "t", "a", "b", "c", "d", "z", "h1", "h2")
    script += ca + cb + sa + sb
    script += ("have ho : s = t /\\ x2 = x5",) + _call("pair_code_injective", "z", "s", "x2", "t", "x5")
    script += ("exact " + fa[3], "exact " + fb[3], "cases ho", "have hm : x = x3 /\\ x1 = x4")
    script += _call("pair_code_injective", "x2", "x", "x1", "x3", "x4")
    script += ("exact " + fa[2], "trans x5", "exact ho_right", "exact " + fb[2], "cases hm",
               "have hl : u = a /\\ U = b")
    script += _call("pair_code_injective", "x", "u", "U", "a", "b")
    script += ("exact " + fa[0], "trans x3", "exact hm_left", "exact " + fb[0], "cases hl",
               "have hr : v = c /\\ V = d")
    script += _call("pair_code_injective", "x1", "v", "V", "c", "d")
    script += ("exact " + fa[1], "trans x4", "exact hm_right", "exact " + fb[1],
               "split", "exact ho_left", "split", "exact hl_left", "split", "exact hl_right", "exact hr")
    rows.append(spec(
        "cf_convergent_state_code_injective",
        "forall s u U v V t a b c d z. (" + _code("s", "u", "U", "v", "V", "z", "code_unique_one")
        + ") -> (" + _code("t", "a", "b", "c", "d", "z", "code_unique_two") + ") -> "
        + _and("s = t", "u = a", "U = b", "v = c", "V = d"),
        ("pair_code_injective",), script,
        "The conservatively shared state code determines every actual quotient-list and matrix coordinate uniquely.",
    ))
    rows.append(spec(
        "cf_convergent_matrix_state_unique",
        "forall h e j s u U v V t a b c d. (" + _at("h", "e", "j", "s", "u", "U", "v", "V", "at_unique_one")
        + ") -> (" + _at("h", "e", "j", "t", "a", "b", "c", "d", "at_unique_two")
        + ") -> " + _and("s = t", "u = a", "U = b", "v = c", "V = d"),
        ("beta_at_unique", "cf_convergent_state_code_injective"),
        _intro("h", "e", "j", "s", "u", "U", "v", "V", "t", "a", "b", "c", "d", "h1", "h2")
        + ("cases h1", "cases h2", "cases h1_witness", "cases h2_witness", "have hz : x = x1")
        + _call("beta_at_unique", "h", "e", "j", "x", "x1")
        + ("exact h1_witness_right", "exact h2_witness_right")
        + _call("cf_convergent_state_code_injective", "s", "u", "U", "v", "V", "t", "a", "b", "c", "d", "x")
        + ("exact h1_witness_left", "rewrite hz", "exact h2_witness_left"),
        "Every beta index of the genuine convergent computation has unique decoded quotient-list and matrix entries.",
    ))
    return tuple(rows)


def _trace_elimination_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    rows = [spec(
        "cf_convergent_matrix_empty_elimination",
        "forall s h e u U v V. (" + _trace("s", "h", "e", "0", "u", "U", "v", "V", "matrix_empty")
        + ") -> " + _and("u = 1", "U = 0", "v = 0", "V = 1"),
        ("cf_convergent_matrix_state_unique",),
        _intro("s", "h", "e", "u", "U", "v", "V", "ht")
        + ("cases ht", "cases ht_witness", "cases ht_witness_right",
           "have heq : " + _and("s = x", "u = 1", "U = 0", "v = 0", "V = 1"))
        + _call("cf_convergent_matrix_state_unique", "h", "e", "0", "s", "u", "U", "v", "V", "x", "1", "0", "0", "1")
        + ("exact ht_witness_right_left", "exact ht_witness_left", "cases heq", "exact heq_right"),
        "The zero-step actual prefix product is exactly the identity matrix, regardless of its unconsumed quotient tail.",
    )]
    ce, en = _cases_exists("hs", 7)
    cs, fs = _cases_and(en, 3)
    cq, fq = _cases_and("heq", 5)
    script = _intro("s", "h", "e", "k", "u", "U", "v", "V", "ht")
    script += ("cases ht", "cases ht_witness", "cases ht_witness_right", "have hs : " + _step("h", "e", "k", "matrix_last_step"))
    script += _call("ht_witness_right_right", "k") + ("exists 0", "apply zero_add") + ce + cs
    script += ("have heq : " + _and("s = x6", "u = x7 * x2 + x4", "U = x7 * x3 + x5", "v = x2", "V = x3"),)
    script += _call("cf_convergent_matrix_state_unique", "h", "e", "S k", "s", "u", "U", "v", "V",
                    "x6", "x7 * x2 + x4", "x7 * x3 + x5", "x2", "x3")
    script += ("exact ht_witness_right_left", "exact " + fs[1]) + cq
    script += ("exists x1", "exists x2", "exists x3", "exists x4", "exists x5", "exists x7", "split",
               "exists x", "split", "exact ht_witness_left", "split", "exact " + fs[0], "intro j", "intro hj")
    script += _call("ht_witness_right_right", "j")
    script += _call("lt_of_lt_of_le", "j", "k", "S k") + ("exact hj",) + _call("le_succ_self", "k")
    script += ("split", "rewrite " + fq[0], "exact " + fs[2])
    for field in fq[1:-1]:
        script += ("split", "exact " + field)
    script += ("exact " + fq[-1],)
    rows.append(spec(
        "cf_convergent_matrix_successor_elimination",
        "forall s h e k u U v V. (" + _trace("s", "h", "e", "S k", "u", "U", "v", "V", "matrix_successor")
        + ") -> (" + _predecessor("s", "h", "e", "k", "u", "U", "v", "V", "matrix_predecessor") + ")",
        ("cf_convergent_matrix_state_unique", "zero_add", "lt_of_lt_of_le", "le_succ_self"),
        script,
        "Every nonempty actual prefix computation exposes a tagged first quotient and the exact four matrix recurrence equations.",
    ))
    ce, en = _cases_exists("hp", 6)
    cs, fs = _cases_and(en, 6)
    rows.append(spec(
        "cf_convergent_matrix_nonempty_list",
        "forall s h e k u U v V. (" + _trace("s", "h", "e", "S k", "u", "U", "v", "V", "matrix_nonempty")
        + ") -> ~(s = 0)",
        ("cf_convergent_matrix_successor_elimination", "cell_nonzero"),
        _intro("s", "h", "e", "k", "u", "U", "v", "V", "ht", "hz")
        + ("have hp : " + _predecessor("s", "h", "e", "k", "u", "U", "v", "V", "matrix_nonempty_pred"),)
        + _call("cf_convergent_matrix_successor_elimination", "s", "h", "e", "k", "u", "U", "v", "V")
        + ("exact ht",) + ce + cs
        + _call("cell_nonzero", "s", "x5", "x") + ("exact " + fs[1], "exact hz"),
        "A nonempty convergent prefix must consume an actual tagged quotient cell; nil cannot be mistaken for an initial convergent.",
    ))
    rows.append(spec(
        "cf_convergent_matrix_list_transport",
        "forall s t h e k u U v V. s = t -> (" + _trace("s", "h", "e", "k", "u", "U", "v", "V", "list_source")
        + ") -> (" + _trace("t", "h", "e", "k", "u", "U", "v", "V", "list_target") + ")",
        (),
        _intro("s", "t", "h", "e", "k", "u", "U", "v", "V", "heq", "ht")
        + ("rewrite <- heq",) * 2 + ("exact ht",),
        "Equality of actual tagged quotient lists transports the finite computation by ordinary substitution.",
    ))
    rows.append(spec(
        "cf_convergent_matrix_length_transport",
        "forall s h e k l u U v V. k = l -> (" + _trace("s", "h", "e", "k", "u", "U", "v", "V", "matrix_length_source")
        + ") -> (" + _trace("s", "h", "e", "l", "u", "U", "v", "V", "matrix_length_target") + ")",
        (),
        _intro("s", "h", "e", "k", "l", "u", "U", "v", "V", "heq", "ht")
        + ("rewrite <- heq",) * 3 + ("exact ht",),
        "Equality transports the length of the actual finite matrix computation without altering its entries or quotient list.",
    ))
    script = _intro("s", "h", "e", "k", "u", "U", "v", "V", "p", "P", "n", "N", "hu", "hU", "hv", "hV", "ht")
    for hyp, count in (("hu", 2), ("hU", 4), ("hv", 2), ("hV", 4)):
        script += ("rewrite " + hyp,) * count
    script += ("exact ht",)
    rows.append(spec(
        "cf_convergent_matrix_entry_transport",
        "forall s h e k u U v V p P n N. u = p -> U = P -> v = n -> V = N -> ("
        + _trace("s", "h", "e", "k", "p", "P", "n", "N", "entries_source") + ") -> ("
        + _trace("s", "h", "e", "k", "u", "U", "v", "V", "entries_target") + ")",
        (), script,
        "Ordinary simultaneous equality transport preserves the actual four terminal matrix entries of the finite computation.",
    ))
    return tuple(rows)


def _trace_construction_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    rows = [
        spec(
            "cf_convergent_matrix_state_prefix_transport",
            "forall h e H E k j s u U v V. (" + _preserves("h", "e", "H", "E", "k", "state_transport")
            + ") -> (" + _lt("j", "k", "state_transport_index") + ") -> ("
            + _at("h", "e", "j", "s", "u", "U", "v", "V", "state_transport_source") + ") -> ("
            + _at("H", "E", "j", "s", "u", "U", "v", "V", "state_transport_target") + ")",
            (),
            _intro("h", "e", "H", "E", "k", "j", "s", "u", "U", "v", "V", "hp", "hj", "ha")
            + ("cases ha", "cases ha_witness", "exists x", "split", "exact ha_witness_left")
            + _call("hp", "j", "x") + ("exact hj", "exact ha_witness_right"),
            "Ordinary beta-prefix extension preserves every actually decoded matrix coordinate at all retained indices.",
        ),
        spec(
            "cf_convergent_matrix_empty_constructor",
            "forall s h e. (" + _at("h", "e", "0", "s", "1", "0", "0", "1", "empty_constructor_state")
            + ") -> (" + _trace("s", "h", "e", "0", "1", "0", "0", "1", "empty_constructor_trace") + ")",
            ("cf_convergent_no_index_below_zero",),
            _intro("s", "h", "e", "ha") + ("exists s", "split", "exact ha", "split", "exact ha", "intro j", "intro hj", "exfalso")
            + _call("cf_convergent_no_index_below_zero", "j") + ("exact hj",),
            "An actual encoded identity state constructs the zero-length quotient-prefix product with no transition obligations.",
        ),
        spec(
            "cf_convergent_matrix_empty_exists",
            "forall s. exists h e. (" + _trace("s", "h", "e", "0", "1", "0", "0", "1", "empty_exists_trace") + ")",
            ("cf_convergent_state_code_exists", "beta_prefix_extend", "cf_convergent_matrix_empty_constructor"),
            _intro("s") + ("have hz : exists z. " + _code("s", "1", "0", "0", "1", "z", "empty_exists_code"),)
            + _call("cf_convergent_state_code_exists", "s", "1", "0", "0", "1")
            + ("cases hz", "have hb : exists h e. " + _and(_beta("h", "e", "0", "x", "empty_exists_beta"),
                _preserves("0", "0", "h", "e", "0", "empty_exists_preserves")))
            + _call("beta_prefix_extend", "0", "0", "0", "x")
            + ("cases hb", "cases hb_witness", "cases hb_witness_witness", "exists x1", "exists x2")
            + _call("cf_convergent_matrix_empty_constructor", "s", "x1", "x2")
            + ("exists x", "split", "exact hz_witness", "exact hb_witness_witness_left"),
            "The zero-step matrix prefix has a genuine finite beta certificate for every unconsumed tagged list.",
        ),
    ]
    computed = ("(q * u + v)", "(q * U + V)", "u", "U")
    args = ("t", "h", "e", "k", "u", "U", "v", "V", "q", "s", "H", "E")
    ce, en = _cases_exists("hs", 7)
    cs, fs = _cases_and(en, 3)
    script = _intro(*args, "ht", "hcell", "hnew", "hp")
    script += ("cases ht", "cases ht_witness", "cases ht_witness_right", "exists x", "split")
    script += _call("cf_convergent_matrix_state_prefix_transport", "h", "e", "H", "E", "S k", "0", "x", "1", "0", "0", "1")
    script += ("exact hp", "exists k", "simp", "exact ht_witness_left", "split", "exact hnew", "intro j", "intro hj",
               "have hjk : " + _le("j", "k", "extend_index"))
    script += _call("le_of_succ_le_succ", "j", "k") + ("exact hj", "have heq : j = k \\/ (" + _lt("j", "k", "extend_case") + ")")
    script += _call("le_eq_or_lt", "j", "k") + ("exact hjk", "cases heq")
    script += ("rewrite heq_left",) * 4
    script += ("exists t", "exists u", "exists U", "exists v", "exists V", "exists s", "exists q", "split")
    script += _call("cf_convergent_matrix_state_prefix_transport", "h", "e", "H", "E", "S k", "k", "t", "u", "U", "v", "V")
    script += ("exact hp", "exists 0", "apply zero_add", "exact ht_witness_right_left", "split", "exact hnew", "exact hcell",
               "have hs : " + _step("h", "e", "j", "extend_previous_step"))
    script += _call("ht_witness_right_right", "j") + ("exact heq_right",) + ce + cs
    script += tuple("exists x" + str(i) for i in range(1, 8)) + ("split",)
    script += _call("cf_convergent_matrix_state_prefix_transport", "h", "e", "H", "E", "S k", "j", "x1", "x2", "x3", "x4", "x5")
    script += ("exact hp", "exact hj", "exact " + fs[0], "split")
    script += _call("cf_convergent_matrix_state_prefix_transport", "h", "e", "H", "E", "S k", "S j", "x6", "x7 * x2 + x4", "x7 * x3 + x5", "x2", "x3")
    script += ("exact hp",) + _call("succ_le_succ", "S j", "k")
    script += ("exact heq_right", "exact " + fs[1], "exact " + fs[2])
    rows.append(spec(
        "cf_convergent_matrix_extend_preserved_prefix",
        "forall t h e k u U v V q s H E. (" + _trace("t", "h", "e", "k", "u", "U", "v", "V", "extend_old")
        + ") -> (" + cell("s", "q", "t") + ") -> (" + _at("H", "E", "S k", "s", *computed, "extend_new_state")
        + ") -> (" + _preserves("h", "e", "H", "E", "S k", "extend_preserves") + ") -> ("
        + _trace("s", "H", "E", "S k", *computed, "extend_result") + ")",
        ("cf_convergent_matrix_state_prefix_transport", "le_of_succ_le_succ", "le_eq_or_lt", "zero_add", "succ_le_succ"),
        script,
        "Appending the actual first-quotient matrix step preserves every earlier computed state and every transition under a genuine beta-prefix recoding.",
    ))
    script = _intro("t", "h", "e", "k", "u", "U", "v", "V", "q", "s", "ht", "hcell")
    script += ("have hz : exists z. " + _code("s", *computed, "z", "extend_new_code"),)
    script += _call("cf_convergent_state_code_exists", "s", *computed) + ("cases hz",)
    script += ("have hb : exists H E. " + _and(_beta("H", "E", "S k", "x", "extend_new_beta"),
                _preserves("h", "e", "H", "E", "S k", "extend_new_preserves")),)
    script += _call("beta_prefix_extend", "S k", "h", "e", "x")
    script += ("cases hb", "cases hb_witness", "cases hb_witness_witness", "exists x1", "exists x2")
    script += _call("cf_convergent_matrix_extend_preserved_prefix", "t", "h", "e", "k", "u", "U", "v", "V", "q", "s", "x1", "x2")
    script += ("exact ht", "exact hcell", "exists x", "split", "exact hz_witness", "exact hb_witness_witness_left", "exact hb_witness_witness_right")
    rows.append(spec(
        "cf_convergent_matrix_prepend_exists",
        "forall t h e k u U v V q s. (" + _trace("t", "h", "e", "k", "u", "U", "v", "V", "prepend_exists_source")
        + ") -> (" + cell("s", "q", "t") + ") -> exists H E. (" + _trace("s", "H", "E", "S k", *computed, "prepend_exists_target") + ")",
        ("cf_convergent_state_code_exists", "beta_prefix_extend", "cf_convergent_matrix_extend_preserved_prefix"),
        script,
        "A genuine tagged quotient prepends its exact matrix to any actually computed prefix and constructs a finite certificate of the longer computation.",
    ))
    return tuple(rows)


def _alignment_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    ch, nh = _cases_exists("hh", 4)
    sh, fh = _cases_and(nh, 5)
    cm, nm = _cases_exists("hm", 6)
    sm, fm = _cases_and(nm, 6)
    arguments = ("a", "b", "s", "h", "e", "L", "H", "E", "k", "u", "U", "v", "V")
    script = _intro(*arguments, "hold", "hnew")
    script += ("have hn : ~(s = 0)", "intro hz")
    script += _call("cf_convergent_matrix_nonempty_list", "s", "H", "E", "k", "u", "U", "v", "V")
    script += ("exact hnew", "exact hz", "have hh : " + _old_head("a", "b", "s", "h", "e", "L", "alignment_head"))
    script += _call("cf_convergent_old_history_nonempty_head", "a", "b", "s", "h", "e", "L")
    script += ("exact hold", "exact hn") + ch + sh
    script += ("have hm : " + _predecessor("s", "H", "E", "k", "u", "U", "v", "V", "alignment_matrix"),)
    script += _call("cf_convergent_matrix_successor_elimination", "s", "H", "E", "k", "u", "U", "v", "V")
    script += ("exact hnew",) + cm + sm
    script += ("have heq : x = x9 /\\ x2 = x4",) + _call("cell_functional", "s", "x", "x2", "x9", "x4")
    script += ("exact " + fh[3], "exact " + fm[1], "cases heq",
               "exists x1", "exists x2", "exists x3", "exists x9", "exists x5", "exists x6", "exists x7", "exists x8",
               "split", "exact " + fh[0], "split", "rewrite <- heq_left", "exact " + fh[1],
               "split", "exact " + fh[2], "split", "exact " + fh[4], "split")
    script += _call("cf_convergent_matrix_list_transport", "x4", "x2", "H", "E", "k", "x5", "x6", "x7", "x8")
    script += ("symm", "exact heq_right", "exact " + fm[0])
    for field in fm[2:-1]:
        script += ("split", "exact " + field)
    script += ("exact " + fm[-1],)
    return (spec(
        "cf_convergent_euclidean_matrix_step_alignment",
        "forall a b s h e L H E k u U v V. (" + _old_trace("a", "b", "s", "h", "e", "L", "alignment_old")
        + ") -> (" + _trace("s", "H", "E", "S k", "u", "U", "v", "V", "alignment_new")
        + ") -> (" + _aligned(*arguments, "alignment_result") + ")",
        ("cf_convergent_matrix_nonempty_list", "cf_convergent_old_history_nonempty_head",
         "cf_convergent_matrix_successor_elimination", "cell_functional", "cf_convergent_matrix_list_transport"),
        script,
        "The actual G071 history and actual matrix prefix consume the same first quotient and tagged tail; both predecessor computations and all recurrence equations are derived, not assumed.",
    ),)


def _invariant_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    arguments = ("a", "b", "s", "h", "e", "L", "H", "E", "u", "U", "v", "V")
    ca, na = _cases_exists("ha", 8)
    sa, fa = _cases_and(na, 9)
    script = ("induction k",)
    for step in (False, True):
        k = "S k" if step else "0"
        script += _intro(*arguments, "hold", "hnew")
        script += ("have ha : " + _aligned("a", "b", "s", "h", "e", "L", "H", "E", k, "u", "U", "v", "V", "invariant_aligned"),)
        script += _call("cf_convergent_euclidean_matrix_step_alignment", "a", "b", "s", "h", "e", "L", "H", "E", k, "u", "U", "v", "V")
        script += ("exact hold", "exact hnew") + ca + sa
        if not step:
            script += ("have hz : " + _and("x4 = 1", "x5 = 0", "x6 = 0", "x7 = 1"),)
            script += _call("cf_convergent_matrix_empty_elimination", "x1", "H", "E", "x4", "x5", "x6", "x7")
            script += ("exact " + fa[4],)
            cz, fz = _cases_and("hz", 4)
            script += cz
            script += _call("cf_approximation_first_recurrence_error_invariant", "a", "b", "x3", "x", "u", "U", "v", "V", "x4", "x5", "x6", "x7")
            script += ("exact " + fa[1], "exact " + fa[2])
            script += tuple("exact " + field for field in fz + fa[5:])
        else:
            script += _call("cf_approximation_prepend_recurrence_error_invariant", "a", "b", "x3", "x", "u", "U", "v", "V", "x4", "x5", "x6", "x7")
            script += tuple("exact " + field for field in (fa[1], fa[2]) + fa[5:])
            script += _call("IH", "b", "x", "x1", "h", "e", "x2", "H", "E", "x4", "x5", "x6", "x7")
            script += ("exact " + fa[3], "exact " + fa[4])
    return (spec(
        "cf_convergent_actual_prefix_error_invariant",
        "forall k a b s h e L H E u U v V. (" + _old_trace("a", "b", "s", "h", "e", "L", "invariant_euclidean")
        + ") -> (" + _trace("s", "H", "E", "S k", "u", "U", "v", "V", "invariant_computation")
        + ") -> (" + _invariant("a", "b", "u", "U", "v", "V", "invariant_output") + ")",
        ("cf_convergent_euclidean_matrix_step_alignment", "cf_convergent_matrix_empty_elimination",
         "cf_approximation_first_recurrence_error_invariant", "cf_approximation_prepend_recurrence_error_invariant"),
        script,
        "Ordinary HA induction on the actual nonempty quotient-prefix length derives determinant one, both alternating errors, strict decrease, and the denominator bound directly from G071 histories.",
    ),)


def _prefix_completeness_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    script = ("induction L",) + _intro("k", "a", "b", "s", "h", "e", "ht", "hk")
    script += ("have hkzero : k = 0",) + _call("le_zero", "k") + ("exact hk",)

    def zero_prefix(equation: str) -> tuple[str, ...]:
        result = ("have hz : exists H E. " + _trace("s", "H", "E", "0", "1", "0", "0", "1", "complete_empty"),)
        result += _call("cf_convergent_matrix_empty_exists", "s")
        result += ("cases hz", "cases hz_witness", "exists x", "exists x1", "exists 1", "exists 0", "exists 0", "exists 1")
        result += _call("cf_convergent_matrix_length_transport", "s", "x", "x1", "0", "k", "1", "0", "0", "1")
        return result + ("symm", "exact " + equation, "exact hz_witness_witness")

    script += zero_prefix("hkzero")
    script += _intro("k", "a", "b", "s", "h", "e", "ht", "hk")
    script += ("have hkcase : k = 0 \\/ exists i. k = S i",) + _call("zero_or_succ", "k")
    script += ("cases hkcase",) + zero_prefix("hkcase_left") + ("cases hkcase_right",)
    predecessor = "exists q r t. " + _and("a = b * q + r", _lt("r", "b", "complete_remainder"), cell("s", "q", "t"),
                                                _old_trace("b", "r", "t", "h", "e", "L", "complete_predecessor"))
    script += ("have hp : " + predecessor,)
    script += _call("cf_convergent_old_history_successor_elimination", "a", "b", "s", "h", "e", "L") + ("exact ht",)
    cp, np = _cases_exists("hp", 3)
    sp, fp = _cases_and(np, 4)
    script += cp + sp + ("have hc : " + _matrix_exists("x3", "x", "complete_child"),)
    script += _call("IH", "x", "b", "x2", "x3", "h", "e") + ("exact " + fp[3],)
    script += _call("le_of_succ_le_succ", "x", "L") + ("rewrite <- hkcase_right_witness", "exact hk")
    cc, nc = _cases_exists("hc", 6)
    script += cc
    extension = "exists H E. " + _trace("s", "H", "E", "S x", "(x1 * x6 + x8)", "(x1 * x7 + x9)", "x6", "x7", "complete_extension")
    script += ("have hext : " + extension,)
    script += _call("cf_convergent_matrix_prepend_exists", "x3", "x4", "x5", "x", "x6", "x7", "x8", "x9", "x1", "s")
    script += ("exact " + nc, "exact " + fp[2], "cases hext", "cases hext_witness", "exists x10", "exists x11",
               "exists x1 * x6 + x8", "exists x1 * x7 + x9", "exists x6", "exists x7")
    script += _call("cf_convergent_matrix_length_transport", "s", "x10", "x11", "S x", "k", "x1 * x6 + x8", "x1 * x7 + x9", "x6", "x7")
    script += ("symm", "exact hkcase_right_witness", "exact hext_witness_witness")
    rows = [spec(
        "cf_convergent_every_valid_matrix_prefix_exists",
        "forall L k a b s h e. (" + _old_trace("a", "b", "s", "h", "e", "L", "complete_source")
        + ") -> (" + _le("k", "L", "complete_index") + ") -> (" + _matrix_exists("s", "k", "complete_result") + ")",
        ("le_zero", "zero_or_succ", "cf_convergent_matrix_empty_exists", "cf_convergent_matrix_length_transport",
         "cf_convergent_old_history_successor_elimination", "le_of_succ_le_succ", "cf_convergent_matrix_prepend_exists"),
        script,
        "HA induction on the actual complete Euclidean history constructs every valid quotient-matrix prefix, including the empty, initial, and full terminal products.",
    )]
    args = ("a", "b", "s", "h", "e", "L", "H", "E", "u", "U", "v", "V")
    script = ("induction k",) + _intro(*args, "hold", "hnew") + ("exists L", "simp")
    script += _intro(*args, "hold", "hnew")
    script += ("have ha : " + _aligned("a", "b", "s", "h", "e", "L", "H", "E", "k", "u", "U", "v", "V", "bound_aligned"),)
    script += _call("cf_convergent_euclidean_matrix_step_alignment", "a", "b", "s", "h", "e", "L", "H", "E", "k", "u", "U", "v", "V")
    script += ("exact hold", "exact hnew")
    ca, na = _cases_exists("ha", 8)
    sa, fa = _cases_and(na, 9)
    script += ca + sa + ("rewrite " + fa[0],) + _call("succ_le_succ", "k", "x2")
    script += _call("IH", "b", "x", "x1", "h", "e", "x2", "H", "E", "x4", "x5", "x6", "x7")
    script += ("exact " + fa[3], "exact " + fa[4])
    rows.append(spec(
        "cf_convergent_actual_prefix_index_bound",
        "forall k a b s h e L H E u U v V. (" + _old_trace("a", "b", "s", "h", "e", "L", "bound_source")
        + ") -> (" + _trace("s", "H", "E", "k", "u", "U", "v", "V", "bound_matrix")
        + ") -> (" + _le("k", "L", "bound_result") + ")",
        ("cf_convergent_euclidean_matrix_step_alignment", "succ_le_succ"),
        script,
        "Every actual matrix prefix consumes at most the available number of G071 quotients; out-of-range indices cannot satisfy Convergent.",
    ))
    conv = convergent_relation("s", "i", "u", "v", tag="existing_convergent", variables=("s", "i", "u", "v"))
    cp, np = _cases_exists("hp", 6)
    script = _intro("i", "a", "b", "s", "h", "e", "L", "ht", "hi")
    script += ("have hp : " + _matrix_exists("s", "S i", "convergent_exists_matrix"),)
    script += _call("cf_convergent_every_valid_matrix_prefix_exists", "L", "S i", "a", "b", "s", "h", "e")
    script += ("exact ht", "exact hi") + cp
    script += ("exists x2", "exists x4", "exists x3", "exists x5", "exists x", "exists x1", "split", "intro hz")
    script += _call("cf_approximation_derived_invariant_denominator_positive", "a", "b", "x2", "x3", "x4", "x5")
    script += _call("cf_convergent_actual_prefix_error_invariant", "i", "a", "b", "s", "h", "e", "L", "x", "x1", "x2", "x3", "x4", "x5")
    script += ("exact ht", "exact " + np, "exact hz", "exact " + np)
    rows.append(spec(
        "continued_fraction_convergent_exists_at_history_index",
        "forall i a b s h e L. (" + _old_trace("a", "b", "s", "h", "e", "L", "convergent_exists_history")
        + ") -> (" + _lt("i", "L", "convergent_exists_index") + ") -> exists u v. (" + conv + ")",
        ("cf_convergent_every_valid_matrix_prefix_exists", "cf_approximation_derived_invariant_denominator_positive",
         "cf_convergent_actual_prefix_error_invariant"),
        script,
        "Every genuine in-range index of a G071 history constructs a convergent with proved positive denominator; zero numerators remain allowed.",
    ))
    cc, nc = _cases_exists("hc", 4)
    sc, fc = _cases_and(nc, 2)
    rows.append(spec(
        "continued_fraction_convergent_index_is_valid",
        "forall a b s h e L i u v. (" + _old_trace("a", "b", "s", "h", "e", "L", "convergent_index_history")
        + ") -> (" + conv + ") -> (" + _lt("i", "L", "convergent_index_valid") + ")",
        ("cf_convergent_actual_prefix_index_bound",),
        _intro("a", "b", "s", "h", "e", "L", "i", "u", "v", "ht", "hc") + cc + sc
        + _call("cf_convergent_actual_prefix_index_bound", "S i", "a", "b", "s", "h", "e", "L", "x2", "x3", "u", "x", "v", "x1")
        + ("exact ht", "exact " + fc[1]),
        "The actual prefix computation proves the advertised index belongs to the complete G071 list; it is not merely a tagged pair of positive integers.",
    ))
    return tuple(rows)


def _boundary_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    first_computed = ("(q * 1 + 0)", "(q * 0 + 1)", "1", "0")
    initial = convergent_relation("s", "0", "q", "1", tag="initial_convergent", variables=("s", "q"))
    rows = [
        spec(
            "cf_convergent_initial_matrix_exists",
            "forall s q t. (" + cell("s", "q", "t") + ") -> exists h e. ("
            + _trace("s", "h", "e", "1", "q", "1", "1", "0", "initial_matrix") + ")",
            ("cf_convergent_matrix_empty_exists", "cf_convergent_matrix_prepend_exists", "cf_convergent_matrix_entry_transport", "zero_add"),
            _intro("s", "q", "t", "hc")
            + ("have hz : exists h e. " + _trace("t", "h", "e", "0", "1", "0", "0", "1", "initial_empty"),)
            + _call("cf_convergent_matrix_empty_exists", "t")
            + ("cases hz", "cases hz_witness", "have hn : exists h e. " + _trace("s", "h", "e", "1", *first_computed, "initial_prepend"))
            + _call("cf_convergent_matrix_prepend_exists", "t", "x", "x1", "0", "1", "0", "0", "1", "q", "s")
            + ("exact hz_witness_witness", "exact hc", "cases hn", "cases hn_witness", "exists x2", "exists x3")
            + _call("cf_convergent_matrix_entry_transport", "s", "x2", "x3", "1", "q", "1", "1", "0", *first_computed)
            + _simp("zero_add") + ("simp", "refl", "refl", "exact hn_witness_witness"),
            "Every actual first quotient cell constructs the exact initial matrix [[q,1],[1,0]], including q=0.",
        ),
        spec(
            "continued_fraction_first_cell_is_initial_convergent",
            "forall s q t. (" + cell("s", "q", "t") + ") -> (" + initial + ")",
            ("cf_convergent_initial_matrix_exists", "succ_ne_zero"),
            _intro("s", "q", "t", "hc")
            + ("have hm : exists h e. " + _trace("s", "h", "e", "1", "q", "1", "1", "0", "initial_actual"),)
            + _call("cf_convergent_initial_matrix_exists", "s", "q", "t")
            + ("exact hc", "cases hm", "cases hm_witness", "exists 1", "exists 0", "exists x", "exists x1", "split", "intro hz")
            + _call("succ_ne_zero", "0") + ("exact hz", "exact hm_witness_witness"),
            "The genuine zeroth convergent is q/1 for the actual first quotient q; no positivity condition is imposed on its numerator.",
        ),
        spec(
            "cf_convergent_numerator_transport",
            "forall s i u p v. u = p -> (" + convergent_relation("s", "i", "u", "v", tag="numerator_source", variables=("s", "i", "u", "v"))
            + ") -> (" + convergent_relation("s", "i", "p", "v", tag="numerator_target", variables=("s", "i", "p", "v")) + ")",
            (),
            _intro("s", "i", "u", "p", "v", "heq", "hc") + ("rewrite <- heq",) * 2 + ("exact hc",),
            "Actual numerator equality transports a convergent while preserving its index, positive denominator, and complete computation certificate.",
        ),
    ]
    cf = continued_fraction("a", "b", "s", tag="zero_initial_fraction")
    ccf, ncf = _cases_exists("hcf", 5)
    scf, fcf = _cases_and(ncf, 3)
    predecessor = "exists q r t. " + _and("a = b * q + r", _lt("r", "b", "zero_initial_remainder"), cell("s", "q", "t"),
                                                _old_trace("b", "r", "t", "x2", "x3", "x4", "zero_initial_history"))
    cp, np = _cases_exists("hp", 3)
    sp, fp = _cases_and(np, 4)
    script = _intro("a", "b", "s", "hcf", "hlt") + ccf + scf
    script += ("have hp : " + predecessor,)
    script += _call("cf_convergent_old_history_successor_elimination", "a", "b", "s", "x2", "x3", "x4")
    script += ("exact " + fcf[2],) + cp + sp + ("have hq : x5 = 0 /\\ x6 = a",)
    script += _call("division_remainder_unique", "b", "a", "x5", "x6", "0", "a")
    script += ("exact " + fp[0], "exact " + fp[1]) + _simp("zero_add") + ("exact hlt", "cases hq")
    script += _call("cf_convergent_numerator_transport", "s", "0", "x5", "0", "1") + ("exact hq_left",)
    script += _call("continued_fraction_first_cell_is_initial_convergent", "s", "x5", "x7") + ("exact " + fp[2],)
    rows.append(spec(
        "continued_fraction_initial_zero_over_one",
        "forall a b s. (" + cf + ") -> (" + _lt("a", "b", "zero_initial_input") + ") -> ("
        + convergent_relation("s", "0", "0", "1", tag="zero_initial_actual", variables=("s",)) + ")",
        ("cf_convergent_old_history_successor_elimination", "division_remainder_unique", "zero_add",
         "cf_convergent_numerator_transport", "continued_fraction_first_cell_is_initial_convergent"),
        script,
        "For every positive G071 fraction below one, the genuine initial convergent is 0/1. This checked theorem explicitly corrects the old planning-only numerator-positivity error.",
    ))
    args = ("a", "b", "s", "h", "e", "H", "E", "u", "U", "v", "V")
    script = ("induction k",) + _intro(*args, "hold", "hnew")
    script += ("have ho : b = 0 /\\ s = 0",) + _call("cf_convergent_old_history_zero_elimination", "a", "b", "s", "h", "e")
    script += ("exact hold", "cases ho", "have hm : " + _and("u = 1", "U = 0", "v = 0", "V = 1"))
    script += _call("cf_convergent_matrix_empty_elimination", "s", "H", "E", "u", "U", "v", "V") + ("exact hnew",)
    cm, fm = _cases_and("hm", 4)
    script += cm + ("rewrite ho_left", "rewrite " + fm[0], "rewrite " + fm[2], "simp")
    script += _intro(*args, "hold", "hnew")
    script += ("have ha : " + _aligned("a", "b", "s", "h", "e", "S k", "H", "E", "k", "u", "U", "v", "V", "exact_aligned"),)
    script += _call("cf_convergent_euclidean_matrix_step_alignment", "a", "b", "s", "h", "e", "S k", "H", "E", "k", "u", "U", "v", "V")
    script += ("exact hold", "exact hnew")
    ca, na = _cases_exists("ha", 8)
    sa, fa = _cases_and(na, 9)
    script += ca + sa + ("have hk : k = x2",) + _call("succ_injective", "k", "x2") + ("exact " + fa[0],)
    script += ("have hvalue : b * x6 = x * x4",)
    script += _call("IH", "b", "x", "x1", "h", "e", "H", "E", "x4", "x5", "x6", "x7")
    script += _call("cf_convergent_old_history_length_transport", "b", "x", "x1", "h", "e", "x2", "k")
    script += ("symm", "exact hk", "exact " + fa[3], "exact " + fa[4], "rewrite " + fa[7], "rewrite " + fa[5])
    script += _call("cf_approximation_exact_value_prepend", "a", "b", "x3", "x", "x4", "x6")
    script += ("exact " + fa[1], "exact hvalue")
    rows.append(spec(
        "cf_convergent_full_matrix_is_exact",
        "forall k a b s h e H E u U v V. (" + _old_trace("a", "b", "s", "h", "e", "k", "exact_history")
        + ") -> (" + _trace("s", "H", "E", "k", "u", "U", "v", "V", "exact_computation") + ") -> a * v = b * u",
        ("cf_convergent_old_history_zero_elimination", "cf_convergent_matrix_empty_elimination",
         "cf_convergent_euclidean_matrix_step_alignment", "succ_injective", "cf_convergent_old_history_length_transport",
         "cf_approximation_exact_value_prepend"),
        script,
        "HA induction proves the complete quotient product represents the input rational exactly, including the empty zero-divisor boundary and the terminal zero error.",
    ))
    conv = convergent_relation("s", "k", "u", "v", tag="terminal_convergent", variables=("s", "k", "u", "v"))
    cc, nc = _cases_exists("hc", 4)
    sc, fc = _cases_and(nc, 2)
    rows.append(spec(
        "continued_fraction_terminal_convergent_is_exact",
        "forall a b s h e k u v. (" + _old_trace("a", "b", "s", "h", "e", "S k", "terminal_history")
        + ") -> (" + conv + ") -> a * v = b * u",
        ("cf_convergent_full_matrix_is_exact",),
        _intro("a", "b", "s", "h", "e", "k", "u", "v", "ht", "hc") + cc + sc
        + _call("cf_convergent_full_matrix_is_exact", "S k", "a", "b", "s", "h", "e", "x2", "x3", "u", "x", "v", "x1")
        + ("exact ht", "exact " + fc[1]),
        "Every actual terminal convergent has zero cross-product error; the best-approximation theorem does not exclude this rational endpoint.",
    ))
    rows.append(spec(
        "continued_fraction_exact_terminal_convergent_exists",
        "forall a b s h e k. (" + _old_trace("a", "b", "s", "h", "e", "S k", "terminal_exists_history")
        + ") -> exists u v. " + _and(conv, "a * v = b * u"),
        ("continued_fraction_convergent_exists_at_history_index", "continued_fraction_terminal_convergent_is_exact", "zero_add"),
        _intro("a", "b", "s", "h", "e", "k", "ht") + ("have hc : exists u v. " + conv,)
        + _call("continued_fraction_convergent_exists_at_history_index", "k", "a", "b", "s", "h", "e", "S k")
        + ("exact ht", "exists 0", "apply zero_add", "cases hc", "cases hc_witness", "exists x", "exists x1", "split", "exact hc_witness_witness")
        + _call("continued_fraction_terminal_convergent_is_exact", "a", "b", "s", "h", "e", "k", "x", "x1")
        + ("exact ht", "exact hc_witness_witness"),
        "The terminal convergent is constructively present and exact for every nonempty complete history, not merely a conditional assertion about a hypothetical endpoint.",
    ))
    terminal_conv = convergent_relation("s", "i", "u", "v", tag="public_terminal", variables=("s", "i", "u", "v"))
    script = _intro("a", "b", "s", "hcf") + ccf + scf
    script += ("have ht : exists u v. " + _and(convergent_relation("s", "x4", "u", "v", tag="public_terminal_chosen", variables=("s", "x4", "u", "v")), "a * v = b * u"),)
    script += _call("continued_fraction_exact_terminal_convergent_exists", "a", "b", "s", "x2", "x3", "x4")
    script += ("exact " + fcf[2], "cases ht", "cases ht_witness", "exists x4", "exists x5", "exists x6", "exact ht_witness_witness")
    rows.append(spec(
        "continued_fraction_has_exact_terminal_convergent",
        "forall a b s. (" + cf + ") -> exists i u v. " + _and(terminal_conv, "a * v = b * u"),
        ("continued_fraction_exact_terminal_convergent_exists",),
        script,
        "Every actual G071 positive rational has an explicitly constructed exact terminal convergent in the same indexed quotient-list relation.",
    ))
    return tuple(rows)


def _functionality_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    args = ("s", "h", "e", "H", "E", "u", "U", "v", "V", "a", "A", "b", "B")
    result = _and("u = a", "U = A", "v = b", "V = B")
    script = ("induction k",) + _intro(*args, "hfirst", "hsecond")
    script += ("have hleft : " + _and("u = 1", "U = 0", "v = 0", "V = 1"),)
    script += _call("cf_convergent_matrix_empty_elimination", "s", "h", "e", "u", "U", "v", "V") + ("exact hfirst",)
    script += ("have hright : " + _and("a = 1", "A = 0", "b = 0", "B = 1"),)
    script += _call("cf_convergent_matrix_empty_elimination", "s", "H", "E", "a", "A", "b", "B") + ("exact hsecond",)
    cl, fl = _cases_and("hleft", 4)
    cr, fr = _cases_and("hright", 4)
    script += cl + cr
    for index, value in enumerate(("1", "0", "0", "1")):
        if index < 3:
            script += ("split",)
        script += ("trans " + value, "exact " + fl[index], "symm", "exact " + fr[index])
    script += _intro(*args, "hfirst", "hsecond")
    script += ("have hleft : " + _predecessor("s", "h", "e", "k", "u", "U", "v", "V", "functional_left"),)
    script += _call("cf_convergent_matrix_successor_elimination", "s", "h", "e", "k", "u", "U", "v", "V") + ("exact hfirst",)
    script += ("have hright : " + _predecessor("s", "H", "E", "k", "a", "A", "b", "B", "functional_right"),)
    script += _call("cf_convergent_matrix_successor_elimination", "s", "H", "E", "k", "a", "A", "b", "B") + ("exact hsecond",)
    cel, nel = _cases_exists("hleft", 6)
    cer, ner = _cases_exists("hright", 6)
    cal, fal = _cases_and(nel, 6)
    car, far = _cases_and(ner, 6)
    script += cel + cer + cal + car
    script += ("have hcell : x5 = x11 /\\ x = x6",) + _call("cell_functional", "s", "x5", "x", "x11", "x6")
    script += ("exact " + fal[1], "exact " + far[1], "cases hcell", "have hinner : " + _and("x1 = x7", "x2 = x8", "x3 = x9", "x4 = x10"))
    script += _call("IH", "x", "h", "e", "H", "E", "x1", "x2", "x3", "x4", "x7", "x8", "x9", "x10")
    script += ("exact " + fal[0],)
    script += _call("cf_convergent_matrix_list_transport", "x6", "x", "H", "E", "k", "x7", "x8", "x9", "x10")
    script += ("symm", "exact hcell_right", "exact " + far[0])
    ci, fi = _cases_and("hinner", 4)
    script += ci
    for index, (before, after, fields) in enumerate((
        ("x5 * x1 + x3", "x11 * x7 + x9", (fi[0], fi[2])),
        ("x5 * x2 + x4", "x11 * x8 + x10", (fi[1], fi[3])),
        ("x1", "x7", (fi[0],)), ("x2", "x8", (fi[1],)),
    )):
        if index < 3:
            script += ("split",)
        script += ("trans " + before, "exact " + fal[index + 2], "trans " + after)
        if index < 2:
            script += ("rewrite hcell_left",) + tuple("rewrite " + field for field in fields) + ("refl",)
        else:
            script += ("exact " + fields[0],)
        script += ("symm", "exact " + far[index + 2])
    rows = [spec(
        "cf_convergent_matrix_prefix_functional",
        "forall k s h e H E u U v V a A b B. (" + _trace("s", "h", "e", "k", "u", "U", "v", "V", "functional_first")
        + ") -> (" + _trace("s", "H", "E", "k", "a", "A", "b", "B", "functional_second") + ") -> " + result,
        ("cf_convergent_matrix_empty_elimination", "cf_convergent_matrix_successor_elimination", "cell_functional", "cf_convergent_matrix_list_transport"),
        script,
        "HA induction proves the genuine quotient-prefix matrix is independent of its beta certificate and has unique actual entries for every tagged list and index.",
    )]
    first = convergent_relation("s", "i", "u", "v", tag="functional_convergent_first", variables=("s", "i", "u", "v"))
    second = convergent_relation("s", "i", "p", "q", tag="functional_convergent_second", variables=("s", "i", "p", "q"))
    c1, n1 = _cases_exists("hc1", 4)
    c2, n2 = _cases_exists("hc2", 4)
    s1, f1 = _cases_and(n1, 2)
    s2, f2 = _cases_and(n2, 2)
    rows.append(spec(
        "continued_fraction_convergent_functional",
        "forall s i u v p q. (" + first + ") -> (" + second + ") -> u = p /\\ v = q",
        ("cf_convergent_matrix_prefix_functional",),
        _intro("s", "i", "u", "v", "p", "q", "hc1", "hc2") + c1 + c2 + s1 + s2
        + ("have heq : " + _and("u = p", "x = x4", "v = q", "x1 = x5"),)
        + _call("cf_convergent_matrix_prefix_functional", "S i", "s", "x2", "x3", "x6", "x7", "u", "x", "v", "x1", "p", "x4", "q", "x5")
        + ("exact " + f1[1], "exact " + f2[1], "cases heq", "cases heq_right", "cases heq_right_right", "split", "exact heq_left", "exact heq_right_right_left"),
        "An actual indexed convergent has a unique natural numerator and positive denominator, independently of every auxiliary matrix-history certificate.",
    ))
    unique = "exists u v. " + _and(first, "forall p q. (" + second + ") -> p = u /\\ q = v")
    rows.append(spec(
        "continued_fraction_convergent_exists_unique_at_history_index",
        "forall i a b s h e L. (" + _old_trace("a", "b", "s", "h", "e", "L", "unique_history")
        + ") -> (" + _lt("i", "L", "unique_index") + ") -> " + unique,
        ("continued_fraction_convergent_exists_at_history_index", "continued_fraction_convergent_functional"),
        _intro("i", "a", "b", "s", "h", "e", "L", "ht", "hi") + ("have hc : exists u v. " + first,)
        + _call("continued_fraction_convergent_exists_at_history_index", "i", "a", "b", "s", "h", "e", "L")
        + ("exact ht", "exact hi", "cases hc", "cases hc_witness", "exists x", "exists x1", "split", "exact hc_witness_witness",
           "intro p", "intro q", "intro hother")
        + _call("continued_fraction_convergent_functional", "s", "i", "p", "q", "x", "x1")
        + ("exact hother", "exact hc_witness_witness"),
        "Every and only valid history index has a uniquely determined actual convergent; all auxiliary finite certificates are immaterial to its value.",
    ))
    zero = convergent_relation("s", "0", "u", "v", tag="initial_unique_given", variables=("s", "u", "v"))
    initial = convergent_relation("s", "0", "q", "1", tag="initial_unique_constructed", variables=("s", "q"))
    rows.append(spec(
        "continued_fraction_initial_convergent_is_first_quotient",
        "forall s q t u v. (" + cell("s", "q", "t") + ") -> (" + zero + ") -> u = q /\\ v = 1",
        ("continued_fraction_first_cell_is_initial_convergent", "continued_fraction_convergent_functional"),
        _intro("s", "q", "t", "u", "v", "hcell", "hc")
        + _call("continued_fraction_convergent_functional", "s", "0", "u", "v", "q", "1")
        + ("exact hc",) + _call("continued_fraction_first_cell_is_initial_convergent", "s", "q", "t") + ("exact hcell",),
        "The uniquely determined zeroth convergent is the actual first quotient divided by one; this includes the zero-numerator boundary.",
    ))
    return tuple(rows)


def _adjacent_columns_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    args = ("s", "h", "e", "u", "U", "v", "V")
    cp, np = _cases_exists("hp", 6)
    sp, fp = _cases_and(np, 6)
    script = ("induction k",) + _intro(*args, "ht")
    script += ("have hp : " + _predecessor("s", "h", "e", "0", "u", "U", "v", "V", "previous_initial_pred"),)
    script += _call("cf_convergent_matrix_successor_elimination", "s", "h", "e", "0", "u", "U", "v", "V") + ("exact ht",) + cp + sp
    script += ("have hm : exists H E. " + _trace("s", "H", "E", "1", "x5", "1", "1", "0", "previous_initial_matrix"),)
    script += _call("cf_convergent_initial_matrix_exists", "s", "x5", "x") + ("exact " + fp[1], "cases hm", "cases hm_witness")
    script += ("have heq : " + _and("u = x5", "U = 1", "v = 1", "V = 0"),)
    script += _call("cf_convergent_matrix_prefix_functional", "1", "s", "h", "e", "x6", "x7", "u", "U", "v", "V", "x5", "1", "1", "0")
    script += ("exact ht", "exact hm_witness_witness")
    cq, fq = _cases_and("heq", 4)
    script += cq + ("have hz : exists H E. " + _trace("s", "H", "E", "0", "1", "0", "0", "1", "previous_empty"),)
    script += _call("cf_convergent_matrix_empty_exists", "s") + ("cases hz", "cases hz_witness", "exists x8", "exists x9", "exists 0", "exists 1")
    script += _call("cf_convergent_matrix_entry_transport", "s", "x8", "x9", "0", "U", "0", "V", "1", "1", "0", "0", "1")
    script += ("exact " + fq[1], "refl", "exact " + fq[3], "refl", "exact hz_witness_witness")
    script += _intro(*args, "ht")
    script += ("have hp : " + _predecessor("s", "h", "e", "S k", "u", "U", "v", "V", "previous_step_pred"),)
    script += _call("cf_convergent_matrix_successor_elimination", "s", "h", "e", "S k", "u", "U", "v", "V") + ("exact ht",) + cp + sp
    script += ("have hi : " + _previous_column("x", "k", "x2", "x4", "previous_child"),)
    script += _call("IH", "x", "h", "e", "x1", "x2", "x3", "x4") + ("exact " + fp[0],)
    ci, ni = _cases_exists("hi", 4)
    script += ci
    computed = ("(x5 * x2 + x4)", "(x5 * x8 + x9)", "x2", "x8")
    script += ("have hext : exists H E. " + _trace("s", "H", "E", "S k", *computed, "previous_extension"),)
    script += _call("cf_convergent_matrix_prepend_exists", "x", "x6", "x7", "k", "x2", "x8", "x4", "x9", "x5", "s")
    script += ("exact " + ni, "exact " + fp[1], "cases hext", "cases hext_witness", "exists x10", "exists x11", "exists x5 * x8 + x9", "exists x8")
    script += _call("cf_convergent_matrix_entry_transport", "s", "x10", "x11", "S k", "U", "x5 * x8 + x9", "V", "x8", *computed)
    script += ("exact " + fp[3], "refl", "exact " + fp[5], "refl", "exact hext_witness_witness")
    rows = [spec(
        "cf_convergent_second_column_is_previous_prefix",
        "forall k s h e u U v V. (" + _trace("s", "h", "e", "S k", "u", "U", "v", "V", "previous_column_source")
        + ") -> (" + _previous_column("s", "k", "U", "V", "previous_column_result") + ")",
        ("cf_convergent_matrix_successor_elimination", "cf_convergent_initial_matrix_exists", "cf_convergent_matrix_prefix_functional",
         "cf_convergent_matrix_empty_exists", "cf_convergent_matrix_entry_transport", "cf_convergent_matrix_prepend_exists"),
        script,
        "The second matrix column is proved to be the actual previous quotient prefix of the same original list, not an arbitrary auxiliary vector chosen to make the determinant or approximation proof work.",
    )]
    cf = continued_fraction("a", "b", "s", tag="adjacent_fraction")
    current = convergent_relation("s", "S i", "u", "v", tag="adjacent_current", variables=("s", "i", "u", "v"))
    previous = convergent_relation("s", "i", "p", "q", tag="adjacent_previous", variables=("s", "i", "p", "q"))
    ccf, ncf = _cases_exists("hcf", 5)
    scf, fcf = _cases_and(ncf, 3)
    cc, nc = _cases_exists("hc", 4)
    sc, fc = _cases_and(nc, 2)
    cpv, npv = _cases_exists("hv", 4)
    spv, fpv = _cases_and(npv, 2)
    script = _intro("a", "b", "s", "i", "u", "v", "p", "q", "hcf", "hc", "hv") + ccf + scf + cc + sc + cpv + spv
    script += ("have hp : " + _previous_column("s", "S i", "x5", "x6", "adjacent_identification"),)
    script += _call("cf_convergent_second_column_is_previous_prefix", "S i", "s", "x7", "x8", "u", "x5", "v", "x6") + ("exact " + fc[1],)
    cprev, nprev = _cases_exists("hp", 4)
    script += cprev + ("have heq : " + _and("p = x5", "x9 = x15", "q = x6", "x10 = x16"),)
    script += _call("cf_convergent_matrix_prefix_functional", "S i", "s", "x11", "x12", "x13", "x14", "p", "x9", "q", "x10", "x5", "x15", "x6", "x16")
    script += ("exact " + fpv[1], "exact " + nprev)
    cqe, fqe = _cases_and("heq", 4)
    script += cqe + ("rewrite " + fqe[0],) * 2 + ("rewrite " + fqe[2],) * 2
    script += _call("cf_approximation_derived_invariant_determinant", "a", "b", "u", "x5", "v", "x6")
    script += _call("cf_convergent_actual_prefix_error_invariant", "S i", "a", "b", "s", "x2", "x3", "S x4", "x7", "x8", "u", "x5", "v", "x6")
    script += ("exact " + fcf[2], "exact " + fc[1])
    rows.append(spec(
        "continued_fraction_adjacent_convergent_determinant",
        "forall a b s i u v p q. (" + cf + ") -> (" + current + ") -> (" + previous
        + ") -> (u * q + 1 = p * v \\/ p * v + 1 = u * q)",
        ("cf_convergent_second_column_is_previous_prefix", "cf_convergent_matrix_prefix_functional",
         "cf_approximation_derived_invariant_determinant", "cf_convergent_actual_prefix_error_invariant"),
        script,
        "Two actual successive convergents of the same G071 list have determinant ±1; both columns are identified with their genuine indexed computations.",
    ))
    conv = convergent_relation("s", "i", "u", "v", tag="coprime_convergent", variables=("s", "i", "u", "v"))
    script = _intro("a", "b", "s", "i", "u", "v", "hcf", "hc") + ccf + scf + cc + sc
    script += _call("cf_approximation_unit_determinant_coprime", "u", "x5", "v", "x6")
    script += _call("cf_approximation_derived_invariant_determinant", "a", "b", "u", "x5", "v", "x6")
    script += _call("cf_convergent_actual_prefix_error_invariant", "i", "a", "b", "s", "x2", "x3", "S x4", "x7", "x8", "u", "x5", "v", "x6")
    script += ("exact " + fcf[2], "exact " + fc[1])
    rows.append(spec(
        "continued_fraction_convergent_coprime",
        "forall a b s i u v. (" + cf + ") -> (" + conv + ") -> (" + coprime("u", "v", tag="actual_convergent_coprime") + ")",
        ("cf_approximation_unit_determinant_coprime", "cf_approximation_derived_invariant_determinant", "cf_convergent_actual_prefix_error_invariant"),
        script,
        "Every actual convergent is reduced, including 0/1 and the exact terminal rational; coprimality follows from the proved determinant, not the definition.",
    ))
    return tuple(rows)


def _best_endpoint_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    cf = continued_fraction("a", "b", "s", tag="best_actual_fraction")
    conv = convergent_relation("s", "i", "u", "v", tag="best_actual_convergent", variables=("s", "i", "u", "v"))
    ccf, ncf = _cases_exists("hcf", 5)
    scf, fcf = _cases_and(ncf, 3)
    ccv, ncv = _cases_exists("hconv", 4)
    scv, fcv = _cases_and(ncv, 2)
    signed_script = _intro("a", "b", "s", "i", "u", "v", "hcf", "hconv", "rp", "rn", "t", "C", "D", "ht", "hlt", "hc", "hd")
    signed_script += ccf + scf + ccv + scv
    signed_script += _call("cf_approximation_derived_invariant_best_signed", "a", "b", "u", "x5", "v", "x6", "rp", "rn", "t", "C", "D")
    signed_script += _call("cf_convergent_actual_prefix_error_invariant", "i", "a", "b", "s", "x2", "x3", "S x4", "x7", "x8", "u", "x5", "v", "x6")
    signed_script += ("exact " + fcf[2], "exact " + fcv[1], "exact ht", "exact hlt", "exact hc", "exact hd")
    return (
        spec(
            "continued_fraction_convergent_best_approximation_signed",
            "forall a b s i u v. (" + cf + ") -> (" + conv + ") -> (" + _best("a", "b", "u", "v", "best_signed", signed=True) + ")",
            ("cf_convergent_actual_prefix_error_invariant", "cf_approximation_derived_invariant_best_signed"),
            signed_script,
            "Full G072, strengthened to arbitrary signed numerator representatives: every actual convergent of the G071 quotient list minimizes absolute cross-product error among all smaller positive denominators.",
        ),
        spec(
            "continued_fraction_convergent_best_approximation",
            "forall a b s i u v. (" + _and(cf, conv) + ") -> (" + _best("a", "b", "u", "v", "best_natural", signed=False) + ")",
            ("continued_fraction_convergent_best_approximation_signed", "cf_approximation_natural_error_as_signed"),
            _intro("a", "b", "s", "i", "u", "v", "h") + ("cases h",)
            + ("have hbest : " + _best("a", "b", "u", "v", "natural_from_signed", signed=True),)
            + _call("continued_fraction_convergent_best_approximation_signed", "a", "b", "s", "i", "u", "v")
            + ("exact h_left", "exact h_right")
            + _intro("r", "t", "C", "D", "ht", "hlt", "hc", "hd")
            + _call("hbest", "r", "0", "t", "C", "D")
            + ("exact ht", "exact hlt", "exact hc")
            + _call("cf_approximation_natural_error_as_signed", "a", "b", "r", "t", "D") + ("exact hd",),
            "Exact natural-domain G072: actual G071 fraction and actual indexed convergent imply |a*v-b*u|≤|a*t-b*r| for every natural numerator r and every 0<t<v, with no assumed approximation premise.",
        ),
    )


__all__ = ["convergent_matrix_state_code_relation", "convergent_matrix_state_at_relation", "convergent_matrix_trace_relation", "convergent_relation", "best_approximation_second_kind_relation",
           "make_continued_fraction_convergents_candidate_theorems"]
