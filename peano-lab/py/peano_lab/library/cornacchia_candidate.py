"""Cornacchia's actual prime two-square Euclidean algorithm in original HA.

The state carries consecutive remainders and absolute Bezout coefficients.
Every arithmetic and history relation is a conservative first-order expansion;
no supplied representation or unrelated Euclidean trace certifies this run.
"""

from __future__ import annotations

from typing import Any, Callable

from ..kernel.terms import parse_term_with_names
from .continued_fraction_candidate import _pair_term
from .euclidean_complexity_candidate import _gcd_term
from .fermat_residue_map_candidate import prime
from .fermat_residue_product_candidate import coprime
from .finite_fold_surface import _beta_at_term, _identifier
from .ha_generalized_crt_congruence_candidate import _checked_term, balanced_mod_eq


def _context(*terms: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(name for term in terms for name in parse_term_with_names(term)[1])) or ("cor_unused",)


def _mod(p: str, a: str, b: str, *, tag: str) -> str:
    return balanced_mod_eq(p, a, b, tag=f"cor_{tag}", variables=_context(p, a, b))


def _gcd(g: str, a: str, b: str, *, tag: str) -> str:
    context = _context(g, a, b)
    return _gcd_term(*(_checked_term(value, context) for value in (g, a, b)), tag=f"cor_{tag}", arguments=context)


def _lt(a: str, b: str, *, tag: str) -> str:
    return f"exists cor_gap_{tag}. cor_gap_{tag} + S ({a}) = ({b})"


def _le(a: str, b: str, *, tag: str) -> str:
    return f"exists cor_bound_{tag}. cor_bound_{tag} + ({a}) = ({b})"


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return (*(f"specialize {name} {argument}" for argument in arguments), f"apply {name}")


def _intros(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _rewrite(equation: str, count: int, *, at: str | None = None) -> tuple[str, ...]:
    return (f"rewrite {equation}" + (f" at {at}" if at else ""),) * count


def _alternating(p: str, z: str, a: str, r: str, u: str, t: str, *, tag: str) -> str:
    return (
        f"((({_mod(p, a, f'{z} * {u}', tag=f'{tag}_ap')}) /\\ "
        f"({_mod(p, f'{r} + {z} * {t}', '0', tag=f'{tag}_rn')})) \\/ "
        f"(({_mod(p, f'{a} + {z} * {u}', '0', tag=f'{tag}_an')}) /\\ "
        f"({_mod(p, r, f'{z} * {t}', tag=f'{tag}_rp')})))"
    )


def _and(*formulas: str) -> str:
    return formulas[0] if len(formulas) == 1 else f"(({formulas[0]}) /\\ ({_and(*formulas[1:])}))"


def _root(p: str, z: str, *, tag: str) -> str:
    return _and(
        prime(p, tag=f"cor_{tag}_prime"), f"~({z} = 0)",
        _lt(z, p, tag=f"{tag}_bound"), f"exists cor_factor_{tag}. {z} * {z} + 1 = {p} * cor_factor_{tag}",
    )


def _invariant(p: str, z: str, a: str, r: str, u: str, t: str, *, tag: str) -> str:
    return _and(
        _root(p, z, tag=f"{tag}_root"), f"~({r} = 0)", _lt(r, a, tag=f"{tag}_order"),
        f"~({t} = 0)", _lt(p, f"{a} * {a}", tag=f"{tag}_previous"),
        f"{p} = {a} * {t} + {r} * {u}", coprime(a, r, tag=f"cor_{tag}_coprime"),
        _alternating(p, z, a, r, u, t, tag=f"{tag}_alternating"),
    )


def _parts(name: str, count: int) -> tuple[str, ...]:
    return tuple(name + "_right" * i + ("_left" if i < count - 1 else "") for i in range(count))


def _cases_and(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_right" * i for i in range(count - 1))


def _arguments(*arguments: str) -> tuple[str, ...]:
    values = tuple(_identifier(value, "Cornacchia relation argument") for value in arguments)
    if len(set(values)) != len(values):
        raise ValueError("Cornacchia relation arguments must be distinct")
    if any(value.startswith(("cor_", "cf_", "ff_", "frp_", "frm_", "hgcrt_", "ec_")) for value in values):
        raise ValueError("generated Cornacchia binder captures an argument")
    return values


def cornacchia_root(p: str, z: str, *, tag: str) -> str:
    """Expand a positive bounded root of minus one at an actual prime."""

    return _root(*_arguments(p, z), tag=_identifier(tag, "Cornacchia binder tag"))


def cornacchia_alternating_congruences(p: str, z: str, a: str, r: str, u: str, t: str, *, tag: str) -> str:
    """Expand the two explicit alternating natural root-coefficient signs."""

    return _alternating(*_arguments(p, z, a, r, u, t), tag=_identifier(tag, "Cornacchia binder tag"))


def cornacchia_state_invariant(p: str, z: str, a: str, r: str, u: str, t: str, *, tag: str) -> str:
    """Expand the rooted arithmetic invariant, not an algorithm oracle."""

    return _invariant(*_arguments(p, z, a, r, u, t), tag=_identifier(tag, "Cornacchia binder tag"))


def _packed(a: str, r: str, u: str, t: str, q: str) -> str:
    return _pair_term(_pair_term(a, r), _pair_term(_pair_term(u, t), q))


def _state(h: str, e: str, i: str, a: str, r: str, u: str, t: str, q: str, *, tag: str) -> str:
    return _beta_at_term(h, e, i, _packed(a, r, u, t, q), tag=f"cor_{tag}", avoid=_context(h, e, i, a, r, u, t, q))


def _preserve(h: str, e: str, H: str, E: str, l: str, *, tag: str) -> str:
    i, v = f"cor_index_{tag}", f"cor_value_{tag}"
    context = _context(h, e, H, E, l) + (i, v)
    before = _beta_at_term(h, e, i, v, tag=f"cor_{tag}_before", avoid=context)
    after = _beta_at_term(H, E, i, v, tag=f"cor_{tag}_after", avoid=context)
    return f"forall {i} {v}. ({_lt(i, l, tag=f'{tag}_bound')}) -> ({before}) -> ({after})"


def _transition(p: str, h: str, e: str, i: str, *, tag: str) -> str:
    a, r, u, t, q, A, R, U, T, Q = (f"cor_{role}_{tag}" for role in (
        "a", "r", "u", "t", "q", "next_a", "next_r", "next_u", "next_t", "next_q",
    ))
    before = _state(h, e, f"S {i}", a, r, u, t, q, tag=f"{tag}_before")
    after = _state(h, e, i, A, R, U, T, Q, tag=f"{tag}_after")
    step = _and(
        f"{A} = {r}", f"{U} = {t}", f"{a} = {r} * {q} + {R}",
        _lt(R, r, tag=f"{tag}_remainder"), f"{T} = {q} * {t} + {u}",
        _lt(p, f"{r} * {r}", tag=f"{tag}_guard"),
    )
    return f"exists {a} {r} {u} {t} {q} {A} {R} {U} {T} {Q}. ({_and(before, after, step)})"


def _run(p: str, a: str, r: str, u: str, t: str, R: str, T: str, h: str, e: str, l: str, *, tag: str) -> str:
    A, U, Q, i = (f"cor_{role}_{tag}" for role in ("terminal_a", "terminal_u", "initial_q", "index"))
    terminal = _state(h, e, "0", A, R, U, T, "0", tag=f"{tag}_terminal")
    initial = _state(h, e, l, a, r, u, t, Q, tag=f"{tag}_initial")
    steps = f"forall {i}. ({_lt(i, l, tag=f'{tag}_index')}) -> ({_transition(p, h, e, i, tag=f'{tag}_step')})"
    return f"exists {A} {U} {Q}. ({_and(terminal, initial, f'~({R} = 0)', f'~({T} = 0)', _lt(f'{R} * {R}', p, tag=f'{tag}_stop'), steps)})"


def cornacchia_state_at(h: str, e: str, i: str, a: str, r: str, u: str, t: str, q: str, *, tag: str) -> str:
    """Decode both remainders, both coefficients, and the actual quotient."""

    return _state(*_arguments(h, e, i, a, r, u, t, q), tag=_identifier(tag, "Cornacchia binder tag"))


def cornacchia_transition_at(p: str, h: str, e: str, i: str, *, tag: str) -> str:
    """Expand one guarded, adjacent encoded division/coefficient transition."""

    return _transition(*_arguments(p, h, e, i), tag=_identifier(tag, "Cornacchia binder tag"))


def cornacchia_euclidean_run(p: str, a: str, r: str, u: str, t: str, R: str, T: str, h: str, e: str, l: str, *, tag: str) -> str:
    """Expand a complete reverse-indexed first-stop history with stored quotients.

    Chronological time runs from index l to zero. Every predecessor is above
    the square-root threshold and every transition is the real bounded division
    together with its absolute-coefficient recurrence. Index zero is stopped.
    """

    return _run(*_arguments(p, a, r, u, t, R, T, h, e, l), tag=_identifier(tag, "Cornacchia binder tag"))


def _trace(p: str, z: str, R: str, T: str, h: str, e: str, l: str, *, tag: str) -> str:
    return _and(_root(p, z, tag=f"{tag}_root"), _run(p, p, z, "0", "1", R, T, h, e, l, tag=f"{tag}_run"))


def cornacchia_trace(p: str, z: str, R: str, T: str, h: str, e: str, l: str, *, tag: str) -> str:
    """Expand the rooted complete first-stop algorithm from (p,z,0,1)."""

    return _trace(*_arguments(p, z, R, T, h, e, l), tag=_identifier(tag, "Cornacchia binder tag"))


def _completion(p: str, a: str, r: str, u: str, t: str, *, tag: str) -> str:
    R, T, h, e, l = (f"cor_{role}_{tag}" for role in ("result_r", "result_t", "history", "scale", "length"))
    return f"exists {R} {T} {h} {e} {l}. ({_and(_run(p, a, r, u, t, R, T, h, e, l, tag=f'{tag}_run'), f'{p} = {R} * {R} + {T} * {T}')})"


def _root_completion(p: str, z: str, *, tag: str) -> str:
    R, T, h, e, l = (f"cor_{role}_{tag}" for role in ("result_r", "result_t", "history", "scale", "length"))
    return f"exists {R} {T} {h} {e} {l}. ({_and(_trace(p, z, R, T, h, e, l, tag=f'{tag}_trace'), f'{p} = {R} * {R} + {T} * {T}')})"


def _cases_exists(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_witness" * i for i in range(count))


def make_cornacchia_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Return genuine ordinary-kernel candidate bodies, without admission."""

    inv = _parts("hi", 8)
    root = _parts("hr", 4)
    trace_body = "ht" + "_witness" * 3
    trace = _parts(trace_body, 6)
    step_body = "hst" + "_witness" * 10
    step_parts = _parts(step_body, 3)

    return (
        spec(
            "cornacchia_prime_not_square",
            f"forall p z. ({prime('p', tag='cor_nonsquare')}) -> ~(p = z * z)",
            (),
            (*_intros("p", "z", "hp", "heq"), "cases hp", "specialize hp_right z",
             "specialize hp_right z", "have hz : z = 1 \\/ z = 1", "apply hp_right", "exact heq", "cases hz",
             "apply hp_left", "trans z * z", "exact heq", *_rewrite("hz_left", 2), "norm_num",
             "apply hp_left", "trans z * z", "exact heq", *_rewrite("hz_right", 2), "norm_num"),
            "No natural square equals a prime, constructively and without factorization search.",
        ),
        spec(
            "cornacchia_prime_square_strictly_above",
            f"forall p. ({prime('p', tag='cor_initial_square')}) -> ({_lt('p', 'p * p', tag='prime_square')})",
            ("prime_two_le", "prime_nonzero", "lt_of_lt_of_le", "mul_lt_mul_right_nonzero", "one_mul"),
            (*_intros("p", "hp"), "have hone : " + _lt("1", "p", tag="prime_above_one"),
             *_call("lt_of_lt_of_le", "1", "2", "p"), "exists 0", "norm_num",
             *_call("prime_two_le", "p"), "exact hp",
             "have hmul : " + _lt("1 * p", "p * p", tag="prime_mul_bound"),
             *_call("mul_lt_mul_right_nonzero", "1", "p", "p"), "exact hone",
             "intro hz", *_call("prime_nonzero", "p"), "exact hp", "exact hz",
             "specialize one_mul p", "rewrite one_mul at hmul", "exact hmul"),
            "The initial previous remainder p already has square strictly above p.",
        ),
        spec(
            "cornacchia_prime_square_comparison",
            f"forall p r. ({prime('p', tag='cor_compare')}) -> "
            f"(({_lt('r * r', 'p', tag='compare_below')}) \\/ ({_lt('p', 'r * r', tag='compare_above')}))",
            ("le_or_lt", "le_eq_or_lt", "cornacchia_prime_not_square"),
            (*_intros("p", "r", "hp"),
             "have hs : (" + _le("p", "r * r", tag="compare_weak") + ") \\/ (" + _lt("r * r", "p", tag="compare_small") + ")",
             *_call("le_or_lt", "p", "(r * r)"), "cases hs",
             "have ht : p = r * r \\/ " + _lt("p", "r * r", tag="compare_strict"),
             *_call("le_eq_or_lt", "p", "(r * r)"), "exact hs_left", "cases ht",
             "exfalso", *_call("cornacchia_prime_not_square", "p", "r"), "exact hp", "exact ht_left",
             "right", "exact ht_right", "left", "exact hs_right"),
            "The square-root stopping test has exactly two constructive branches at a prime: strictly below or strictly above.",
        ),
        spec(
            "cornacchia_division_quotient_nonzero",
            "forall a r q s. a = r * q + s -> "
            f"({_lt('r', 'a', tag='quotient_order')}) -> ({_lt('s', 'r', tag='quotient_remainder')}) -> ~(q = 0)",
            ("zero_add", "lt_trans", "lt_irrefl_expanded"),
            (*_intros("a", "r", "q", "s", "hdiv", "hra", "hsr", "hq"),
             "have has : a = s", "trans r * q + s", "exact hdiv", "rewrite hq", "simp [zero_add]",
             "rewrite has at hra", *_call("lt_irrefl_expanded", "r"),
             *_call("lt_trans", "r", "s", "r"), "exact hra", "exact hsr"),
            "Every genuine decreasing Euclidean division has a positive quotient.",
        ),
        spec(
            "cornacchia_coprime_euclidean_step",
            "forall a r q s. a = r * q + s -> "
            f"({coprime('a', 'r', tag='cor_coprime_old')}) -> ({coprime('r', 's', tag='cor_coprime_new')})",
            ("coprime_to_is_gcd_one", "is_gcd_euclid_backward", "is_gcd_one_to_coprime"),
            (*_intros("a", "r", "q", "s", "hdiv", "hc"),
             *_call("is_gcd_one_to_coprime", "r", "s"),
             *_call("is_gcd_euclid_backward", "1", "a", "r", "q", "s"), "exact hdiv",
             *_call("coprime_to_is_gcd_one", "a", "r"), "exact hc"),
            "Euclidean remainder transport preserves the exact common-divisor coprimality invariant.",
        ),
        spec(
            "cornacchia_above_threshold_remainder_nonzero",
            "forall p r s. ~(p = 0) -> "
            f"({_lt('p', 'r * r', tag='remainder_guard')}) -> "
            f"({coprime('r', 's', tag='cor_remainder_coprime')}) -> ~(s = 0)",
            ("multiple_refl", "one_le_of_ne_zero", "lt_not_le"),
            (*_intros("p", "r", "s", "hp", "hguard", "hc", "hs"),
             "have hr : r = 1", "specialize hc r", "apply hc",
             *_call("multiple_refl", "r"), "exists 0", "rewrite hs", "symm", "apply PA5",
             *_rewrite("hr", 2, at="hguard"), "have hone : 1 * 1 = 1", "norm_num", "rewrite hone at hguard",
             *_call("lt_not_le", "p", "1"), "exact hguard", *_call("one_le_of_ne_zero", "p"), "exact hp"),
            "Before the square-root threshold, coprime Euclid cannot jump to zero; its next remainder is positive.",
        ),
        spec(
            "cornacchia_coefficient_step_nonzero",
            "forall q t u T. ~(q = 0) -> ~(t = 0) -> T = q * t + u -> ~(T = 0)",
            ("add_eq_zero_left", "mul_ne_zero"),
            (*_intros("q", "t", "u", "T", "hq", "ht", "hT", "hz"),
             *_call("mul_ne_zero", "q", "t"), "exact hq", "exact ht",
             *_call("add_eq_zero_left", "(q * t)", "u"), "trans T", "symm", "exact hT", "exact hz"),
            "The absolute coefficient recurrence preserves positivity without signed natural subtraction.",
        ),
        spec(
            "cornacchia_coefficient_step_exists",
            "forall q t u. exists T. T = q * t + u",
            (),
            (*_intros("q", "t", "u"), "exists q * t + u", "refl"),
            "The next absolute coefficient is an actual natural witness of the multiplication-and-addition recurrence.",
        ),
        spec(
            "cornacchia_cross_identity_step",
            "forall p a r u t q s T. p = a * t + r * u -> a = r * q + s -> T = q * t + u -> p = r * T + s * t",
            ("mul_add", "add_mul", "mul_assoc", "mul_comm", "add_assoc", "add_comm"),
            (*_intros("p", "a", "r", "u", "t", "q", "s", "T", "hp", "ha", "hT"),
             "rewrite hp", "rewrite ha", "rewrite hT",
             "simp [mul_add, add_mul, mul_assoc, mul_comm, add_assoc, add_comm]"),
            "The actual remainder and coefficient recurrences preserve p=a*t+r*u exactly.",
        ),
        spec(
            "cornacchia_coefficient_square_below_prime",
            "forall p a r u t. p = a * t + r * u -> "
            f"({_lt('p', 'a * a', tag='coefficient_previous')}) -> ~(t = 0) -> "
            f"({_lt('t * t', 'p', tag='coefficient_square')})",
            ("le_add_right", "le_or_lt", "mul_le_mul_left", "le_trans",
             "lt_not_le", "mul_lt_mul_right_nonzero", "lt_of_lt_of_le"),
            (*_intros("p", "a", "r", "u", "t", "hp", "ha", "ht"),
             "have hm : " + _le("a * t", "p", tag="coefficient_product"),
             "rewrite hp", *_call("le_add_right", "(a * t)", "(r * u)"),
             "have hta : " + _lt("t", "a", tag="coefficient_below_previous"),
             "have hs : (" + _le("a", "t", tag="coefficient_compare_le") + ") \\/ (" + _lt("t", "a", tag="coefficient_compare_lt") + ")",
             *_call("le_or_lt", "a", "t"), "cases hs", "exfalso",
             *_call("lt_not_le", "p", "(a * a)"), "exact ha",
             *_call("le_trans", "(a * a)", "(a * t)", "p"),
             *_call("mul_le_mul_left", "a", "t", "a"), "exact hs_left", "exact hm", "exact hs_right",
             *_call("lt_of_lt_of_le", "(t * t)", "(a * t)", "p"),
             *_call("mul_lt_mul_right_nonzero", "t", "a", "t"), "exact hta", "exact ht", "exact hm"),
            "The cross identity and the previous remainder's square bound force the current positive coefficient's square below p.",
        ),
        spec(
            "cornacchia_mod_subtraction_transport",
            "forall p a b c d e. a = b + c -> "
            f"({_mod('p', 'a', 'd', tag='subtract_whole')}) -> "
            f"({_mod('p', 'b', 'e', tag='subtract_part')}) -> "
            f"({_mod('p', 'c + e', 'd', tag='subtract_result')})",
            ("mod_eq_add", "mod_eq_refl", "mod_eq_symm", "mod_eq_trans", "add_comm"),
            (*_intros("p", "a", "b", "c", "d", "e", "ha", "hw", "hb"),
             "have hsum : " + _mod("p", "b + c", "e + c", tag="subtract_sum"),
             *_call("mod_eq_add", "p", "b", "e", "c", "c"), "exact hb", *_call("mod_eq_refl", "p", "c"),
             "have hrev : " + _mod("p", "e + c", "b + c", tag="subtract_reverse"),
             *_call("mod_eq_symm", "p", "(b + c)", "(e + c)"), "exact hsum",
             "have hresult : " + _mod("p", "e + c", "d", tag="subtract_actual_result"),
             *_call("mod_eq_trans", "p", "(e + c)", "a", "d"), "rewrite ha", "exact hrev", "exact hw",
             "have hswap : c + e = e + c", "apply add_comm", "rewrite hswap", "exact hresult"),
            "Balanced congruence transports an actual natural difference without introducing integer subtraction.",
        ),
        spec(
            "cornacchia_signed_step_direct",
            "forall p z a r u t q s T. a = r * q + s -> T = q * t + u -> "
            f"({_mod('p', 'a', 'z * u', tag='direct_old_a')}) -> "
            f"({_mod('p', 'r + z * t', '0', tag='direct_old_r')}) -> "
            f"({_mod('p', 's', 'z * T', tag='direct_new')})",
            ("mul_add", "add_mul", "mul_assoc", "mul_comm", "add_assoc", "add_comm",
             "mod_eq_add", "mod_eq_refl", "mod_eq_mul_left", "cornacchia_mod_subtraction_transport"),
            (*_intros("p", "z", "a", "r", "u", "t", "q", "s", "T", "ha", "hT", "hA", "hR"),
             "have heq : a + q * (z * t) = q * (r + z * t) + s", "rewrite ha",
             "simp [mul_add, add_mul, mul_assoc, mul_comm, add_assoc, add_comm]",
             "have hsum : " + _mod("p", "a + q * (z * t)", "z * u + q * (z * t)", tag="direct_sum"),
             *_call("mod_eq_add", "p", "a", "(z * u)", "(q * (z * t))", "(q * (z * t))"), "exact hA",
             *_call("mod_eq_refl", "p", "(q * (z * t))"),
             "have hzero : " + _mod("p", "q * (r + z * t)", "q * 0", tag="direct_zero_scaled"),
             *_call("mod_eq_mul_left", "p", "(r + z * t)", "0", "q"), "exact hR",
             "have hqzero : q * 0 = 0", "apply PA5", "rewrite hqzero at hzero",
             "have hsmall : " + _mod("p", "s + 0", "z * u + q * (z * t)", tag="direct_small"),
             *_call("cornacchia_mod_subtraction_transport", "p", "(a + q * (z * t))", "(q * (r + z * t))", "s", "(z * u + q * (z * t))", "0"),
             "exact heq", "exact hsum", "exact hzero",
             "have hszero : s + 0 = s", "apply PA3", "rewrite hszero at hsmall",
             "have hcoef : z * T = z * u + q * (z * t)", "rewrite hT",
             "simp [mul_add, mul_assoc, mul_comm, add_comm]", "rewrite hcoef", "exact hsmall"),
            "One Euclidean step turns a positive/negative root-coefficient pair into the next positive coefficient congruence.",
        ),
        spec(
            "cornacchia_signed_step_opposite",
            "forall p z a r u t q s T. a = r * q + s -> T = q * t + u -> "
            f"({_mod('p', 'a + z * u', '0', tag='opposite_old_a')}) -> "
            f"({_mod('p', 'r', 'z * t', tag='opposite_old_r')}) -> "
            f"({_mod('p', 's + z * T', '0', tag='opposite_new')})",
            ("mul_add", "add_mul", "mul_assoc", "mul_comm", "add_assoc", "add_comm",
             "mod_eq_mul_right", "cornacchia_mod_subtraction_transport"),
            (*_intros("p", "z", "a", "r", "u", "t", "q", "s", "T", "ha", "hT", "hA", "hR"),
             "have heq : a + z * u = r * q + (s + z * u)", "rewrite ha", "apply add_assoc",
             "have hscaled : " + _mod("p", "r * q", "(z * t) * q", tag="opposite_scaled"),
             *_call("mod_eq_mul_right", "p", "r", "(z * t)", "q"), "exact hR",
             "have hsmall : " + _mod("p", "(s + z * u) + (z * t) * q", "0", tag="opposite_small"),
             *_call("cornacchia_mod_subtraction_transport", "p", "(a + z * u)", "(r * q)", "(s + z * u)", "0", "((z * t) * q)"),
             "exact heq", "exact hA", "exact hscaled",
             "have hcoef : s + z * T = (s + z * u) + (z * t) * q", "rewrite hT",
             "simp [mul_add, mul_assoc, mul_comm, add_assoc, add_comm]",
             "congr", "refl", "congr", "trans (q * t) * z", "symm", "apply mul_assoc",
             "trans (t * q) * z", "congr", "apply mul_comm", "refl", "apply mul_assoc", "refl",
             "rewrite hcoef", "exact hsmall"),
            "The other alternating sign branch yields the next opposite coefficient congruence with actual natural witnesses.",
        ),
        spec(
            "cornacchia_alternating_congruences_step",
            "forall p z a r u t q s T. a = r * q + s -> T = q * t + u -> "
            f"({_alternating('p', 'z', 'a', 'r', 'u', 't', tag='alternating_old')}) -> "
            f"({_alternating('p', 'z', 'r', 's', 't', 'T', tag='alternating_new')})",
            ("cornacchia_signed_step_direct", "cornacchia_signed_step_opposite"),
            (*_intros("p", "z", "a", "r", "u", "t", "q", "s", "T", "ha", "hT", "halt"),
             "cases halt", "cases halt_left", "right", "split", "exact halt_left_right",
             *_call("cornacchia_signed_step_direct", "p", "z", "a", "r", "u", "t", "q", "s", "T"),
             "exact ha", "exact hT", "exact halt_left_left", "exact halt_left_right",
             "cases halt_right", "left", "split", "exact halt_right_right",
             *_call("cornacchia_signed_step_opposite", "p", "z", "a", "r", "u", "t", "q", "s", "T"),
             "exact ha", "exact hT", "exact halt_right_left", "exact halt_right_right"),
            "Successive actual Euclidean states toggle the two explicit root-coefficient sign patterns.",
        ),
        spec(
            "cornacchia_alternating_congruences_norm_multiple",
            "forall p z a r u t. (exists k. z * z + 1 = p * k) -> "
            f"({_alternating('p', 'z', 'a', 'r', 'u', 't', tag='norm_alternating')}) -> exists k. r * r + t * t = p * k",
            ("negative_one_linear_congruence_norm_multiple", "negative_one_opposite_linear_congruence_norm_multiple", "mod_eq_symm", "add_comm"),
            (*_intros("p", "z", "a", "r", "u", "t", "hroot", "halt"),
             "have hswap : r * r + t * t = t * t + r * r", "apply add_comm", "rewrite hswap",
             "cases halt", "cases halt_left",
             *_call("negative_one_opposite_linear_congruence_norm_multiple", "p", "z", "t", "r"), "exact hroot",
             "have hs : z * t + r = r + z * t", "apply add_comm", "rewrite hs", "exact halt_left_right",
             "cases halt_right", *_call("negative_one_linear_congruence_norm_multiple", "p", "z", "t", "r"), "exact hroot",
             *_call("mod_eq_symm", "p", "r", "(z * t)"), "exact halt_right_right"),
            "The actual alternating root invariant makes the current remainder/coefficient two-square norm divisible by p.",
        ),
        spec(
            "cornacchia_stopping_state_represents_prime",
            "forall p z a r u t. (exists k. z * z + 1 = p * k) -> "
            f"({_alternating('p', 'z', 'a', 'r', 'u', 't', tag='stopping_alternating')}) -> "
            "p = a * t + r * u -> "
            f"({_lt('p', 'a * a', tag='stopping_previous')}) -> ~(r = 0) -> ~(t = 0) -> "
            f"({_lt('r * r', 'p', tag='stopping_remainder')}) -> p = r * r + t * t",
            ("cornacchia_coefficient_square_below_prime", "cornacchia_alternating_congruences_norm_multiple",
             "nonzero_coordinate_pair_has_positive_square_norm", "add_lt_add", "bounded_divisible_two_square_norm_equals_prime"),
            (*_intros("p", "z", "a", "r", "u", "t", "hroot", "halt", "hid", "ha", "hr", "ht", "hstop"),
             *_call("bounded_divisible_two_square_norm_equals_prime", "p", "r", "t"),
             *_call("nonzero_coordinate_pair_has_positive_square_norm", "r", "t"), "intro hz", "cases hz", "apply hr", "exact hz_left",
             *_call("cornacchia_alternating_congruences_norm_multiple", "p", "z", "a", "r", "u", "t"), "exact hroot", "exact halt",
             *_call("add_lt_add", "(r * r)", "p", "(t * t)", "p"), "exact hstop",
             *_call("cornacchia_coefficient_square_below_prime", "p", "a", "r", "u", "t"), "exact hid", "exact ha", "exact ht"),
            "At the first positive remainder below sqrt(p), the actual Euclidean coefficient completes an exact two-square representation of p.",
        ),
        spec(
            "cornacchia_root_nonzero",
            f"forall p z. ({prime('p', tag='cor_root_nonzero')}) -> (exists k. z * z + 1 = p * k) -> ~(z = 0)",
            ("divisor_one",),
            (*_intros("p", "z", "hp", "hn", "hz"), "cases hp", "apply hp_left",
             *_call("divisor_one", "p"), "cases hn", "exists x", "trans z * z + 1",
             *_rewrite("hz", 2), "norm_num", "exact hn_witness"),
            "A genuine root of minus one modulo a prime is nonzero.",
        ),
        spec(
            "cornacchia_root_coprime",
            f"forall p z. ({_root('p', 'z', tag='coprime_root')}) -> ({coprime('p', 'z', tag='cor_root_coprime')})",
            ("prime_not_divides_coprime", "four_square_bounded_multiple_is_zero"),
            (*_intros("p", "z", "hr"), *_cases_and("hr", 4),
             *_call("prime_not_divides_coprime", "p", "z"), f"exact {root[0]}",
             "intro hdiv", f"apply {root[1]}", *_call("four_square_bounded_multiple_is_zero", "p", "z"),
             f"exact {root[2]}", "exact hdiv"),
            "The bounded nonzero root is coprime to its prime, with the bounded-divisibility contradiction checked explicitly.",
        ),
        spec(
            "cornacchia_root_exists",
            f"forall p. ({prime('p', tag='cor_root_exists')}) -> (exists k. p = 4 * k + 1) -> exists z. ({_root('p', 'z', tag='root_exists')})",
            ("zero_or_succ", "prime_nonzero", "prime_mod_four_one_bounded_divisible_two_square_norm_exists", "cornacchia_root_nonzero"),
            (*_intros("p", "hp", "hfour"), "specialize zero_or_succ p", "cases zero_or_succ",
             "exfalso", *_call("prime_nonzero", "p"), "exact hp", "exact zero_or_succ_left",
             "cases zero_or_succ_right",
             "have hz : exists z k. ((" + _lt("z", "p", tag="root_construct_bound") + ") /\\ z * z + 1 = p * k)",
             *_call("prime_mod_four_one_bounded_divisible_two_square_norm_exists", "p", "x"),
             "exact zero_or_succ_right_witness", "exact hp", "exact hfour",
             "cases hz", "cases hz_witness", "cases hz_witness_witness",
             "exists x1", "split", "exact hp", "split", "intro hzero",
             *_call("cornacchia_root_nonzero", "p", "x1"), "exact hp", "exists x2", "exact hz_witness_witness_right", "exact hzero",
             "split", "exact hz_witness_witness_left", "exists x2", "exact hz_witness_witness_right"),
            "Every prime one modulo four constructively supplies an actual positive bounded root of minus one for the algorithm.",
        ),
        spec(
            "cornacchia_initial_alternating_congruences",
            f"forall p z. ({_alternating('p', 'z', 'p', 'z', '0', '1', tag='initial_alternating')})",
            ("multiple_refl", "multiple_implies_balanced_zero_congruence", "mod_eq_refl", "zero_add"),
            (*_intros("p", "z"), "right", "split",
             "have hz : p + z * 0 = p", "simp", "rewrite hz",
             *_call("multiple_implies_balanced_zero_congruence", "p", "p"), *_call("multiple_refl", "p"),
             "have hone : z * 1 = z", "simp [zero_add]", "rewrite hone", *_call("mod_eq_refl", "p", "z")),
            "The initial state (p,root,0,1) has the genuine negative/positive root-coefficient orientation.",
        ),
        spec(
            "cornacchia_initial_invariant",
            f"forall p z. ({_root('p', 'z', tag='initial_root')}) -> "
            f"({_invariant('p', 'z', 'p', 'z', '0', '1', tag='initial_invariant')})",
            ("cornacchia_prime_square_strictly_above", "cornacchia_root_coprime", "cornacchia_initial_alternating_congruences", "zero_add"),
            (*_intros("p", "z", "hr"), "have hroot : " + _root("p", "z", tag="initial_root_copy"), "exact hr",
             *_cases_and("hr", 4), "split", "exact hroot", "split", f"exact {root[1]}",
             "split", f"exact {root[2]}", "split", "intro hz", "apply PA1", "exact hz",
             "split", *_call("cornacchia_prime_square_strictly_above", "p"), f"exact {root[0]}",
             "split", "simp [zero_add]", "split", *_call("cornacchia_root_coprime", "p", "z"), "exact hroot",
             *_call("cornacchia_initial_alternating_congruences", "p", "z")),
            "A constructed root initializes all arithmetic, coprimality, sign, and threshold invariants of Cornacchia's actual state.",
        ),
        spec(
            "cornacchia_invariant_euclidean_step",
            "forall p z a r u t q s T. "
            f"({_invariant('p', 'z', 'a', 'r', 'u', 't', tag='invariant_step_old')}) -> "
            f"({_lt('p', 'r * r', tag='invariant_step_guard')}) -> a = r * q + s -> "
            f"({_lt('s', 'r', tag='invariant_step_remainder')}) -> T = q * t + u -> "
            f"({_invariant('p', 'z', 'r', 's', 't', 'T', tag='invariant_step_new')})",
            ("cornacchia_coprime_euclidean_step", "cornacchia_division_quotient_nonzero",
             "cornacchia_above_threshold_remainder_nonzero", "prime_nonzero",
             "cornacchia_coefficient_step_nonzero", "cornacchia_cross_identity_step",
             "cornacchia_alternating_congruences_step"),
            (*_intros("p", "z", "a", "r", "u", "t", "q", "s", "T", "hi", "hguard", "hdiv", "hsr", "hT"),
             *_cases_and("hi", 8),
             "have hc : " + coprime("r", "s", tag="cor_step_new_coprime"),
             *_call("cornacchia_coprime_euclidean_step", "a", "r", "q", "s"), "exact hdiv", f"exact {inv[6]}",
             "have hq : ~(q = 0)", "intro hz", *_call("cornacchia_division_quotient_nonzero", "a", "r", "q", "s"),
             "exact hdiv", f"exact {inv[2]}", "exact hsr", "exact hz",
             "split", f"exact {inv[0]}", "split", "intro hz",
             *_call("cornacchia_above_threshold_remainder_nonzero", "p", "r", "s"),
             "intro hpzero", *_call("prime_nonzero", "p"), f"cases {inv[0]}", f"exact {inv[0]}_left", "exact hpzero",
             "exact hguard", "exact hc", "exact hz",
             "split", "exact hsr", "split", "intro hz", *_call("cornacchia_coefficient_step_nonzero", "q", "t", "u", "T"),
             "exact hq", f"exact {inv[3]}", "exact hT", "exact hz", "split", "exact hguard", "split",
             *_call("cornacchia_cross_identity_step", "p", "a", "r", "u", "t", "q", "s", "T"),
             f"exact {inv[5]}", "exact hdiv", "exact hT", "split", "exact hc",
             *_call("cornacchia_alternating_congruences_step", "p", "z", "a", "r", "u", "t", "q", "s", "T"),
             "exact hdiv", "exact hT", f"exact {inv[7]}"),
            "Every actual Euclidean/coefficient transition above the stopping threshold preserves the full rooted invariant and keeps the next remainder positive.",
        ),
        spec(
            "cornacchia_invariant_stop_correct",
            "forall p z a r u t. "
            f"({_invariant('p', 'z', 'a', 'r', 'u', 't', tag='stop_invariant')}) -> "
            f"({_lt('r * r', 'p', tag='stop_guard')}) -> p = r * r + t * t",
            ("cornacchia_stopping_state_represents_prime",),
            (*_intros("p", "z", "a", "r", "u", "t", "hi", "hs"), *_cases_and("hi", 8),
             *_call("cornacchia_stopping_state_represents_prime", "p", "z", "a", "r", "u", "t"),
             *_cases_and(inv[0], 4), f"exact {_parts(inv[0], 4)[3]}",
             f"exact {inv[7]}", f"exact {inv[5]}", f"exact {inv[4]}", f"exact {inv[1]}", f"exact {inv[3]}", "exact hs"),
            "A halted state of the rooted Cornacchia invariant is an exact two-square representation, not just a divisible norm.",
        ),
        spec(
            "cornacchia_stopped_trace",
            "forall p a r u t h e. "
            f"({_state('h', 'e', '0', 'a', 'r', 'u', 't', '0', tag='stopped_state')}) -> "
            f"~(r = 0) -> ~(t = 0) -> ({_lt('r * r', 'p', tag='stopped_bound')}) -> "
            f"({_run('p', 'a', 'r', 'u', 't', 'r', 't', 'h', 'e', '0', tag='stopped_run')})",
            (),
            (*_intros("p", "a", "r", "u", "t", "h", "e", "hs", "hr", "ht", "hb"),
             "exists a", "exists u", "exists 0", "split", "exact hs", "split", "exact hs",
             "split", "exact hr", "split", "exact ht", "split", "exact hb",
             "intro i", "intro hi", "exfalso", "cases hi", "rewrite PA4 at hi_witness", "apply PA1", "exact hi_witness"),
            "A below-threshold positive state is a complete zero-transition Cornacchia run with stored terminal quotient zero.",
        ),
        spec(
            "cornacchia_stopped_trace_exists",
            "forall p a r u t. ~(r = 0) -> ~(t = 0) -> "
            f"({_lt('r * r', 'p', tag='stopped_exists_bound')}) -> exists h e. "
            f"({_run('p', 'a', 'r', 'u', 't', 'r', 't', 'h', 'e', '0', tag='stopped_exists_run')})",
            ("beta_prefix_extend", "cornacchia_stopped_trace"),
            (*_intros("p", "a", "r", "u", "t", "hr", "ht", "hb"),
             "specialize beta_prefix_extend 0", "specialize beta_prefix_extend 0", "specialize beta_prefix_extend 0",
             f"specialize beta_prefix_extend ({_packed('a', 'r', 'u', 't', '0')})",
             "cases beta_prefix_extend", "cases beta_prefix_extend_witness", "cases beta_prefix_extend_witness_witness",
             "exists x", "exists x1", *_call("cornacchia_stopped_trace", "p", "a", "r", "u", "t", "x", "x1"),
             "exact beta_prefix_extend_witness_witness_left", "exact hr", "exact ht", "exact hb"),
            "The actual stopped state can always be encoded in the established beta history without an external coding oracle.",
        ),
        spec(
            "cornacchia_trace_extend",
            "forall p a r u t q s V R T h e l. a = r * q + s -> "
            f"({_lt('s', 'r', tag='extend_remainder')}) -> V = q * t + u -> "
            f"({_lt('p', 'r * r', tag='extend_guard')}) -> "
            f"({_run('p', 'r', 's', 't', 'V', 'R', 'T', 'h', 'e', 'l', tag='extend_old')}) -> exists H E. "
            f"({_run('p', 'a', 'r', 'u', 't', 'R', 'T', 'H', 'E', 'S l', tag='extend_new')})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt", "le_succ", "succ_le_succ", "zero_add"),
            (*_intros("p", "a", "r", "u", "t", "q", "s", "V", "R", "T", "h", "e", "l", "hdiv", "hrem", "hcoef", "hguard", "ht"),
             *_cases_exists("ht", 3), *_cases_and(trace_body, 6),
             "have hext : exists H E. (" + _and(
                 _state("H", "E", "S l", "a", "r", "u", "t", "q", tag="extend_appended"),
                 _preserve("h", "e", "H", "E", "S l", tag="extend_preserve"),
             ) + ")",
             *_call("beta_prefix_extend", "(S l)", "h", "e", f"({_packed('a', 'r', 'u', 't', 'q')})"),
             "cases hext", "cases hext_witness", "cases hext_witness_witness",
             "exists x3", "exists x4", "exists x", "exists x1", "exists q", "split",
             *_call("hext_witness_witness_right", "0", f"({_packed('x', 'R', 'x1', 'T', '0')})"),
             "exists l", "simp", f"exact {trace[0]}", "split", "exact hext_witness_witness_left",
             "split", f"exact {trace[2]}", "split", f"exact {trace[3]}", "split", f"exact {trace[4]}",
             "intro i", "intro hi", "have hs : i = l \\/ " + _lt("i", "l", tag="extend_split"),
             *_call("finite_lt_succ_eq_or_lt", "l", "i"), "exact hi", "cases hs",
             *_rewrite("hs_left", 4),
             "exists a", "exists r", "exists u", "exists t", "exists q",
             "exists r", "exists s", "exists t", "exists V", "exists x2", "split", "exact hext_witness_witness_left",
             "split", *_call("hext_witness_witness_right", "l", f"({_packed('r', 's', 't', 'V', 'x2')})"),
             "exists 0", "apply zero_add", f"exact {trace[1]}",
             "split", "refl", "split", "refl", "split", "exact hdiv", "split", "exact hrem", "split", "exact hcoef", "exact hguard",
             "have hst : " + _transition("p", "h", "e", "i", tag="extend_old_step"),
             *_call(trace[5], "i"), "exact hs_right", *_cases_exists("hst", 10), *_cases_and(step_body, 3),
             *(f"exists x{i}" for i in range(5, 15)), "split",
             *_call("hext_witness_witness_right", "(S i)", f"({_packed('x5', 'x6', 'x7', 'x8', 'x9')})"),
             *_call("succ_le_succ", "(S i)", "l"), "exact hs_right", f"exact {step_parts[0]}",
             "split", *_call("hext_witness_witness_right", "i", f"({_packed('x10', 'x11', 'x12', 'x13', 'x14')})"),
             *_call("le_succ", "(S i)", "l"), "exact hs_right", f"exact {step_parts[1]}", f"exact {step_parts[2]}"),
            "A genuine above-threshold Euclidean division prepends its full remainder/coefficient/quotient state to the same stopped history, preserving every earlier encoded state and transition.",
        ),
        spec(
            "cornacchia_complete_from_invariant_up_to",
            "forall B r. " + f"({_le('r', 'B', tag='completion_bound')}) -> forall p z a u t. "
            f"({_invariant('p', 'z', 'a', 'r', 'u', 't', tag='completion_source')}) -> "
            f"({_completion('p', 'a', 'r', 'u', 't', tag='completion_result')})",
            ("le_zero", "cornacchia_prime_square_comparison", "cornacchia_stopped_trace_exists",
             "cornacchia_invariant_stop_correct", "euclidean_division_step_exists",
             "cornacchia_coefficient_step_exists", "cornacchia_invariant_euclidean_step",
             "le_of_succ_le_succ", "le_trans", "cornacchia_trace_extend"),
            ("intro B", "induction B", *_intros("r", "hb", "p", "z", "a", "u", "t", "hi"),
             "exfalso", "cases hi", "cases hi_right", "apply hi_right_left", *_call("le_zero", "r"), "exact hb",
             *_intros("r", "hb", "p", "z", "a", "u", "t", "hi"),
             "have hp : " + prime("p", tag="cor_completion_prime"), "cases hi", "cases hi_left", "exact hi_left_left",
             "have hr : ~(r = 0)", "cases hi", "cases hi_right", "exact hi_right_left",
             "have ht : ~(t = 0)", *_cases_and("hi", 8), f"exact {inv[3]}",
             "have hs : (" + _lt("r * r", "p", tag="completion_stop") + ") \\/ (" + _lt("p", "r * r", tag="completion_continue") + ")",
             *_call("cornacchia_prime_square_comparison", "p", "r"), "exact hp", "cases hs",
             "have hbase : exists h e. " + _run("p", "a", "r", "u", "t", "r", "t", "h", "e", "0", tag="completion_stopped"),
             *_call("cornacchia_stopped_trace_exists", "p", "a", "r", "u", "t"), "exact hr", "exact ht", "exact hs_left",
             "cases hbase", "cases hbase_witness", "exists r", "exists t", "exists x", "exists x1", "exists 0",
             "split", "exact hbase_witness_witness", *_call("cornacchia_invariant_stop_correct", "p", "z", "a", "r", "u", "t"), "exact hi", "exact hs_left",
             "have hdiv : exists q s. (a = r * q + s /\\ (" + _lt("s", "r", tag="completion_actual_division") + "))",
             *_call("euclidean_division_step_exists", "a", "r"), "exact hr", "cases hdiv", "cases hdiv_witness", "cases hdiv_witness_witness",
             "have hV : exists V. V = x * t + u", *_call("cornacchia_coefficient_step_exists", "x", "t", "u"), "cases hV",
             "have hnew : " + _invariant("p", "z", "r", "x1", "t", "x2", tag="completion_next_invariant"),
             *_call("cornacchia_invariant_euclidean_step", "p", "z", "a", "r", "u", "t", "x", "x1", "x2"),
             "exact hi", "exact hs_right", "exact hdiv_witness_witness_left", "exact hdiv_witness_witness_right", "exact hV_witness",
             "have hsmaller : " + _le("x1", "B", tag="completion_smaller"),
             *_call("le_of_succ_le_succ", "x1", "B"), *_call("le_trans", "(S x1)", "r", "(S B)"),
             "exact hdiv_witness_witness_right", "exact hb",
             "have hall : forall P Z A U V. (" + _invariant("P", "Z", "A", "x1", "U", "V", tag="completion_IH_invariant") + ") -> (" + _completion("P", "A", "x1", "U", "V", tag="completion_IH_result") + ")",
             *_call("IH", "x1"), "exact hsmaller",
             "have hsmall : " + _completion("p", "r", "x1", "t", "x2", tag="completion_recursive"),
             *_call("hall", "p", "z", "r", "t", "x2"), "exact hnew",
             *_cases_exists("hsmall", 5), "cases " + "hsmall" + "_witness" * 5,
             "have hext : exists H E. " + _run("p", "a", "r", "u", "t", "x3", "x4", "H", "E", "S x7", tag="completion_extended"),
             *_call("cornacchia_trace_extend", "p", "a", "r", "u", "t", "x", "x1", "x2", "x3", "x4", "x5", "x6", "x7"),
             "exact hdiv_witness_witness_left", "exact hdiv_witness_witness_right", "exact hV_witness", "exact hs_right",
             "exact " + "hsmall" + "_witness" * 5 + "_left",
             "cases hext", "cases hext_witness", "exists x3", "exists x4", "exists x8", "exists x9", "exists S x7",
             "split", "exact hext_witness_witness", "exact " + "hsmall" + "_witness" * 5 + "_right"),
            "Bounded natural induction on the positive current remainder constructs the entire first-stop history with actual quotients and coefficients and proves its final exact two-square norm.",
        ),
        spec(
            "cornacchia_complete_from_invariant",
            "forall p z a r u t. "
            f"({_invariant('p', 'z', 'a', 'r', 'u', 't', tag='total_source')}) -> "
            f"({_completion('p', 'a', 'r', 'u', 't', tag='total_result')})",
            ("cornacchia_complete_from_invariant_up_to", "le_refl"),
            (*_intros("p", "z", "a", "r", "u", "t", "hi"),
             "have hall : forall P Z A U V. (" + _invariant("P", "Z", "A", "r", "U", "V", tag="total_bounded_invariant") + ") -> (" + _completion("P", "A", "r", "U", "V", tag="total_bounded_result") + ")",
             *_call("cornacchia_complete_from_invariant_up_to", "r", "r"), *_call("le_refl", "r"),
             *_call("hall", "p", "z", "a", "u", "t"), "exact hi"),
            "Every rooted valid Cornacchia state terminates constructively at its first square-root crossing and returns its actual two-square coordinates.",
        ),
        spec(
            "cornacchia_from_any_bounded_negative_one_root",
            f"forall p z. ({_root('p', 'z', tag='root_algorithm_source')}) -> ({_root_completion('p', 'z', tag='root_algorithm_result')})",
            ("cornacchia_initial_invariant", "cornacchia_complete_from_invariant"),
            (*_intros("p", "z", "hr"), "have hc : " + _completion("p", "p", "z", "0", "1", tag="root_algorithm_complete"),
             *_call("cornacchia_complete_from_invariant", "p", "z", "p", "z", "0", "1"),
             *_call("cornacchia_initial_invariant", "p", "z"), "exact hr",
             *_cases_exists("hc", 5), "cases " + "hc" + "_witness" * 5,
             "exists x", "exists x1", "exists x2", "exists x3", "exists x4", "split", "split", "exact hr",
             "exact " + "hc" + "_witness" * 5 + "_left", "exact " + "hc" + "_witness" * 5 + "_right"),
            "Every positive bounded root of minus one at a prime produces a genuine complete Cornacchia execution and its returned exact representation; no successful trace is supplied.",
        ),
        spec(
            "cornacchia_prime_two_squares_complete",
            f"forall p. ({prime('p', tag='cor_complete_prime')}) -> (exists k. p = 4 * k + 1) -> "
            f"exists z. ({_root_completion('p', 'z', tag='prime_algorithm_result')})",
            ("cornacchia_root_exists", "cornacchia_from_any_bounded_negative_one_root"),
            (*_intros("p", "hp", "hfour"), "have hr : exists z. " + _root("p", "z", tag="prime_algorithm_root"),
             *_call("cornacchia_root_exists", "p"), "exact hp", "exact hfour", "cases hr", "exists x",
             *_call("cornacchia_from_any_bounded_negative_one_root", "p", "x"), "exact hr_witness"),
            "Full G107: every prime one modulo four yields an actual root of minus one, a complete first-stop Euclidean/coefficient/quotient history from (p,root,0,1), and exactly the two-square representation returned by that history.",
        ),
    )


__all__ = [
    "cornacchia_root", "cornacchia_alternating_congruences", "cornacchia_state_invariant",
    "cornacchia_state_at", "cornacchia_transition_at", "cornacchia_euclidean_run", "cornacchia_trace",
    "make_cornacchia_candidate_theorems",
]
