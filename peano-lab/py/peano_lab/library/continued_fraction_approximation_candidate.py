"""Unsealed exact convergents and best approximation in original HA.

Every relation is a conservative expansion. In particular a convergent will
be an actual finite quotient-matrix computation, never a record containing
the desired best-approximation conclusion. Numerators may be zero. The
arithmetic comparison lemmas also support signed approximation numerators
represented by arbitrary positive/negative natural pairs.

This authoring module alone grants no Alpha admission or closed-use authority.
"""

from __future__ import annotations

from typing import Any, Callable
import re

from ..kernel.terms import parse_term_with_names
from ..kernel.formulas import parse_formula_with_names
from .finite_fold_surface import _identifier
from .ha_generalized_crt_congruence_candidate import _checked_term
from .matrix_lattice_data_candidate import _absolute
from .fermat_residue_product_candidate import coprime


def _context(*terms: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(name for term in terms for name in parse_term_with_names(term)[1]))


def _terms(values: tuple[str, ...], variables: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(variables, tuple) or len(set(variables)) != len(variables):
        raise ValueError("continued-fraction term context must contain distinct identifiers")
    context = tuple(_identifier(name, "continued-fraction variable") for name in variables)
    return tuple(_checked_term(value, context) for value in values)


def _public_formula(source: str, variables: tuple[str, ...]) -> str:
    """Check every generated binder, including nested legacy beta binders.

    Even an unused name in the caller's declared context is protected. This
    is untrusted authoring validation only; the expanded HA formula remains
    the sole proposition supplied to the ordinary checker.
    """
    bound = {name for match in re.finditer(r"\b(?:forall|exists)\s+([^.]*)\.", source)
             for name in match.group(1).split()}
    if bound & set(variables):
        raise ValueError("generated convergent binder captures the declared variable context")
    _, free = parse_formula_with_names(source)
    if not set(free) <= set(variables):
        raise ValueError("convergent relation introduces an undeclared variable")
    return source


def _and(*parts: str) -> str:
    result = f"({parts[-1]})"
    for part in reversed(parts[:-1]):
        result = f"(({part}) /\\ {result})"
    return result


def _le(a: str, b: str, tag: str) -> str:
    name = f"cfba_bound_{_identifier(tag, 'continued-fraction bound tag')}"
    if name in _context(a, b):
        raise ValueError("continued-fraction bound captures an input variable")
    return f"exists {name}. {name} + ({a}) = ({b})"


def _lt(a: str, b: str, tag: str) -> str:
    name = f"cfba_gap_{_identifier(tag, 'continued-fraction bound tag')}"
    if name in _context(a, b):
        raise ValueError("continued-fraction bound captures an input variable")
    return f"exists {name}. {name} + S ({a}) = ({b})"


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return tuple(f"specialize {name} ({argument})" for argument in arguments) + (f"apply {name}",)


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _simp(*names: str) -> tuple[str, ...]:
    return ("simp [" + ", ".join(names) + "]",)


def _identity(a: str, b: str, u: str, U: str, v: str, V: str, E: str, F: str) -> str:
    positive = _and(f"{u} * {V} + 1 = {U} * {v}",
                    f"{a} * {v} = {b} * {u} + {E}",
                    f"{b} * {U} = {a} * {V} + {F}")
    negative = _and(f"{U} * {v} + 1 = {u} * {V}",
                    f"{b} * {u} = {a} * {v} + {E}",
                    f"{a} * {V} = {b} * {U} + {F}")
    return f"({positive}) \\/ ({negative})"


def _errors(a: str, b: str, u: str, U: str, v: str, V: str, E: str, F: str) -> str:
    return (
        f"(({a} * {v} = {b} * {u} + {E}) /\\ ({b} * {U} = {a} * {V} + {F})) \\/ "
        f"(({b} * {u} = {a} * {v} + {E}) /\\ ({a} * {V} = {b} * {U} + {F}))"
    )


def _invariant(a: str, b: str, u: str, U: str, v: str, V: str, tag: str) -> str:
    safe_tag = _identifier(tag, "convergent invariant binder tag")
    E, F = "cfba_error_" + safe_tag, "cfba_previous_error_" + safe_tag
    if {E, F} & set(_context(a, b, u, U, v, V)):
        raise ValueError("convergent invariant binder captures an input variable")
    return f"exists {E} {F}. " + _and(_identity(a, b, u, U, v, V, E, F),
                                     _lt(E, F, tag + "decrease"), _le(F, b, tag + "previous_bound"))


def _difference_coordinates(u: str, U: str, v: str, V: str, rp: str, rn: str, t: str, c: str, d: str) -> str:
    return _and(f"{rp} + {d} * {U} = {rn} + {c} * {u}", f"{t} + {d} * {V} = {c} * {v}")


def _balance(x: str, y: str, u: str, U: str, p: str, n: str, q: str, m: str) -> str:
    return f"({x}) + (({n}) * ({u}) + ({m}) * ({U})) = ({y}) + (({p}) * ({u}) + ({q}) * ({U}))"


def _signed_scalar_case(kind: str, x: str, y: str, u: str, U: str, c: str, d: str) -> str:
    return {
        "pp": f"({x}) = ({y}) + (({c}) * ({u}) + ({d}) * ({U}))",
        "pn": f"({x}) + ({d}) * ({U}) = ({y}) + ({c}) * ({u})",
        "np": f"({x}) + ({c}) * ({u}) = ({y}) + ({d}) * ({U})",
        "nn": f"({x}) + (({c}) * ({u}) + ({d}) * ({U})) = ({y})",
    }[kind]


def _basis_case(kind: str, u: str, U: str, v: str, V: str, rp: str, rn: str, t: str, c: str, d: str) -> str:
    return _and(_signed_scalar_case(kind, rp, rn, u, U, c, d),
                _signed_scalar_case(kind, t, "0", v, V, c, d))


def _small_coordinates(u: str, U: str, v: str, V: str, rp: str, rn: str, t: str, c: str, d: str) -> str:
    return _or(_and(f"~({c} = 0)", _basis_case("pn", u, U, v, V, rp, rn, t, c, d)),
               _and(f"~({d} = 0)", _basis_case("np", u, U, v, V, rp, rn, t, c, d)))


def _or(*parts: str) -> str:
    result = f"({parts[-1]})"
    for part in reversed(parts[:-1]):
        result = f"(({part}) \\/ {result})"
    return result


def rational_approximation_error_relation(
    a: str, b: str, numerator_positive: str, numerator_negative: str,
    denominator: str, error: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Actual |a*t-b*(rp-rn)|; no approximation inequality is built in."""
    _identifier(tag, "rational-error binder tag")
    a, b, rp, rn, t, error = _terms(
        (a, b, numerator_positive, numerator_negative, denominator, error), variables,
    )
    return _public_formula(_absolute(f"({a}) * ({t}) + ({b}) * ({rn})", f"({b}) * ({rp})", error), variables)


def alternating_convergent_identity_relation(
    a: str, b: str, u: str, U: str, v: str, V: str, E: str, F: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Exact adjacent determinant and alternating signed error equations."""
    _identifier(tag, "convergent-identity binder tag")
    return _public_formula(_identity(*_terms((a, b, u, U, v, V, E, F), variables)), variables)


def convergent_error_invariant_relation(
    a: str, b: str, u: str, U: str, v: str, V: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Derived determinant and errors, never the definition of Convergent."""
    return _public_formula(_invariant(*_terms((a, b, u, U, v, V), variables), tag), variables)


def make_continued_fraction_approximation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return non-admitting arithmetic bodies used by the full G072 roots."""
    return (_local_identity_rows(spec) + _recurrence_invariant_rows(spec) + _error_comparison_rows(spec)
            + _basis_coordinate_rows(spec) + _small_denominator_rows(spec) + _best_comparison_rows(spec))


def _local_identity_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    semiring = ("add_mul", "mul_add", "mul_assoc", "mul_comm", "add_assoc", "add_comm")
    determinant_rules = ("add_mul", "mul_assoc", "mul_comm", "add_comm")
    exact_value_rules = ("add_mul", "mul_add", "mul_assoc", "mul_comm", "add_comm")
    rows = [
        spec(
            "cf_approximation_prepend_determinant_forward",
            "forall u U v V q. u * V + 1 = U * v -> (q * U + V) * u + 1 = (q * u + v) * U",
            determinant_rules,
            _intro("u", "U", "v", "V", "q", "hd")
            + ("trans (q * U) * u + (u * V + 1)",)
            + _simp(*determinant_rules)
            + ("rewrite hd",) + _simp(*determinant_rules),
            "Prepending a genuine quotient matrix reverses the determinant-one orientation.",
        ),
        spec(
            "cf_approximation_prepend_determinant_backward",
            "forall u U v V q. U * v + 1 = u * V -> (q * u + v) * U + 1 = (q * U + V) * u",
            ("cf_approximation_prepend_determinant_forward",),
            _intro("u", "U", "v", "V", "q", "hd")
            + _call("cf_approximation_prepend_determinant_forward", "U", "u", "V", "v", "q")
            + ("exact hd",),
            "The reverse determinant orientation has the same actual quotient-matrix transition.",
        ),
        spec(
            "cf_approximation_prepend_error_forward",
            "forall a b q r x y e. a = b * q + r -> b * y = r * x + e -> b * (q * x + y) = a * x + e",
            semiring,
            _intro("a", "b", "q", "r", "x", "y", "e", "ha", "he")
            + ("trans b * (q * x) + b * y", "apply mul_add", "rewrite he", "rewrite ha")
            + _simp(*semiring),
            "A true Euclidean division transports one signed numerator error exactly.",
        ),
        spec(
            "cf_approximation_prepend_error_backward",
            "forall a b q r x y e. a = b * q + r -> r * x = b * y + e -> a * x = b * (q * x + y) + e",
            semiring,
            _intro("a", "b", "q", "r", "x", "y", "e", "ha", "he")
            + ("rewrite ha", "trans (b * q) * x + r * x", "apply add_mul", "rewrite he")
            + _simp(*semiring),
            "The opposite signed numerator error transports with the same nonnegative magnitude.",
        ),
        spec(
            "cf_approximation_empty_matrix_identity",
            "forall a b. (" + _identity("a", "b", "1", "0", "0", "1", "b", "a") + ")",
            ("zero_add",),
            _intro("a", "b") + ("right", "split")
            + _simp("zero_add")
            + ("split",) + _simp("zero_add")
            + _simp("zero_add"),
            "The identity matrix gives the exact two initial signed errors b and a, including zero values.",
        ),
        spec(
            "cf_approximation_prepend_identity",
            "forall a b q r u U v V E F. a = b * q + r -> ("
            + _identity("b", "r", "u", "U", "v", "V", "E", "F") + ") -> ("
            + _identity("a", "b", "(q * u + v)", "(q * U + V)", "u", "U", "E", "F") + ")",
            ("cf_approximation_prepend_determinant_forward", "cf_approximation_prepend_determinant_backward",
             "cf_approximation_prepend_error_forward", "cf_approximation_prepend_error_backward"),
            _intro("a", "b", "q", "r", "u", "U", "v", "V", "E", "F", "ha", "h")
            + ("cases h", "cases h_left", "cases h_left_right", "right", "split")
            + _call("cf_approximation_prepend_determinant_forward", "u", "U", "v", "V", "q")
            + ("exact h_left_left", "split")
            + _call("cf_approximation_prepend_error_forward", "a", "b", "q", "r", "u", "v", "E")
            + ("exact ha", "exact h_left_right_left")
            + _call("cf_approximation_prepend_error_backward", "a", "b", "q", "r", "U", "V", "F")
            + ("exact ha", "exact h_left_right_right", "cases h_right", "cases h_right_right", "left", "split")
            + _call("cf_approximation_prepend_determinant_backward", "u", "U", "v", "V", "q")
            + ("exact h_right_left", "split")
            + _call("cf_approximation_prepend_error_backward", "a", "b", "q", "r", "u", "v", "E")
            + ("exact ha", "exact h_right_right_left")
            + _call("cf_approximation_prepend_error_forward", "a", "b", "q", "r", "U", "V", "F")
            + ("exact ha", "exact h_right_right_right"),
            "A quotient prepended to both actual convergents transports both error magnitudes and the alternating determinant.",
        ),
        spec(
            "cf_approximation_unit_determinant_coprime",
            "forall u U v V. (u * V + 1 = U * v \\/ U * v + 1 = u * V) -> ("
            + coprime("u", "v", tag="cfba_determinant_coprime") + ")",
            ("balanced_bezout_one_implies_coprime", "mul_comm", "zero_add", "add_succ_left"),
            _intro("u", "U", "v", "V", "hd") + ("cases hd",)
            + _call("balanced_bezout_one_implies_coprime", "u", "v", "0", "U", "V", "0")
            + ("trans U * v",) + _simp("mul_comm", "zero_add")
            + ("trans u * V + 1", "symm", "exact hd_left") + _simp("zero_add", "add_succ_left")
            + _call("balanced_bezout_one_implies_coprime", "u", "v", "V", "0", "0", "U")
            + ("trans u * V",) + _simp("zero_add")
            + ("trans U * v + 1", "symm", "exact hd_right") + _simp("mul_comm", "zero_add", "add_succ_left"),
            "Every actual determinant-one adjacent pair has a coprime current numerator and denominator, including 0/1.",
        ),
    ]
    script = _intro("a", "b", "u", "U", "v", "V", "p", "P", "q", "Q", "E", "F", "hu", "hU", "hv", "hV", "hi")
    script += ("cases hi",)
    for side in ("left", "right"):
        source = "hi_" + side
        script += ("cases " + source, "cases " + source + "_right", side, "split")
        script += ("rewrite hu", "rewrite hU", "rewrite hv", "rewrite hV", "exact " + source + "_left", "split")
        script += ("rewrite hu", "rewrite hv", "exact " + source + "_right_left")
        script += ("rewrite hU", "rewrite hV", "exact " + source + "_right_right")
    rows.append(spec(
        "cf_approximation_identity_entry_transport",
        "forall a b u U v V p P q Q E F. u = p -> U = P -> v = q -> V = Q -> ("
        + _identity("a", "b", "p", "P", "q", "Q", "E", "F") + ") -> ("
        + _identity("a", "b", "u", "U", "v", "V", "E", "F") + ")",
        (), script,
        "Substitution along the actual recurrence equations transports the determinant/error invariant without assuming it as part of a convergent certificate.",
    ))
    rows.append(spec(
        "cf_approximation_identity_current_absolute_error",
        "forall a b u U v V E F. (" + _identity("a", "b", "u", "U", "v", "V", "E", "F")
        + ") -> (" + _absolute("a * v", "b * u", "E") + ")",
        (),
        _intro("a", "b", "u", "U", "v", "V", "E", "F", "hi")
        + ("cases hi", "cases hi_left", "cases hi_left_right", "left", "exact hi_left_right_left",
           "cases hi_right", "cases hi_right_right", "right", "exact hi_right_right_left"),
        "The invariant's current error is exactly the absolute cross-product error, including the zero terminal value.",
    ))
    rows.append(spec(
        "cf_approximation_exact_value_prepend",
        "forall a b q r p n. a = b * q + r -> b * n = r * p -> a * p = b * (q * p + n)",
        exact_value_rules,
        _intro("a", "b", "q", "r", "p", "n", "ha", "he")
        + ("rewrite ha", "trans (b * q) * p + r * p", "apply add_mul", "rewrite <- he") + _simp(*exact_value_rules),
        "A genuine Euclidean quotient transports an exact tail rational value to an exact value of the original fraction.",
    ))
    return tuple(rows)


def _recurrence_invariant_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    args = ("a", "b", "q", "r", "u", "U", "v", "V", "p", "P", "n", "N")
    recurrences = "u = q * p + n -> U = q * P + N -> v = p -> V = P -> "
    computed = ("(q * p + n)", "(q * P + N)", "p", "P")
    base = _intro(*args, "ha", "hr", "hp", "hP", "hn", "hN", "hu", "hU", "hv", "hV")
    base += ("have hi : " + _identity("b", "r", "p", "P", "n", "N", "r", "b"),)
    base += _call("cf_approximation_identity_entry_transport", "b", "r", "p", "P", "n", "N", "1", "0", "0", "1", "r", "b")
    base += ("exact hp", "exact hP", "exact hn", "exact hN")
    base += _call("cf_approximation_empty_matrix_identity", "b", "r")
    base += ("exists r", "exists b", "split")
    base += _call("cf_approximation_identity_entry_transport", "a", "b", "u", "U", "v", "V", *computed, "r", "b")
    base += ("exact hu", "exact hU", "exact hv", "exact hV")
    base += _call("cf_approximation_prepend_identity", "a", "b", "q", "r", "p", "P", "n", "N", "r", "b")
    base += ("exact ha", "exact hi", "split", "exact hr") + _call("le_refl", "b")
    step = _intro(*args, "ha", "hr", "hu", "hU", "hv", "hV", "hi")
    step += ("cases hi", "cases hi_witness", "cases hi_witness_witness", "cases hi_witness_witness_right",
             "exists x", "exists x1", "split")
    step += _call("cf_approximation_identity_entry_transport", "a", "b", "u", "U", "v", "V", *computed, "x", "x1")
    step += ("exact hu", "exact hU", "exact hv", "exact hV")
    step += _call("cf_approximation_prepend_identity", "a", "b", "q", "r", "p", "P", "n", "N", "x", "x1")
    step += ("exact ha", "exact hi_witness_witness_left", "split", "exact hi_witness_witness_right_left")
    step += _call("le_trans", "x1", "r", "b") + ("exact hi_witness_witness_right_right",)
    step += _call("lt_to_le", "r", "b") + ("exact hr",)
    return (
        spec(
            "cf_approximation_first_recurrence_error_invariant",
            "forall a b q r u U v V p P n N. a = b * q + r -> (" + _lt("r", "b", "first_remainder")
            + ") -> p = 1 -> P = 0 -> n = 0 -> N = 1 -> " + recurrences
            + "(" + _invariant("a", "b", "u", "U", "v", "V", "first_invariant") + ")",
            ("cf_approximation_identity_entry_transport", "cf_approximation_empty_matrix_identity",
             "cf_approximation_prepend_identity", "le_refl"),
            base,
            "A genuine first Euclidean quotient applied to the actual identity matrix yields errors r<b and b, including quotient zero and remainder zero.",
        ),
        spec(
            "cf_approximation_prepend_recurrence_error_invariant",
            "forall a b q r u U v V p P n N. a = b * q + r -> (" + _lt("r", "b", "prepend_remainder")
            + ") -> " + recurrences + "(" + _invariant("b", "r", "p", "P", "n", "N", "prepend_source")
            + ") -> (" + _invariant("a", "b", "u", "U", "v", "V", "prepend_result") + ")",
            ("cf_approximation_identity_entry_transport", "cf_approximation_prepend_identity", "le_trans", "lt_to_le"),
            step,
            "Actual quotient recurrence transports the derived determinant and decreasing errors while retaining the previous-error bound by the input denominator.",
        ),
        spec(
            "cf_approximation_derived_invariant_denominator_positive",
            "forall a b u U v V. (" + _invariant("a", "b", "u", "U", "v", "V", "positive_denominator") + ") -> ~(v = 0)",
            ("succ_ne_zero", "mul_eq_one_components", "mul_one", "zero_add", "lt_not_le"),
            _intro("a", "b", "u", "U", "v", "V", "hi", "hv")
            + ("cases hi", "cases hi_witness", "cases hi_witness_witness", "cases hi_witness_witness_right",
               "cases hi_witness_witness_left", "cases hi_witness_witness_left_left")
            + _call("succ_ne_zero", "u * V")
            + ("trans u * V + 1", "simp", "trans U * v", "exact hi_witness_witness_left_left_left", "rewrite hv", "simp",
               "cases hi_witness_witness_left_right", "cases hi_witness_witness_left_right_right", "have hm : u * V = 1",
               "trans U * v + 1", "symm", "exact hi_witness_witness_left_right_left", "rewrite hv", "simp",
               "have ho : u = 1 /\\ V = 1")
            + _call("mul_eq_one_components", "u", "V") + ("exact hm", "cases ho", "have he : b = x",
               "trans b * u", "rewrite ho_left", "symm", "apply mul_one",
               "trans a * v + x", "exact hi_witness_witness_left_right_right_left", "rewrite hv")
            + _simp("zero_add")
            + _call("lt_not_le", "x", "x1") + ("exact hi_witness_witness_right_left", "rewrite <- he", "exact hi_witness_witness_right_right"),
            "Every actual derived nonempty-prefix invariant forces a positive denominator; this is proved, rather than postulated to make the convergent predicate non-vacuous.",
        ),
        spec(
            "cf_approximation_derived_invariant_determinant",
            "forall a b u U v V. (" + _invariant("a", "b", "u", "U", "v", "V", "derived_determinant")
            + ") -> (u * V + 1 = U * v \\/ U * v + 1 = u * V)",
            (),
            _intro("a", "b", "u", "U", "v", "V", "hi")
            + ("cases hi", "cases hi_witness", "cases hi_witness_witness", "cases hi_witness_witness_left",
               "cases hi_witness_witness_left_left", "left", "exact hi_witness_witness_left_left_left",
               "cases hi_witness_witness_left_right", "right", "exact hi_witness_witness_left_right_left"),
            "The determinant-one equation is a proved consequence of the actual-prefix invariant, not a field assumed by the computation relation.",
        ),
    )


def _error_comparison_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    semiring = ("add_mul", "mul_add", "mul_assoc", "mul_comm", "add_assoc", "add_comm",
                "four_square_add_swap_right_tail")
    error_rules = tuple(name for name in semiring if name not in ("add_mul", "mul_assoc"))
    balance_rules = tuple(name for name in semiring if name != "add_mul")
    P = "c * (a * v) + d * (b * U)"
    N = "c * (b * u) + d * (a * V)"
    hp = "a * t + b * rn"
    hn = "b * rp"
    errors = _errors("a", "b", "u", "U", "v", "V", "E", "F")
    coordinates = _difference_coordinates("u", "U", "v", "V", "rp", "rn", "t", "c", "d")
    return (
        spec(
            "cf_approximation_opposite_errors_linear_absolute",
            "forall a b u U v V E F c d. (" + errors + ") -> ("
            + _absolute(P, N, "c * E + d * F") + ")",
            error_rules,
            _intro("a", "b", "u", "U", "v", "V", "E", "F", "c", "d", "h")
            + ("cases h", "cases h_left", "left", "rewrite h_left_left", "rewrite h_left_right")
            + _simp(*error_rules)
            + ("cases h_right", "right", "rewrite h_right_left", "rewrite h_right_right")
            + _simp(*error_rules),
            "Opposite signed errors combine without cancellation after subtracting the previous coefficient vector.",
        ),
        spec(
            "cf_approximation_subtract_previous_error_balance",
            "forall a b u U v V rp rn t c d. (" + coordinates + ") -> "
            + f"({hp}) + ({N}) = ({P}) + ({hn})",
            balance_rules,
            _intro("a", "b", "u", "U", "v", "V", "rp", "rn", "t", "c", "d", "h")
            + ("cases h", "trans a * (t + d * V) + b * (rn + c * u)")
            + _simp(*balance_rules)
            + ("rewrite h_right", "rewrite <- h_left") + _simp(*balance_rules),
            "Actual numerator and denominator coordinate equations transport the represented rational error exactly.",
        ),
        spec(
            "cf_approximation_subtract_previous_absolute_error",
            "forall a b u U v V E F rp rn t c d. (" + errors + ") -> ("
            + coordinates + ") -> (" + _absolute(hp, hn, "c * E + d * F") + ")",
            ("cf_approximation_opposite_errors_linear_absolute", "cf_approximation_subtract_previous_error_balance",
             "matrix_lattice_absolute_difference_integer_transport"),
            _intro("a", "b", "u", "U", "v", "V", "E", "F", "rp", "rn", "t", "c", "d", "he", "hc")
            + (f"have hb : ({hp}) + ({N}) = ({P}) + ({hn})",)
            + _call("cf_approximation_subtract_previous_error_balance", "a", "b", "u", "U", "v", "V", "rp", "rn", "t", "c", "d")
            + ("exact hc",)
            + _call("matrix_lattice_absolute_difference_integer_transport", P, N, hp, hn, "c * E + d * F")
            + ("symm", "exact hb")
            + _call("cf_approximation_opposite_errors_linear_absolute", "a", "b", "u", "U", "v", "V", "E", "F", "c", "d")
            + ("exact he",),
            "The actual absolute error of a signed numerator difference is the nonnegative sum of the two error contributions.",
        ),
    )


def _basis_coordinate_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    semiring = ("add_mul", "mul_add", "mul_assoc", "mul_comm", "add_assoc", "add_comm",
                "four_square_add_swap_right_tail", "natural_mul_swap_right_tail")
    scalar_rules = ("add_mul", "add_assoc", "add_comm", "four_square_add_swap_right_tail")
    rows = []
    for kind in ("pp", "pn", "np", "nn"):
        pbase = "n" if kind[0] == "p" else "p"
        qbase = "m" if kind[1] == "p" else "q"
        hp = "p = n + c" if kind[0] == "p" else "n = p + c"
        hq = "q = m + d" if kind[1] == "p" else "m = q + d"
        target = _signed_scalar_case(kind, "x", "y", "u", "U", "c", "d")
        left, right = target.split(" = ")
        base = f"{pbase} * u + {qbase} * U"
        rows.append(spec(
            "cf_approximation_signed_coordinates_" + kind,
            "forall x y u U p n q m c d. (" + _balance("x", "y", "u", "U", "p", "n", "q", "m")
            + ") -> " + hp + " -> " + hq + " -> " + target,
            ("add_right_cancel",) + scalar_rules,
            _intro("x", "y", "u", "U", "p", "n", "q", "m", "c", "d", "h", "hp", "hq")
            + _call("add_right_cancel", left, right, base)
            + ("trans x + (n * u + m * U)",)
            + tuple("rewrite " + hname for sign, hname in zip(kind, ("hp", "hq")) if sign == "n")
            + _simp(*scalar_rules)
            + ("trans y + (p * u + q * U)", "exact h")
            + tuple("rewrite " + hname for sign, hname in zip(kind, ("hp", "hq")) if sign == "p")
            + _simp(*scalar_rules),
            "Cancelling the common nonnegative coordinate representatives yields the actual " + kind + " signed linear combination.",
        ))
    p, n, q, m = "V * rp", "V * rn + U * t", "u * t + v * rn", "v * rp"
    numeric_semiring = semiring + ("add_succ_left", "mul_one", "one_mul", "zero_add")
    numerator_rules = tuple(name for name in numeric_semiring if name not in ("mul_add", "add_succ_left", "mul_one", "one_mul", "zero_add"))
    denominator_rules = tuple(name for name in numeric_semiring if name not in ("add_succ_left", "mul_one", "one_mul"))
    rows.extend((
        spec(
            "cf_approximation_cofactor_numerator_balance",
            "forall u U v V rp rn t. U * v + 1 = u * V -> "
            + _balance("rp", "rn", "u", "U", p, n, q, m),
            numerator_rules,
            _intro("u", "U", "v", "V", "rp", "rn", "t", "hd")
            + ("trans (u * V) * rn + ((U * v + 1) * rp + (u * U) * t)",) + _simp(*numerator_rules)
            + ("trans (U * v + 1) * rn + ((u * V) * rp + (u * U) * t)", "rewrite hd", "rewrite hd", "refl")
            + _simp(*numerator_rules),
            "The determinant-one cofactor formula reconstructs every actual signed numerator, not merely positive vectors.",
        ),
        spec(
            "cf_approximation_cofactor_denominator_balance",
            "forall u U v V rp rn t. U * v + 1 = u * V -> "
            + _balance("t", "0", "v", "V", p, n, q, m),
            denominator_rules,
            _intro("u", "U", "v", "V", "rp", "rn", "t", "hd")
            + ("trans (U * v + 1) * t + (v * V) * (rn + rp)",) + _simp(*denominator_rules)
            + ("rewrite hd",) + _simp(*denominator_rules),
            "The same cofactor coefficients reconstruct the denominator in the exact determinant-one basis.",
        ),
    ))
    cases = _or(*(_basis_case(kind, "u", "U", "v", "V", "rp", "rn", "t", "c", "d")
                  for kind in ("pp", "pn", "np", "nn")))
    script = _intro("u", "U", "v", "V", "rp", "rn", "t", "p", "n", "q", "m", "hnumerator", "hdenominator")
    script += ("have hp : exists c. (" + _absolute("p", "n", "c") + ")",)
    script += _call("matrix_lattice_absolute_difference_exists", "p", "n")
    script += ("cases hp", "have hq : exists d. (" + _absolute("q", "m", "d") + ")")
    script += _call("matrix_lattice_absolute_difference_exists", "q", "m")
    script += ("cases hq", "exists x", "exists x1", "cases hp_witness")
    for first in ("p", "n"):
        first_h = "hp_witness_left" if first == "p" else "hp_witness_right"
        script += ("cases hq_witness",)
        for second in ("p", "n"):
            kind = first + second
            second_h = "hq_witness_left" if second == "p" else "hq_witness_right"
            script += {"pp": ("left",), "pn": ("right", "left"),
                       "np": ("right", "right", "left"), "nn": ("right", "right", "right")}[kind]
            script += ("split",)
            for x, y, first_coordinate, second_coordinate, hypothesis in (
                ("rp", "rn", "u", "U", "hnumerator"), ("t", "0", "v", "V", "hdenominator"),
            ):
                script += _call("cf_approximation_signed_coordinates_" + kind,
                                x, y, first_coordinate, second_coordinate, "p", "n", "q", "m", "x", "x1")
                script += ("exact " + hypothesis, "exact " + first_h, "exact " + second_h)
    rows.append(spec(
        "cf_approximation_signed_basis_normalization",
        "forall u U v V rp rn t p n q m. (" + _balance("rp", "rn", "u", "U", "p", "n", "q", "m")
        + ") -> (" + _balance("t", "0", "v", "V", "p", "n", "q", "m")
        + ") -> exists c d. " + cases,
        ("matrix_lattice_absolute_difference_exists",)
        + tuple("cf_approximation_signed_coordinates_" + kind for kind in ("pp", "pn", "np", "nn")),
        script,
        "Normalizing two actual signed cofactor coefficients gives all four signed coordinate cases constructively.",
    ))
    rows.append(spec(
        "cf_approximation_determinant_one_signed_basis",
        "forall u U v V rp rn t. U * v + 1 = u * V -> exists c d. " + cases,
        ("cf_approximation_cofactor_numerator_balance", "cf_approximation_cofactor_denominator_balance",
         "cf_approximation_signed_basis_normalization"),
        _intro("u", "U", "v", "V", "rp", "rn", "t", "hd")
        + _call("cf_approximation_signed_basis_normalization", "u", "U", "v", "V", "rp", "rn", "t", p, n, q, m)
        + _call("cf_approximation_cofactor_numerator_balance", "u", "U", "v", "V", "rp", "rn", "t")
        + ("exact hd",)
        + _call("cf_approximation_cofactor_denominator_balance", "u", "U", "v", "V", "rp", "rn", "t")
        + ("exact hd",),
        "Every signed candidate numerator and natural denominator have actual integral coordinates in a determinant-one adjacent basis.",
    ))
    rows.append(spec(
        "cf_approximation_balance_exchange_columns",
        "forall x y u U p n q m. (" + _balance("x", "y", "u", "U", "p", "n", "q", "m")
        + ") -> (" + _balance("x", "y", "U", "u", "q", "m", "p", "n") + ")",
        ("add_comm",),
        _intro("x", "y", "u", "U", "p", "n", "q", "m", "h")
        + ("trans x + (n * u + m * U)",) + _simp("add_comm")
        + ("trans y + (p * u + q * U)", "exact h") + _simp("add_comm"),
        "Exchanging the two genuine basis columns exchanges their coefficients and preserves the represented integer.",
    ))
    reverse_script = _intro("u", "U", "v", "V", "rp", "rn", "t", "hd")
    reverse_script += _call("cf_approximation_signed_basis_normalization", "u", "U", "v", "V", "rp", "rn", "t",
                            "U * t + V * rn", "V * rp", "v * rp", "v * rn + u * t")
    for x, y, first, second, lemma in (
        ("rp", "rn", "U", "u", "cf_approximation_cofactor_numerator_balance"),
        ("t", "0", "V", "v", "cf_approximation_cofactor_denominator_balance"),
    ):
        reverse_script += _call("cf_approximation_balance_exchange_columns", x, y, first, second,
                                "v * rp", "v * rn + u * t", "U * t + V * rn", "V * rp")
        reverse_script += _call(lemma, "U", "u", "V", "v", "rp", "rn", "t") + ("exact hd",)
    rows.append(spec(
        "cf_approximation_determinant_minus_one_signed_basis",
        "forall u U v V rp rn t. u * V + 1 = U * v -> exists c d. " + cases,
        ("cf_approximation_cofactor_numerator_balance", "cf_approximation_cofactor_denominator_balance",
         "cf_approximation_balance_exchange_columns", "cf_approximation_signed_basis_normalization"),
        reverse_script,
        "The opposite unimodular orientation gives the same complete four-case signed basis decomposition.",
    ))
    rows.append(spec(
        "cf_approximation_unimodular_signed_basis",
        "forall u U v V rp rn t. (u * V + 1 = U * v \\/ U * v + 1 = u * V) -> exists c d. " + cases,
        ("cf_approximation_determinant_one_signed_basis", "cf_approximation_determinant_minus_one_signed_basis"),
        _intro("u", "U", "v", "V", "rp", "rn", "t", "hd") + ("cases hd",)
        + _call("cf_approximation_determinant_minus_one_signed_basis", "u", "U", "v", "V", "rp", "rn", "t")
        + ("exact hd_left",)
        + _call("cf_approximation_determinant_one_signed_basis", "u", "U", "v", "V", "rp", "rn", "t")
        + ("exact hd_right",),
        "Both determinant orientations represent every signed numerator and every natural denominator with actual integer coefficients.",
    ))
    return tuple(rows)


def _small_denominator_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    common = ("u", "U", "v", "V", "rp", "rn", "t")
    four_cases = _or(*(_basis_case(kind, *common, "c", "d") for kind in ("pp", "pn", "np", "nn")))
    small = _small_coordinates(*common, "c", "d")
    rows = [
        spec(
            "cf_approximation_positive_coefficient_bound",
            "forall E F c d. ~(c = 0) -> (" + _le("E", "c * E + d * F", "positive_coefficient") + ")",
            ("one_le_of_ne_zero", "le_mul_of_one_le_left", "le_add_right", "le_trans"),
            _intro("E", "F", "c", "d", "hc")
            + _call("le_trans", "E", "c * E", "c * E + d * F")
            + _call("le_mul_of_one_le_left", "c", "E")
            + _call("one_le_of_ne_zero", "c") + ("exact hc",)
            + _call("le_add_right", "c * E", "d * F"),
            "A positive coefficient makes the nonnegative error contribution at least the current error, including error zero.",
        ),
        spec(
            "cf_approximation_small_positive_sum_current_zero",
            "forall t v V c d. t = 0 + (c * v + d * V) -> ("
            + _lt("t", "v", "small_positive_sum") + ") -> c = 0",
            ("eq_decidable", "cf_approximation_positive_coefficient_bound", "le_trans", "lt_not_le", "zero_add"),
            _intro("t", "v", "V", "c", "d", "ht", "hlt")
            + ("have hc : c = 0 \\/ ~(c = 0)",) + _call("eq_decidable", "c", "0")
            + ("cases hc", "exact hc_left", "exfalso")
            + _call("lt_not_le", "t", "v") + ("exact hlt",)
            + _call("le_trans", "v", "c * v + d * V", "t")
            + _call("cf_approximation_positive_coefficient_bound", "v", "V", "c", "d") + ("exact hc_right",)
            + ("exists 0", "trans c * v + d * V", "apply zero_add", "symm", "trans 0 + (c * v + d * V)", "exact ht", "apply zero_add"),
            "A nonnegative combination with denominator below the current denominator has zero current coefficient.",
        ),
        spec(
            "cf_approximation_positive_difference_coefficient_nonzero",
            "forall t v V c d. ~(t = 0) -> t + d * V = 0 + c * v -> ~(c = 0)",
            ("add_eq_zero_left", "mul_zero_left"),
            _intro("t", "v", "V", "c", "d", "ht", "h", "hc") + ("apply ht",)
            + _call("add_eq_zero_left", "t", "d * V")
            + ("trans 0 + c * v", "exact h", "rewrite hc") + _simp("mul_zero_left"),
            "A strictly positive denominator in a difference of two nonnegative columns has a nonzero positive coefficient.",
        ),
        spec(
            "cf_approximation_zero_current_sum_as_difference",
            "forall u U v V rp rn t c d. (" + _basis_case("pp", *common, "c", "d")
            + ") -> c = 0 -> (" + _basis_case("np", *common, "0", "d") + ")",
            ("mul_zero_left", "zero_add"),
            _intro(*common, "c", "d", "h", "hc") + ("cases h", "split", "trans rp")
            + _simp("mul_zero_left")
            + ("trans rn + (c * u + d * U)", "exact h_left", "rewrite hc") + _simp("mul_zero_left", "zero_add")
            + ("trans t",) + _simp("mul_zero_left")
            + ("trans 0 + (c * v + d * V)", "exact h_right", "rewrite hc") + _simp("mul_zero_left", "zero_add"),
            "The only small-denominator nonnegative combination is an actual previous-column difference with zero current coefficient.",
        ),
    ]
    script = _intro(*common, "hd", "ht", "hlt")
    script += ("have hb : exists c d. " + four_cases,)
    script += _call("cf_approximation_unimodular_signed_basis", *common) + ("exact hd",)
    script += ("cases hb", "cases hb_witness", "cases hb_witness_witness", "cases hb_witness_witness_left")
    script += ("have hc : x = 0",)
    script += _call("cf_approximation_small_positive_sum_current_zero", "t", "v", "V", "x", "x1")
    script += ("exact hb_witness_witness_left_right", "exact hlt")
    script += ("have hn : " + _basis_case("np", *common, "0", "x1"),)
    script += _call("cf_approximation_zero_current_sum_as_difference", *common, "x", "x1")
    script += ("exact hb_witness_witness_left", "exact hc", "cases hn", "exists 0", "exists x1", "right", "split", "intro hzero")
    script += _call("cf_approximation_positive_difference_coefficient_nonzero", "t", "V", "v", "x1", "0")
    script += ("exact ht", "exact hn_right", "exact hzero", "exact hn", "cases hb_witness_witness_right")
    for kind, branch in (("pn", "hb_witness_witness_right_left"), ("np", "hb_witness_witness_right_right_left")):
        if kind == "np":
            script += ("cases hb_witness_witness_right_right",)
        script += ("cases " + branch, "exists x", "exists x1", "left" if kind == "pn" else "right", "split", "intro hzero")
        script += _call("cf_approximation_positive_difference_coefficient_nonzero", "t",
                        "v" if kind == "pn" else "V", "V" if kind == "pn" else "v",
                        "x" if kind == "pn" else "x1", "x1" if kind == "pn" else "x")
        script += ("exact ht", "exact " + branch + "_right", "exact hzero", "exact " + branch)
    script += ("cases hb_witness_witness_right_right_right", "exfalso", "apply ht")
    script += _call("add_eq_zero_left", "t", "x * v + x1 * V") + ("exact hb_witness_witness_right_right_right_right",)
    rows.append(spec(
        "cf_approximation_small_denominator_signed_coordinates",
        "forall u U v V rp rn t. (u * V + 1 = U * v \\/ U * v + 1 = u * V) -> ~(t = 0) -> ("
        + _lt("t", "v", "small_denominator") + ") -> exists c d. " + small,
        ("cf_approximation_unimodular_signed_basis", "cf_approximation_small_positive_sum_current_zero",
         "cf_approximation_positive_difference_coefficient_nonzero", "cf_approximation_zero_current_sum_as_difference", "add_eq_zero_left"),
        script,
        "Every candidate with positive denominator below the current one lies in one of the two opposite-sign coordinate sectors; no sign case is omitted.",
    ))
    return tuple(rows)


def _best_comparison_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    errors = _errors("a", "b", "u", "U", "v", "V", "E", "F")
    basis = _basis_case("pn", "u", "U", "v", "V", "rp", "rn", "t", "c", "d")
    hp, hn = "a * t + b * rn", "b * rp"
    arguments = ("a", "b", "u", "U", "v", "V", "E", "F", "rp", "rn", "t", "D")
    comparison = (
        "forall a b u U v V E F rp rn t D. (u * V + 1 = U * v \\/ U * v + 1 = u * V) -> ("
        + errors + ") -> (" + _le("E", "F", "comparison_errors") + ") -> ~(t = 0) -> ("
        + _lt("t", "v", "comparison_denominator") + ") -> (" + _absolute(hp, hn, "D") + ") -> ("
        + _le("E", "D", "comparison_result") + ")"
    )
    script = _intro(*arguments, "hd", "he", "hEF", "ht", "hlt", "herror")
    script += ("have hc : exists c d. " + _small_coordinates("u", "U", "v", "V", "rp", "rn", "t", "c", "d"),)
    script += _call("cf_approximation_small_denominator_signed_coordinates", "u", "U", "v", "V", "rp", "rn", "t")
    script += ("exact hd", "exact ht", "exact hlt", "cases hc", "cases hc_witness", "cases hc_witness_witness", "cases hc_witness_witness_left")
    script += _call("cf_approximation_subtractive_error_lower_bound", *arguments, "x", "x1")
    script += ("exact he", "exact hc_witness_witness_left_right", "exact hc_witness_witness_left_left", "exact herror", "cases hc_witness_witness_right")
    script += _call("le_trans", "E", "F", "D") + ("exact hEF",)
    script += _call("cf_approximation_subtractive_error_lower_bound", "a", "b", "U", "u", "V", "v", "F", "E", "rp", "rn", "t", "D", "x1", "x")
    script += _call("cf_approximation_errors_exchange_columns", "a", "b", "u", "U", "v", "V", "E", "F")
    script += ("exact he", "exact hc_witness_witness_right_right", "exact hc_witness_witness_right_left", "exact herror")
    identity_script = _intro(*arguments, "hi", "hEF", "ht", "hlt", "herror") + ("cases hi",)
    for side in ("left", "right"):
        branch = "hi_" + side
        identity_script += ("cases " + branch, "cases " + branch + "_right")
        identity_script += _call("cf_approximation_unimodular_best_approximation", *arguments)
        identity_script += (side, "exact " + branch + "_left", side, "exact " + branch + "_right",
                            "exact hEF", "exact ht", "exact hlt", "exact herror")
    rows = [
        spec(
            "cf_approximation_errors_exchange_columns",
            "forall a b u U v V E F. (" + errors + ") -> (" + _errors("a", "b", "U", "u", "V", "v", "F", "E") + ")",
            (),
            _intro("a", "b", "u", "U", "v", "V", "E", "F", "h")
            + ("cases h", "cases h_left", "right", "split", "exact h_left_right", "exact h_left_left",
               "cases h_right", "left", "split", "exact h_right_right", "exact h_right_left"),
            "Exchanging adjacent vectors exchanges their actual error magnitudes and reverses their signs.",
        ),
        spec(
            "cf_approximation_subtractive_error_lower_bound",
            "forall a b u U v V E F rp rn t D c d. (" + errors + ") -> (" + basis
            + ") -> ~(c = 0) -> (" + _absolute(hp, hn, "D") + ") -> (" + _le("E", "D", "subtractive_bound") + ")",
            ("cf_approximation_subtract_previous_absolute_error", "matrix_lattice_absolute_difference_functional",
             "cf_approximation_positive_coefficient_bound", "zero_add"),
            _intro(*arguments, "c", "d", "he", "hc", "hcpositive", "herror")
            + ("cases hc", "have hm : " + _absolute(hp, hn, "c * E + d * F"),)
            + _call("cf_approximation_subtract_previous_absolute_error", "a", "b", "u", "U", "v", "V", "E", "F", "rp", "rn", "t", "c", "d")
            + ("exact he", "split", "exact hc_left", "trans 0 + c * v", "exact hc_right", "apply zero_add",
               "have hD : D = c * E + d * F")
            + _call("matrix_lattice_absolute_difference_functional", hp, hn, "D", "c * E + d * F")
            + ("exact herror", "exact hm", "rewrite hD")
            + _call("cf_approximation_positive_coefficient_bound", "E", "F", "c", "d") + ("exact hcpositive",),
            "In either subtractive sector, a nonzero current coefficient gives the sharp lower bound for the actual absolute error.",
        ),
        spec(
            "cf_approximation_unimodular_best_approximation",
            comparison,
            ("cf_approximation_small_denominator_signed_coordinates", "cf_approximation_subtractive_error_lower_bound",
             "cf_approximation_errors_exchange_columns", "le_trans"),
            script,
            "Complete signed-numerator comparison from a genuine unimodular pair and its opposite decreasing errors; these premises still need the actual continued-fraction alignment theorem.",
        ),
        spec(
            "cf_approximation_alternating_identity_best_approximation",
            "forall a b u U v V E F rp rn t D. (" + _identity("a", "b", "u", "U", "v", "V", "E", "F")
            + ") -> (" + _le("E", "F", "identity_comparison_errors") + ") -> ~(t = 0) -> ("
            + _lt("t", "v", "identity_comparison_denominator") + ") -> (" + _absolute(hp, hn, "D") + ") -> ("
            + _le("E", "D", "identity_comparison_result") + ")",
            ("cf_approximation_unimodular_best_approximation",),
            identity_script,
            "The actual determinant and signed-error invariant implies the full comparison with every smaller positive denominator, including signed candidate numerators and exact terminal error zero.",
        ),
    ]
    rows.append(spec(
        "cf_approximation_derived_invariant_best_signed",
        "forall a b u U v V rp rn t C D. (" + _invariant("a", "b", "u", "U", "v", "V", "derived_comparison")
        + ") -> ~(t = 0) -> (" + _lt("t", "v", "derived_comparison_denominator") + ") -> ("
        + _absolute("a * v", "b * u", "C") + ") -> (" + _absolute(hp, hn, "D") + ") -> ("
        + _le("C", "D", "derived_comparison_result") + ")",
        ("matrix_lattice_absolute_difference_functional", "cf_approximation_identity_current_absolute_error",
         "cf_approximation_alternating_identity_best_approximation", "lt_to_le"),
        _intro("a", "b", "u", "U", "v", "V", "rp", "rn", "t", "C", "D", "hi", "ht", "hlt", "hc", "hd")
        + ("cases hi", "cases hi_witness", "cases hi_witness_witness", "cases hi_witness_witness_right", "have heq : C = x")
        + _call("matrix_lattice_absolute_difference_functional", "a * v", "b * u", "C", "x")
        + ("exact hc",) + _call("cf_approximation_identity_current_absolute_error", "a", "b", "u", "U", "v", "V", "x", "x1")
        + ("exact hi_witness_witness_left", "rewrite heq")
        + _call("cf_approximation_alternating_identity_best_approximation", "a", "b", "u", "U", "v", "V", "x", "x1", "rp", "rn", "t", "D")
        + ("exact hi_witness_witness_left",) + _call("lt_to_le", "x", "x1")
        + ("exact hi_witness_witness_right_left", "exact ht", "exact hlt", "exact hd"),
        "The derived invariant compares the actual, uniquely determined convergent error with every signed candidate's actual error.",
    ))
    rows.append(spec(
        "cf_approximation_natural_error_as_signed",
        "forall a b r t D. (" + _absolute("a * t", "b * r", "D") + ") -> ("
        + _absolute("a * t + b * 0", "b * r", "D") + ")",
        (),
        _intro("a", "b", "r", "t", "D", "h")
        + ("cases h", "left", "trans a * t", "simp", "exact h_left", "right", "trans a * t + D", "exact h_right", "simp"),
        "Every natural numerator, including zero, is an actual signed numerator with negative component zero.",
    ))
    return tuple(rows)


__all__ = [
    "rational_approximation_error_relation", "alternating_convergent_identity_relation",
    "convergent_error_invariant_relation",
    "make_continued_fraction_approximation_candidate_theorems",
]
