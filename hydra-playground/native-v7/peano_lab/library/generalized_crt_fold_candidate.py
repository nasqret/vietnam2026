"""Constructive finite congruence folds over genuinely decoded beta lists.

The immutable public binary CRT proves compatibility for two arbitrary natural
moduli.  This module extends the executable surface to *arbitrary finite lists*
of positive, pairwise coprime moduli and identifies their product as the
canonical list lcm.  Every definition is only a hygienic expansion into the
unchanged first-order Heyting-arithmetic language.

Pairwise compatibility for arbitrary noncoprime lists is a stronger statement:
lifting individual gcd-compatibilities through an accumulated lcm requires a
gcd/lcm distributivity lemma not provided by the existing checked library.
Nothing here silently assumes that missing implication or declares G011 closed.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_primorial_choose_interval_candidate import (
    _pairwise_coprime_prefix_term,
)
from .fermat_residue_product_candidate import coprime, pointwise_coprime
from .finite_fold_surface import _beta_at_term, _identifier, _lt, product_relation
from .ha_generalized_crt_congruence_candidate import balanced_mod_eq
from .ha_relational_lcm_candidate import is_lcm


class GeneralizedCRTFoldError(ValueError):
    """An authoring relation would leave the conservative first-order language."""


def _arguments(*values: tuple[str, str]) -> tuple[str, ...]:
    try:
        arguments = tuple(_identifier(value, label) for value, label in values)
        if len(set(arguments)) != len(arguments):
            raise ValueError("finite CRT arguments must be distinct identifiers")
        if any(
            item.startswith(("gcrt_", "ff_", "frp_", "bpr_", "hgcrt_", "hlcm_"))
            for item in arguments
        ):
            raise ValueError("generated finite CRT binder captures an argument")
        return arguments
    except ValueError as error:
        raise GeneralizedCRTFoldError(str(error)) from error


def _safe(tag: str) -> str:
    try:
        return _identifier(tag, "finite CRT binder tag")
    except ValueError as error:
        raise GeneralizedCRTFoldError(str(error)) from error


def _fresh(tag: str, context: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    safe = _safe(tag)
    result = tuple(f"gcrt_{role}_{safe}" for role in roles)
    if len(set(result)) != len(result) or set(result) & set(context):
        raise GeneralizedCRTFoldError("generated finite CRT binder captures an argument")
    return result


def _at(code: str, scale: str, index: str, value: str, *, tag: str, context: tuple[str, ...]) -> str:
    return _beta_at_term(code, scale, index, value, tag=f"gcrt_{_safe(tag)}", avoid=context)


def _bound(index: str, length: str, *, tag: str, context: tuple[str, ...]) -> str:
    return _lt(index, length, tag=f"gcrt_{_safe(tag)}", avoid=context)


def _mod(modulus: str, left: str, right: str, *, tag: str, context: tuple[str, ...]) -> str:
    return balanced_mod_eq(modulus, left, right, tag=f"gcrt_{_safe(tag)}", variables=context)


def _positive_terms(code: str, scale: str, length: str, *, tag: str, context: tuple[str, ...]) -> str:
    index, value = _fresh(tag, context, "positive_index", "positive_value")
    local = context + (index, value)
    bound = _bound(index, length, tag=f"{tag}_bound", context=local)
    entry = _at(code, scale, index, value, tag=f"{tag}_entry", context=local)
    return f"forall {index} {value}. ({bound}) -> ({entry}) -> ~({value} = 0)"


def crt_positive_moduli_prefix(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand the assertion that every actually decoded modulus is nonzero."""

    arguments = _arguments((code, "modulus code"), (scale, "modulus scale"), (length, "prefix length"))
    return _positive_terms(*arguments, tag=_safe(tag), context=arguments)


def crt_pairwise_coprime_prefix(code: str, scale: str, length: str, *, tag: str) -> str:
    """Reuse the already reviewed, exact beta-coded pairwise-coprime relation."""

    arguments = _arguments((code, "modulus code"), (scale, "modulus scale"), (length, "prefix length"))
    return _pairwise_coprime_prefix_term(*arguments, tag=f"gcrt_{_safe(tag)}", variables=arguments)


def _pairwise_terms(code: str, scale: str, length: str, *, tag: str, context: tuple[str, ...]) -> str:
    return _pairwise_coprime_prefix_term(code, scale, length, tag=f"gcrt_{_safe(tag)}", variables=context)


def _solution_terms(
    residue_code: str,
    residue_scale: str,
    modulus_code: str,
    modulus_scale: str,
    length: str,
    value: str,
    *,
    tag: str,
    context: tuple[str, ...],
) -> str:
    index, residue, modulus = _fresh(tag, context, "solution_index", "solution_residue", "solution_modulus")
    local = context + (index, residue, modulus)
    bound = _bound(index, length, tag=f"{tag}_bound", context=local)
    residue_entry = _at(residue_code, residue_scale, index, residue, tag=f"{tag}_residue", context=local)
    modulus_entry = _at(modulus_code, modulus_scale, index, modulus, tag=f"{tag}_modulus", context=local)
    congruence = _mod(modulus, value, residue, tag=f"{tag}_congruence", context=local)
    return (
        f"forall {index} {residue} {modulus}. ({bound}) -> ({residue_entry}) -> "
        f"({modulus_entry}) -> ({congruence})"
    )


def crt_prefix_solution(
    residue_code: str,
    residue_scale: str,
    modulus_code: str,
    modulus_scale: str,
    length: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand simultaneous congruence at every actual finite-list position."""

    arguments = _arguments(
        (residue_code, "residue code"), (residue_scale, "residue scale"),
        (modulus_code, "modulus code"), (modulus_scale, "modulus scale"),
        (length, "prefix length"), (value, "simultaneous solution"),
    )
    return _solution_terms(*arguments, tag=_safe(tag), context=arguments)


def _common_terms(code: str, scale: str, length: str, multiple: str, *, tag: str, context: tuple[str, ...]) -> str:
    index, modulus, quotient = _fresh(tag, context, "common_index", "common_modulus", "common_quotient")
    local = context + (index, modulus, quotient)
    bound = _bound(index, length, tag=f"{tag}_bound", context=local)
    entry = _at(code, scale, index, modulus, tag=f"{tag}_entry", context=local)
    return f"forall {index} {modulus}. ({bound}) -> ({entry}) -> exists {quotient}. {multiple} = {modulus} * {quotient}"


def _lcm_terms(code: str, scale: str, length: str, modulus: str, *, tag: str, context: tuple[str, ...]) -> str:
    common, quotient = _fresh(tag, context, "lcm_common", "lcm_quotient")
    own = _common_terms(code, scale, length, modulus, tag=f"{tag}_own", context=context)
    other = _common_terms(code, scale, length, common, tag=f"{tag}_other", context=context + (common, quotient))
    return f"(({own}) /\\ forall {common}. ({other}) -> exists {quotient}. {common} = {modulus} * {quotient})"


def crt_prefix_lcm(code: str, scale: str, length: str, modulus: str, *, tag: str) -> str:
    """Expand the exact universal-property lcm of all decoded finite moduli."""

    arguments = _arguments(
        (code, "modulus code"), (scale, "modulus scale"),
        (length, "prefix length"), (modulus, "list lcm"),
    )
    return _lcm_terms(*arguments, tag=_safe(tag), context=arguments)


def _canonical_terms(
    residue_code: str,
    residue_scale: str,
    modulus_code: str,
    modulus_scale: str,
    length: str,
    value: str,
    modulus: str,
    *,
    tag: str,
    context: tuple[str, ...],
) -> str:
    least = _lcm_terms(modulus_code, modulus_scale, length, modulus, tag=f"{tag}_lcm", context=context)
    bounded = _bound(value, modulus, tag=f"{tag}_bounded", context=context)
    solution = _solution_terms(
        residue_code, residue_scale, modulus_code, modulus_scale, length, value,
        tag=f"{tag}_solution", context=context,
    )
    return f"(({least}) /\\ (({bounded}) /\\ ({solution})))"


def crt_canonical_prefix_solution(
    residue_code: str,
    residue_scale: str,
    modulus_code: str,
    modulus_scale: str,
    length: str,
    value: str,
    modulus: str,
    *,
    tag: str,
) -> str:
    """Expand the exact list-lcm, strict bound, and simultaneous congruences."""

    arguments = _arguments(
        (residue_code, "residue code"), (residue_scale, "residue scale"),
        (modulus_code, "modulus code"), (modulus_scale, "modulus scale"),
        (length, "prefix length"), (value, "canonical solution"), (modulus, "list lcm"),
    )
    return _canonical_terms(*arguments, tag=_safe(tag), context=arguments)


def make_generalized_crt_fold_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Return dependency-ordered genuine intuitionistic finite-list CRT proofs."""

    positive = lambda length, tag: _positive_terms("b", "c", length, tag=tag, context=("b", "c", "l"))
    pairwise = lambda length, tag: _pairwise_terms("b", "c", length, tag=tag, context=("b", "c", "l"))
    solution = lambda length, value, tag: _solution_terms(
        "r", "s", "b", "c", length, value,
        tag=tag, context=("r", "s", "b", "c", "l", "x"),
    )

    return (
        spec(
            "crt_positive_moduli_prefix_empty",
            f"forall b c l. l = 0 -> ({positive('l', 'empty')})",
            ("le_zero", "succ_ne_zero"),
            (
                "intro b", "intro c", "intro l", "intro hz", "intro i", "intro m",
                "intro hi", "intro hm", "intro hzero", "rewrite hz at hi",
                "have hbad : S i = 0", "specialize le_zero (S i)", "apply le_zero", "exact hi",
                "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hbad",
            ),
            "An empty decoded modulus prefix has no zero-valued member.",
        ),
        spec(
            "crt_positive_moduli_prefix_drop_last",
            f"forall b c l. ({positive('S l', 'drop_source')}) -> ({positive('l', 'drop_target')})",
            ("le_succ",),
            (
                "intro b", "intro c", "intro l", "intro hpositive", "intro i", "intro m",
                "intro hi", "intro hm", "intro hzero", "specialize hpositive i", "specialize hpositive m",
                "apply hpositive", "specialize le_succ (S i)", "specialize le_succ l",
                "apply le_succ", "exact hi", "exact hm", "exact hzero",
            ),
            "Positivity of a successor-length modulus list restricts to its predecessor prefix.",
        ),
        spec(
            "crt_positive_moduli_prefix_last_nonzero",
            f"forall b c l x. ({positive('S l', 'last_source')}) -> "
            f"({_at('b', 'c', 'l', 'x', tag='last_value', context=('b','c','l','x'))}) -> ~(x = 0)",
            ("le_refl",),
            (
                "intro b", "intro c", "intro l", "intro x", "intro hpositive", "intro hx", "intro hzero",
                "specialize hpositive l", "specialize hpositive x", "apply hpositive",
                "specialize le_refl (S l)", "exact le_refl", "exact hx", "exact hzero",
            ),
            "The final decoded modulus of a positive successor list is nonzero.",
        ),
        spec(
            "crt_pairwise_coprime_prefix_drop_last",
            f"forall b c l. ({pairwise('S l', 'pairwise_drop_source')}) -> "
            f"({pairwise('l', 'pairwise_drop_target')})",
            ("le_succ",),
            (
                "intro b", "intro c", "intro l", "intro hpairs", "intro i", "intro j",
                "intro m", "intro n", "intro hi", "intro hj", "intro hm", "intro hn", "intro hne",
                "specialize hpairs i", "specialize hpairs j", "specialize hpairs m",
                "specialize hpairs n", "apply hpairs",
                "specialize le_succ (S i)", "specialize le_succ l", "apply le_succ", "exact hi",
                "specialize le_succ (S j)", "specialize le_succ l", "apply le_succ", "exact hj",
                "exact hm", "exact hn", "exact hne",
            ),
            "Pairwise coprimality of decoded moduli restricts to every predecessor prefix.",
        ),
        spec(
            "crt_prefix_solution_empty",
            f"forall r s b c l x. l = 0 -> ({solution('l', 'x', 'solution_empty')})",
            ("le_zero", "succ_ne_zero"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro x",
                "intro hz", "intro i", "intro a", "intro m", "intro hi", "intro ha", "intro hm",
                "exfalso", "rewrite hz at hi", "have hbad : S i = 0",
                "specialize le_zero (S i)", "apply le_zero", "exact hi",
                "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hbad",
            ),
            "Every natural number solves the empty simultaneous-congruence system.",
        ),
        spec(
            "crt_prefix_solution_drop_last",
            f"forall r s b c l x. ({solution('S l', 'x', 'solution_drop_source')}) -> "
            f"({solution('l', 'x', 'solution_drop_result')})",
            ("le_succ",),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro x", "intro hsolution",
                "intro i", "intro a", "intro m", "intro hi", "intro ha", "intro hm",
                "specialize hsolution i", "specialize hsolution a", "specialize hsolution m",
                "apply hsolution", "specialize le_succ (S i)", "specialize le_succ l",
                "apply le_succ", "exact hi", "exact ha", "exact hm",
            ),
            "A solution of a successor list remains a solution of the predecessor prefix.",
        ),
        spec(
            "crt_prefix_solution_last",
            f"forall r s b c l x a m. ({solution('S l', 'x', 'solution_last_source')}) -> "
            f"({_at('r','s','l','a',tag='solution_last_residue',context=('r','s','b','c','l','x','a','m'))}) -> "
            f"({_at('b','c','l','m',tag='solution_last_modulus',context=('r','s','b','c','l','x','a','m'))}) -> "
            f"({_mod('m','x','a',tag='solution_last_result',context=('r','s','b','c','l','x','a','m'))})",
            ("le_refl",),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro x", "intro a", "intro m",
                "intro hsolution", "intro ha", "intro hm", "specialize hsolution l",
                "specialize hsolution a", "specialize hsolution m", "apply hsolution",
                "specialize le_refl (S l)", "exact le_refl", "exact ha", "exact hm",
            ),
            "The last residue/modulus pair of a solved successor list satisfies its actual congruence.",
        ),
        spec(
            "crt_prefix_solution_successor_intro",
            f"forall r s b c l x a m. ({solution('l', 'x', 'intro_prefix')}) -> "
            f"({_at('r','s','l','a',tag='intro_last_residue',context=('r','s','b','c','l','x','a','m'))}) -> "
            f"({_at('b','c','l','m',tag='intro_last_modulus',context=('r','s','b','c','l','x','a','m'))}) -> "
            f"({_mod('m','x','a',tag='intro_last_congruence',context=('r','s','b','c','l','x','a','m'))}) -> "
            f"({solution('S l', 'x', 'intro_result')})",
            ("finite_lt_succ_eq_or_lt", "beta_at_unique"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro x", "intro a", "intro m",
                "intro hprefix", "intro ha", "intro hm", "intro hnew", "intro i", "intro q", "intro n",
                "intro hi", "intro hq", "intro hn",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l", "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "rewrite hsplit_left at hq", "rewrite hsplit_left at hq",
                "rewrite hsplit_left at hn", "rewrite hsplit_left at hn",
                "have hresidue : q = a", "specialize beta_at_unique r", "specialize beta_at_unique s",
                "specialize beta_at_unique l", "specialize beta_at_unique q", "specialize beta_at_unique a",
                "apply beta_at_unique", "exact hq", "exact ha",
                "have hmodulus : n = m", "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique l", "specialize beta_at_unique n", "specialize beta_at_unique m",
                "apply beta_at_unique", "exact hn", "exact hm",
                "rewrite hmodulus", "rewrite hmodulus", "rewrite hresidue", "exact hnew",
                "specialize hprefix i", "specialize hprefix q", "specialize hprefix n",
                "apply hprefix", "exact hsplit_right", "exact hq", "exact hn",
            ),
            "A solved predecessor prefix extends exactly when the actual last decoded congruence holds.",
        ),
        spec(
            "crt_pairwise_coprime_prefix_last",
            f"forall b c l i n m. ({pairwise('S l', 'last_pair_source')}) -> "
            f"({_bound('i','l',tag='last_pair_index',context=('b','c','l','i','n','m'))}) -> "
            f"({_at('b','c','i','n',tag='last_pair_old',context=('b','c','l','i','n','m'))}) -> "
            f"({_at('b','c','l','m',tag='last_pair_new',context=('b','c','l','i','n','m'))}) -> "
            f"({coprime('n','m',tag='gcrt_last_pair_result')})",
            ("le_succ", "le_refl", "lt_irrefl_expanded"),
            (
                "intro b", "intro c", "intro l", "intro i", "intro n", "intro m", "intro hpairs",
                "intro hi", "intro hn", "intro hm", "specialize hpairs i", "specialize hpairs l",
                "specialize hpairs n", "specialize hpairs m", "apply hpairs",
                "specialize le_succ (S i)", "specialize le_succ l", "apply le_succ", "exact hi",
                "specialize le_refl (S l)", "exact le_refl", "exact hn", "exact hm", "intro heq",
                "rewrite heq at hi", "specialize lt_irrefl_expanded l", "apply lt_irrefl_expanded", "exact hi",
            ),
            "The last decoded modulus is coprime to every actual earlier modulus in a pairwise-coprime list.",
        ),
        spec(
            "crt_positive_moduli_prefix_product_nonzero",
            f"forall b c l x. ({positive('l', 'product_nonzero_source')}) -> "
            f"({product_relation('b','c','l','x',tag='gcrt_product_nonzero')}) -> ~(x = 0)",
            (
                "beta_product_zero", "succ_ne_zero", "beta_product_succ_decompose",
                "crt_positive_moduli_prefix_drop_last", "crt_positive_moduli_prefix_last_nonzero", "mul_ne_zero",
            ),
            (
                "intro b", "intro c", "induction l",
                "intro x", "intro hpositive", "intro hproduct", "intro hzero",
                "have hunit : x = 1", "specialize beta_product_zero b", "specialize beta_product_zero c",
                "specialize beta_product_zero x", "apply beta_product_zero", "exact hproduct",
                "rewrite hunit at hzero", "specialize succ_ne_zero 0", "apply succ_ne_zero", "exact hzero",
                "intro x", "intro hpositive", "intro hproduct", "intro hzero",
                "have hdecomposition : exists p q. "
                f"(({_at('b','c','l','p',tag='nonzero_decompose_last',context=('b','c','l','x','p','q'))}) /\\ "
                f"(({product_relation('b','c','l','q',tag='gcrt_nonzero_decompose_prefix')}) /\\ x = q * p))",
                "specialize beta_product_succ_decompose b", "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose l", "specialize beta_product_succ_decompose x",
                "apply beta_product_succ_decompose", "exact hproduct",
                "cases hdecomposition", "cases hdecomposition_witness", "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                f"have hrestricted : {positive('l', 'product_nonzero_restricted')}",
                "specialize crt_positive_moduli_prefix_drop_last b",
                "specialize crt_positive_moduli_prefix_drop_last c",
                "specialize crt_positive_moduli_prefix_drop_last l",
                "apply crt_positive_moduli_prefix_drop_last", "exact hpositive",
                "have hprefix_nonzero : ~(x2 = 0)", "specialize IH x2", "intro hprefix_zero",
                "apply IH", "exact hrestricted", "exact hdecomposition_witness_witness_right_left", "exact hprefix_zero",
                "have hlast_nonzero : ~(x1 = 0)",
                "specialize crt_positive_moduli_prefix_last_nonzero b",
                "specialize crt_positive_moduli_prefix_last_nonzero c",
                "specialize crt_positive_moduli_prefix_last_nonzero l",
                "specialize crt_positive_moduli_prefix_last_nonzero x1", "intro hlast_zero",
                "apply crt_positive_moduli_prefix_last_nonzero", "exact hpositive",
                "exact hdecomposition_witness_witness_left", "exact hlast_zero",
                "rewrite hdecomposition_witness_witness_right_right at hzero",
                "specialize mul_ne_zero x2", "specialize mul_ne_zero x1", "apply mul_ne_zero",
                "exact hprefix_nonzero", "exact hlast_nonzero", "exact hzero",
            ),
            "A genuine beta-coded product of an arbitrary positive finite modulus list is nonzero.",
        ),
        spec(
            "crt_prefix_product_common_multiple",
            f"forall b c l x. ({product_relation('b','c','l','x',tag='gcrt_product_multiple')}) -> "
            f"({_common_terms('b','c','l','x',tag='product_multiple_result',context=('b','c','l','x'))})",
            ("beta_factor_divides_product",),
            (
                "intro b", "intro c", "intro l", "intro x", "intro hproduct", "intro i", "intro m",
                "intro hi", "intro hm", "specialize beta_factor_divides_product b",
                "specialize beta_factor_divides_product c", "specialize beta_factor_divides_product l",
                "specialize beta_factor_divides_product x", "specialize beta_factor_divides_product i",
                "specialize beta_factor_divides_product m", "apply beta_factor_divides_product",
                "exact hi", "exact hm", "exact hproduct",
            ),
            "The actual finite beta-product is a common multiple of every decoded modulus.",
        ),
        spec(
            "crt_pairwise_coprime_prefix_product_is_lcm",
            f"forall b c l x. ({pairwise('l', 'product_lcm_pairwise')}) -> "
            f"({product_relation('b','c','l','x',tag='gcrt_product_lcm_source')}) -> "
            f"({_lcm_terms('b','c','l','x',tag='product_lcm_result',context=('b','c','l','x'))})",
            ("crt_prefix_product_common_multiple", "beta_pairwise_coprime_product_divides_common_multiple"),
            (
                "intro b", "intro c", "intro l", "intro x", "intro hpairs", "intro hproduct", "split",
                "specialize crt_prefix_product_common_multiple b", "specialize crt_prefix_product_common_multiple c",
                "specialize crt_prefix_product_common_multiple l", "specialize crt_prefix_product_common_multiple x",
                "apply crt_prefix_product_common_multiple", "exact hproduct",
                "intro z", "intro hcommon", "specialize beta_pairwise_coprime_product_divides_common_multiple b",
                "specialize beta_pairwise_coprime_product_divides_common_multiple c",
                "specialize beta_pairwise_coprime_product_divides_common_multiple l",
                "specialize beta_pairwise_coprime_product_divides_common_multiple x",
                "specialize beta_pairwise_coprime_product_divides_common_multiple z",
                "apply beta_pairwise_coprime_product_divides_common_multiple", "exact hpairs",
                "exact hcommon", "exact hproduct",
            ),
            "For pairwise-coprime decoded moduli the actual finite product is exactly their universal-property lcm.",
        ),
        spec(
            "crt_prefix_lcm_unique",
            f"forall b c l x y. ({_lcm_terms('b','c','l','x',tag='lcm_unique_left',context=('b','c','l','x','y'))}) -> "
            f"({_lcm_terms('b','c','l','y',tag='lcm_unique_right',context=('b','c','l','x','y'))}) -> x = y",
            ("multiple_antisymm",),
            (
                "intro b", "intro c", "intro l", "intro x", "intro y", "intro hx", "intro hy",
                "cases hx", "cases hy", "specialize multiple_antisymm x", "specialize multiple_antisymm y",
                "apply multiple_antisymm", "specialize hx_right y", "apply hx_right", "exact hy_left",
                "specialize hy_right x", "apply hy_right", "exact hx_left",
            ),
            "The universal-property lcm of any decoded finite modulus prefix is unique whenever it exists.",
        ),
        spec(
            "crt_prefix_lcm_empty",
            f"forall b c. ({_lcm_terms('b','c','0','1',tag='empty_lcm',context=('b','c'))})",
            ("le_zero", "succ_ne_zero", "one_multiple"),
            (
                "intro b", "intro c", "split", "intro i", "intro m", "intro hi", "intro hm", "exfalso",
                "have hbad : S i = 0", "specialize le_zero (S i)", "apply le_zero", "exact hi",
                "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hbad",
                "intro z", "intro hz", "specialize one_multiple z", "exact one_multiple",
            ),
            "The universal-property lcm of the empty decoded modulus list is exactly one.",
        ),
        spec(
            "crt_prefix_lcm_successor_intro",
            f"forall b c l P m M. "
            f"({_lcm_terms('b','c','l','P',tag='step_prefix_lcm',context=('b','c','l','P','m','M'))}) -> "
            f"({_at('b','c','l','m',tag='step_last_modulus',context=('b','c','l','P','m','M'))}) -> "
            f"({is_lcm('M','P','m',tag='gcrt_step_binary_lcm')}) -> "
            f"({_lcm_terms('b','c','S l','M',tag='step_result_lcm',context=('b','c','l','P','m','M'))})",
            (
                "finite_lt_succ_eq_or_lt", "beta_at_unique", "is_lcm_multiple_left",
                "is_lcm_multiple_right", "multiple_trans", "is_lcm_least", "le_succ", "le_refl",
            ),
            (
                "intro b", "intro c", "intro l", "intro P", "intro m", "intro M",
                "intro hprefix", "intro hm", "intro hbinary", "cases hprefix", "split",
                "intro i", "intro n", "intro hi", "intro hn",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l", "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "rewrite hsplit_left at hn", "rewrite hsplit_left at hn",
                "have heq : n = m", "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique l", "specialize beta_at_unique n", "specialize beta_at_unique m",
                "apply beta_at_unique", "exact hn", "exact hm", "rewrite heq",
                "specialize is_lcm_multiple_right M", "specialize is_lcm_multiple_right P",
                "specialize is_lcm_multiple_right m", "apply is_lcm_multiple_right", "exact hbinary",
                "specialize multiple_trans P", "specialize multiple_trans n", "specialize multiple_trans M",
                "apply multiple_trans", "specialize is_lcm_multiple_left M", "specialize is_lcm_multiple_left P",
                "specialize is_lcm_multiple_left m", "apply is_lcm_multiple_left", "exact hbinary",
                "specialize hprefix_left i", "specialize hprefix_left n", "apply hprefix_left",
                "exact hsplit_right", "exact hn",
                "intro z", "intro hcommon", "specialize is_lcm_least M", "specialize is_lcm_least P",
                "specialize is_lcm_least m", "specialize is_lcm_least z", "apply is_lcm_least", "exact hbinary",
                "specialize hprefix_right z", "apply hprefix_right", "intro i", "intro n", "intro hi", "intro hn",
                "specialize hcommon i", "specialize hcommon n", "apply hcommon",
                "specialize le_succ (S i)", "specialize le_succ l", "apply le_succ", "exact hi", "exact hn",
                "specialize hcommon l", "specialize hcommon m", "apply hcommon",
                "specialize le_refl (S l)", "exact le_refl", "exact hm",
            ),
            "Binary relational lcm extends the exact universal-property lcm of any finite decoded modulus prefix.",
        ),
        spec(
            "crt_prefix_lcm_exists_unique",
            f"forall b c l. exists x. "
            f"(({_lcm_terms('b','c','l','x',tag='general_lcm_chosen',context=('b','c','l','x'))}) /\\ "
            f"forall y. ({_lcm_terms('b','c','l','y',tag='general_lcm_compared',context=('b','c','l','y'))}) -> y = x)",
            (
                "crt_prefix_lcm_empty", "crt_prefix_lcm_unique", "beta_at_exists",
                "lcm_exists_relational", "crt_prefix_lcm_successor_intro",
            ),
            (
                "intro b", "intro c", "induction l", "exists 1", "split",
                "specialize crt_prefix_lcm_empty b", "specialize crt_prefix_lcm_empty c", "exact crt_prefix_lcm_empty",
                "intro y", "intro hy", "specialize crt_prefix_lcm_unique b", "specialize crt_prefix_lcm_unique c",
                "specialize crt_prefix_lcm_unique 0", "specialize crt_prefix_lcm_unique y",
                "specialize crt_prefix_lcm_unique 1", "apply crt_prefix_lcm_unique", "exact hy",
                "specialize crt_prefix_lcm_empty b", "specialize crt_prefix_lcm_empty c", "exact crt_prefix_lcm_empty",
                "cases IH", "cases IH_witness",
                "have hlast : exists m. "
                f"({_at('b','c','l','m',tag='general_lcm_last',context=('b','c','l','x','m'))})",
                "specialize beta_at_exists b", "specialize beta_at_exists c", "specialize beta_at_exists l",
                "exact beta_at_exists", "cases hlast", "specialize lcm_exists_relational x",
                "specialize lcm_exists_relational x1", "cases lcm_exists_relational", "exists x2", "split",
                "specialize crt_prefix_lcm_successor_intro b", "specialize crt_prefix_lcm_successor_intro c",
                "specialize crt_prefix_lcm_successor_intro l", "specialize crt_prefix_lcm_successor_intro x",
                "specialize crt_prefix_lcm_successor_intro x1", "specialize crt_prefix_lcm_successor_intro x2",
                "apply crt_prefix_lcm_successor_intro", "exact IH_witness_left", "exact hlast_witness",
                "exact lcm_exists_relational_witness",
                "intro y", "intro hy", "specialize crt_prefix_lcm_unique b", "specialize crt_prefix_lcm_unique c",
                "specialize crt_prefix_lcm_unique (S l)", "specialize crt_prefix_lcm_unique y",
                "specialize crt_prefix_lcm_unique x2", "apply crt_prefix_lcm_unique", "exact hy",
                "specialize crt_prefix_lcm_successor_intro b", "specialize crt_prefix_lcm_successor_intro c",
                "specialize crt_prefix_lcm_successor_intro l", "specialize crt_prefix_lcm_successor_intro x",
                "specialize crt_prefix_lcm_successor_intro x1", "specialize crt_prefix_lcm_successor_intro x2",
                "apply crt_prefix_lcm_successor_intro", "exact IH_witness_left", "exact hlast_witness",
                "exact lcm_exists_relational_witness",
            ),
            "Every arbitrary finite decoded modulus list, including noncoprime and zero entries, has a unique exact lcm.",
        ),
        spec(
            "crt_pairwise_coprime_prefix_lcm_exists_unique",
            f"forall b c l. ({pairwise('l', 'lcm_exists_pairwise')}) -> exists x. "
            f"(({_lcm_terms('b','c','l','x',tag='lcm_exists_chosen',context=('b','c','l','x'))}) /\\ "
            f"forall y. ({_lcm_terms('b','c','l','y',tag='lcm_exists_compared',context=('b','c','l','y'))}) -> y = x)",
            ("beta_product_exists_unique", "crt_pairwise_coprime_prefix_product_is_lcm", "crt_prefix_lcm_unique"),
            (
                "intro b", "intro c", "intro l", "intro hpairs", "specialize beta_product_exists_unique b",
                "specialize beta_product_exists_unique c", "specialize beta_product_exists_unique l",
                "cases beta_product_exists_unique", "cases beta_product_exists_unique_witness", "exists x", "split",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm b",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm c",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm l",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm x",
                "apply crt_pairwise_coprime_prefix_product_is_lcm", "exact hpairs",
                "exact beta_product_exists_unique_witness_left", "intro y", "intro hy",
                "specialize crt_prefix_lcm_unique b", "specialize crt_prefix_lcm_unique c",
                "specialize crt_prefix_lcm_unique l", "specialize crt_prefix_lcm_unique y",
                "specialize crt_prefix_lcm_unique x", "apply crt_prefix_lcm_unique", "exact hy",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm b",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm c",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm l",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm x",
                "apply crt_pairwise_coprime_prefix_product_is_lcm", "exact hpairs",
                "exact beta_product_exists_unique_witness_left",
            ),
            "Every arbitrary finite pairwise-coprime modulus list has a unique relational lcm.",
        ),
        spec(
            "crt_pairwise_coprime_prefix_product_coprime_last",
            f"forall b c l x m. ({pairwise('S l', 'product_last_pairs')}) -> "
            f"({product_relation('b','c','l','x',tag='gcrt_product_last_prefix')}) -> "
            f"({_at('b','c','l','m',tag='product_last_entry',context=('b','c','l','x','m'))}) -> "
            f"({coprime('x','m',tag='gcrt_product_last_coprime')})",
            ("beta_product_pointwise_coprime", "crt_pairwise_coprime_prefix_last"),
            (
                "intro b", "intro c", "intro l", "intro x", "intro m", "intro hpairs", "intro hproduct", "intro hm",
                "specialize beta_product_pointwise_coprime m", "specialize beta_product_pointwise_coprime b",
                "specialize beta_product_pointwise_coprime c", "specialize beta_product_pointwise_coprime l",
                "specialize beta_product_pointwise_coprime x", "apply beta_product_pointwise_coprime",
                "intro i", "intro n", "intro hi", "intro hn",
                "specialize crt_pairwise_coprime_prefix_last b", "specialize crt_pairwise_coprime_prefix_last c",
                "specialize crt_pairwise_coprime_prefix_last l", "specialize crt_pairwise_coprime_prefix_last i",
                "specialize crt_pairwise_coprime_prefix_last n", "specialize crt_pairwise_coprime_prefix_last m",
                "apply crt_pairwise_coprime_prefix_last", "exact hpairs", "exact hi", "exact hn", "exact hm",
                "exact hproduct",
            ),
            "The actual predecessor product is coprime to the final modulus of any pairwise-coprime list.",
        ),
        spec(
            "crt_pairwise_coprime_prefix_solution_exists",
            f"forall r s b c l. ({positive('l', 'fold_positive')}) -> "
            f"({pairwise('l', 'fold_pairwise')}) -> exists x. "
            f"({_solution_terms('r','s','b','c','l','x',tag='fold_result',context=('r','s','b','c','l','x'))})",
            (
                "crt_prefix_solution_empty", "crt_positive_moduli_prefix_drop_last",
                "crt_pairwise_coprime_prefix_drop_last", "beta_product_exists_unique",
                "beta_at_exists", "crt_positive_moduli_prefix_product_nonzero",
                "crt_positive_moduli_prefix_last_nonzero",
                "crt_pairwise_coprime_prefix_product_coprime_last", "binary_crt_fold_step",
                "beta_factor_divides_product", "crt_prefix_solution_successor_intro",
            ),
            (
                "intro r", "intro s", "intro b", "intro c", "induction l",
                "intro hpositive", "intro hpairs", "exists 0",
                "specialize crt_prefix_solution_empty r", "specialize crt_prefix_solution_empty s",
                "specialize crt_prefix_solution_empty b", "specialize crt_prefix_solution_empty c",
                "specialize crt_prefix_solution_empty 0", "specialize crt_prefix_solution_empty 0",
                "apply crt_prefix_solution_empty", "refl",
                "intro hpositive", "intro hpairs",
                f"have hpositive_prefix : {positive('l', 'fold_positive_prefix')}",
                "specialize crt_positive_moduli_prefix_drop_last b",
                "specialize crt_positive_moduli_prefix_drop_last c",
                "specialize crt_positive_moduli_prefix_drop_last l",
                "apply crt_positive_moduli_prefix_drop_last", "exact hpositive",
                f"have hpairs_prefix : {pairwise('l', 'fold_pairwise_prefix')}",
                "specialize crt_pairwise_coprime_prefix_drop_last b",
                "specialize crt_pairwise_coprime_prefix_drop_last c",
                "specialize crt_pairwise_coprime_prefix_drop_last l",
                "apply crt_pairwise_coprime_prefix_drop_last", "exact hpairs",
                "have hprevious : exists x. "
                f"({_solution_terms('r','s','b','c','l','x',tag='fold_previous',context=('r','s','b','c','l','x'))})",
                "apply IH", "exact hpositive_prefix", "exact hpairs_prefix", "cases hprevious",
                "specialize beta_product_exists_unique b", "specialize beta_product_exists_unique c",
                "specialize beta_product_exists_unique l", "cases beta_product_exists_unique",
                "cases beta_product_exists_unique_witness",
                "have hmodulus : exists m. "
                f"({_at('b','c','l','m',tag='fold_last_modulus',context=('r','s','b','c','l','x','x1','m'))})",
                "specialize beta_at_exists b", "specialize beta_at_exists c", "specialize beta_at_exists l",
                "exact beta_at_exists", "cases hmodulus",
                "have hresidue : exists a. "
                f"({_at('r','s','l','a',tag='fold_last_residue',context=('r','s','b','c','l','x','x1','x2','a'))})",
                "specialize beta_at_exists r", "specialize beta_at_exists s", "specialize beta_at_exists l",
                "exact beta_at_exists", "cases hresidue",
                "have hproduct_nonzero : ~(x1 = 0)",
                "specialize crt_positive_moduli_prefix_product_nonzero b",
                "specialize crt_positive_moduli_prefix_product_nonzero c",
                "specialize crt_positive_moduli_prefix_product_nonzero l",
                "specialize crt_positive_moduli_prefix_product_nonzero x1", "intro hzero",
                "apply crt_positive_moduli_prefix_product_nonzero", "exact hpositive_prefix",
                "exact beta_product_exists_unique_witness_left", "exact hzero",
                "have hlast_nonzero : ~(x2 = 0)",
                "specialize crt_positive_moduli_prefix_last_nonzero b",
                "specialize crt_positive_moduli_prefix_last_nonzero c",
                "specialize crt_positive_moduli_prefix_last_nonzero l",
                "specialize crt_positive_moduli_prefix_last_nonzero x2", "intro hzero",
                "apply crt_positive_moduli_prefix_last_nonzero", "exact hpositive", "exact hmodulus_witness",
                "exact hzero",
                f"have hcoprime : {coprime('x1','x2',tag='gcrt_fold_local_coprime')}",
                "specialize crt_pairwise_coprime_prefix_product_coprime_last b",
                "specialize crt_pairwise_coprime_prefix_product_coprime_last c",
                "specialize crt_pairwise_coprime_prefix_product_coprime_last l",
                "specialize crt_pairwise_coprime_prefix_product_coprime_last x1",
                "specialize crt_pairwise_coprime_prefix_product_coprime_last x2",
                "apply crt_pairwise_coprime_prefix_product_coprime_last", "exact hpairs",
                "exact beta_product_exists_unique_witness_left", "exact hmodulus_witness",
                "have hfold : exists z. "
                "((forall m a. (exists q. x1 = m * q) -> "
                "(exists u v. x + m * u = a + m * v) -> "
                "exists u v. z + m * u = a + m * v) /\\ "
                "exists u v. z + x2 * u = x3 + x2 * v)",
                "specialize binary_crt_fold_step x1", "specialize binary_crt_fold_step x2",
                "specialize binary_crt_fold_step x", "specialize binary_crt_fold_step x3",
                "apply binary_crt_fold_step", "exact hproduct_nonzero", "exact hlast_nonzero", "exact hcoprime",
                "cases hfold", "cases hfold_witness",
                "have htransported : "
                f"{_solution_terms('r','s','b','c','l','x4',tag='fold_transported',context=('r','s','b','c','l','x','x1','x2','x3','x4'))}",
                "intro i", "intro a", "intro m", "intro hi", "intro ha", "intro hm",
                "specialize hfold_witness_left m", "specialize hfold_witness_left a", "apply hfold_witness_left",
                "specialize beta_factor_divides_product b", "specialize beta_factor_divides_product c",
                "specialize beta_factor_divides_product l", "specialize beta_factor_divides_product x1",
                "specialize beta_factor_divides_product i", "specialize beta_factor_divides_product m",
                "apply beta_factor_divides_product", "exact hi", "exact hm",
                "exact beta_product_exists_unique_witness_left",
                "specialize hprevious_witness i", "specialize hprevious_witness a", "specialize hprevious_witness m",
                "apply hprevious_witness", "exact hi", "exact ha", "exact hm",
                "exists x4", "specialize crt_prefix_solution_successor_intro r",
                "specialize crt_prefix_solution_successor_intro s", "specialize crt_prefix_solution_successor_intro b",
                "specialize crt_prefix_solution_successor_intro c", "specialize crt_prefix_solution_successor_intro l",
                "specialize crt_prefix_solution_successor_intro x4", "specialize crt_prefix_solution_successor_intro x3",
                "specialize crt_prefix_solution_successor_intro x2", "apply crt_prefix_solution_successor_intro",
                "exact htransported", "exact hresidue_witness", "exact hmodulus_witness",
                "exact hfold_witness_right",
            ),
            "Every arbitrary finite beta-coded list of positive pairwise-coprime moduli has an actual simultaneous CRT solution.",
        ),
        spec(
            "crt_prefix_solutions_pointwise_congruent",
            f"forall r s b c l x y i a m. "
            f"({_solution_terms('r','s','b','c','l','x',tag='pointwise_solution_left',context=('r','s','b','c','l','x','y','i','a','m'))}) -> "
            f"({_solution_terms('r','s','b','c','l','y',tag='pointwise_solution_right',context=('r','s','b','c','l','x','y','i','a','m'))}) -> "
            f"({_bound('i','l',tag='pointwise_index',context=('r','s','b','c','l','x','y','i','a','m'))}) -> "
            f"({_at('r','s','i','a',tag='pointwise_residue',context=('r','s','b','c','l','x','y','i','a','m'))}) -> "
            f"({_at('b','c','i','m',tag='pointwise_modulus',context=('r','s','b','c','l','x','y','i','a','m'))}) -> "
            f"({_mod('m','x','y',tag='pointwise_result',context=('r','s','b','c','l','x','y','i','a','m'))})",
            ("mod_eq_symm", "mod_eq_trans"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro x", "intro y",
                "intro i", "intro a", "intro m", "intro hx", "intro hy", "intro hi", "intro ha", "intro hm",
                "specialize mod_eq_trans m", "specialize mod_eq_trans x", "specialize mod_eq_trans a",
                "specialize mod_eq_trans y", "apply mod_eq_trans",
                "specialize hx i", "specialize hx a", "specialize hx m", "apply hx", "exact hi", "exact ha", "exact hm",
                "specialize mod_eq_symm m", "specialize mod_eq_symm y", "specialize mod_eq_symm a", "apply mod_eq_symm",
                "specialize hy i", "specialize hy a", "specialize hy m", "apply hy", "exact hi", "exact ha", "exact hm",
            ),
            "Two simultaneous solutions are congruent modulo every actually decoded list modulus.",
        ),
        spec(
            "crt_prefix_solution_transport_common_multiple",
            f"forall r s b c l M x y. "
            f"({_common_terms('b','c','l','M',tag='transport_multiple',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_solution_terms('r','s','b','c','l','x',tag='transport_source',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_mod('M','y','x',tag='transport_congruence',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_solution_terms('r','s','b','c','l','y',tag='transport_result',context=('r','s','b','c','l','M','x','y'))})",
            ("mod_eq_of_mod_eq_multiple", "mod_eq_trans"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro M", "intro x", "intro y",
                "intro hcommon", "intro hx", "intro hmod", "intro i", "intro a", "intro m", "intro hi", "intro ha", "intro hm",
                "specialize mod_eq_trans m", "specialize mod_eq_trans y", "specialize mod_eq_trans x",
                "specialize mod_eq_trans a", "apply mod_eq_trans",
                "specialize mod_eq_of_mod_eq_multiple m", "specialize mod_eq_of_mod_eq_multiple M",
                "specialize mod_eq_of_mod_eq_multiple y", "specialize mod_eq_of_mod_eq_multiple x",
                "apply mod_eq_of_mod_eq_multiple", "specialize hcommon i", "specialize hcommon m",
                "apply hcommon", "exact hi", "exact hm", "exact hmod",
                "specialize hx i", "specialize hx a", "specialize hx m", "apply hx", "exact hi", "exact ha", "exact hm",
            ),
            "Congruence modulo any common multiple transports an actual simultaneous-list solution.",
        ),
        spec(
            "crt_prefix_ordered_solutions_gap_multiple",
            f"forall r s b c l M x y k. "
            f"({_lcm_terms('b','c','l','M',tag='gap_lcm',context=('r','s','b','c','l','M','x','y','k'))}) -> "
            f"({_solution_terms('r','s','b','c','l','x',tag='gap_solution_left',context=('r','s','b','c','l','M','x','y','k'))}) -> "
            f"({_solution_terms('r','s','b','c','l','y',tag='gap_solution_right',context=('r','s','b','c','l','M','x','y','k'))}) -> "
            "k + x = y -> exists q. k = M * q",
            ("beta_at_exists", "crt_prefix_solutions_pointwise_congruent", "mod_eq_ordered_gap_multiple"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro M", "intro x", "intro y", "intro k",
                "intro hlcm", "intro hx", "intro hy", "intro hgap", "cases hlcm", "specialize hlcm_right k",
                "apply hlcm_right", "intro i", "intro m", "intro hi", "intro hm",
                "have hresidue : exists a. "
                f"({_at('r','s','i','a',tag='gap_decoded_residue',context=('r','s','b','c','l','M','x','y','k','i','m','a'))})",
                "specialize beta_at_exists r", "specialize beta_at_exists s", "specialize beta_at_exists i",
                "exact beta_at_exists", "cases hresidue",
                "specialize mod_eq_ordered_gap_multiple m", "specialize mod_eq_ordered_gap_multiple k",
                "specialize mod_eq_ordered_gap_multiple x", "specialize mod_eq_ordered_gap_multiple y",
                "apply mod_eq_ordered_gap_multiple", "exact hgap",
                "specialize crt_prefix_solutions_pointwise_congruent r",
                "specialize crt_prefix_solutions_pointwise_congruent s",
                "specialize crt_prefix_solutions_pointwise_congruent b",
                "specialize crt_prefix_solutions_pointwise_congruent c",
                "specialize crt_prefix_solutions_pointwise_congruent l",
                "specialize crt_prefix_solutions_pointwise_congruent x",
                "specialize crt_prefix_solutions_pointwise_congruent y",
                "specialize crt_prefix_solutions_pointwise_congruent i",
                "specialize crt_prefix_solutions_pointwise_congruent x1",
                "specialize crt_prefix_solutions_pointwise_congruent m",
                "apply crt_prefix_solutions_pointwise_congruent", "exact hx", "exact hy", "exact hi",
                "exact hresidue_witness", "exact hm",
            ),
            "For every finite list, the directed gap between two solutions is divisible by its universal-property lcm.",
        ),
        spec(
            "crt_prefix_solutions_congruent_lcm",
            f"forall r s b c l M x y. "
            f"({_lcm_terms('b','c','l','M',tag='class_lcm',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_solution_terms('r','s','b','c','l','x',tag='class_solution_left',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_solution_terms('r','s','b','c','l','y',tag='class_solution_right',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_mod('M','x','y',tag='class_result',context=('r','s','b','c','l','M','x','y'))})",
            (
                "le_total", "crt_prefix_ordered_solutions_gap_multiple",
                "remainder_decomposition_to_mod_eq", "mul_comm", "mod_eq_symm",
            ),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro M", "intro x", "intro y",
                "intro hlcm", "intro hx", "intro hy", "specialize le_total x", "specialize le_total y",
                "cases le_total", "cases le_total_left",
                "have hgap : exists q. x1 = M * q",
                "specialize crt_prefix_ordered_solutions_gap_multiple r",
                "specialize crt_prefix_ordered_solutions_gap_multiple s",
                "specialize crt_prefix_ordered_solutions_gap_multiple b",
                "specialize crt_prefix_ordered_solutions_gap_multiple c",
                "specialize crt_prefix_ordered_solutions_gap_multiple l",
                "specialize crt_prefix_ordered_solutions_gap_multiple M",
                "specialize crt_prefix_ordered_solutions_gap_multiple x",
                "specialize crt_prefix_ordered_solutions_gap_multiple y",
                "specialize crt_prefix_ordered_solutions_gap_multiple x1",
                "apply crt_prefix_ordered_solutions_gap_multiple", "exact hlcm", "exact hx", "exact hy",
                "exact le_total_left_witness", "cases hgap",
                f"have hreverse : {_mod('M','y','x',tag='class_reverse',context=('r','s','b','c','l','M','x','y','x1','x2'))}",
                "specialize remainder_decomposition_to_mod_eq M", "specialize remainder_decomposition_to_mod_eq y",
                "specialize remainder_decomposition_to_mod_eq x2", "specialize remainder_decomposition_to_mod_eq x",
                "apply remainder_decomposition_to_mod_eq", "trans x1 + x", "symm",
                "exact le_total_left_witness", "rewrite hgap_witness", "congr", "apply mul_comm", "refl",
                "specialize mod_eq_symm M", "specialize mod_eq_symm y", "specialize mod_eq_symm x",
                "apply mod_eq_symm", "exact hreverse",
                "cases le_total_right", "have hgap : exists q. x1 = M * q",
                "specialize crt_prefix_ordered_solutions_gap_multiple r",
                "specialize crt_prefix_ordered_solutions_gap_multiple s",
                "specialize crt_prefix_ordered_solutions_gap_multiple b",
                "specialize crt_prefix_ordered_solutions_gap_multiple c",
                "specialize crt_prefix_ordered_solutions_gap_multiple l",
                "specialize crt_prefix_ordered_solutions_gap_multiple M",
                "specialize crt_prefix_ordered_solutions_gap_multiple y",
                "specialize crt_prefix_ordered_solutions_gap_multiple x",
                "specialize crt_prefix_ordered_solutions_gap_multiple x1",
                "apply crt_prefix_ordered_solutions_gap_multiple", "exact hlcm", "exact hy", "exact hx",
                "exact le_total_right_witness", "cases hgap",
                "specialize remainder_decomposition_to_mod_eq M", "specialize remainder_decomposition_to_mod_eq x",
                "specialize remainder_decomposition_to_mod_eq x2", "specialize remainder_decomposition_to_mod_eq y",
                "apply remainder_decomposition_to_mod_eq", "trans x1 + y", "symm",
                "exact le_total_right_witness", "rewrite hgap_witness", "congr", "apply mul_comm", "refl",
            ),
            "For arbitrary decoded lists, every two simultaneous solutions are congruent modulo the exact list lcm.",
        ),
        spec(
            "crt_prefix_solution_class_iff_lcm",
            f"forall r s b c l M x y. "
            f"({_lcm_terms('b','c','l','M',tag='iff_lcm',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_solution_terms('r','s','b','c','l','x',tag='iff_fixed',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"((({_solution_terms('r','s','b','c','l','y',tag='iff_candidate_forward',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_mod('M','y','x',tag='iff_mod_forward',context=('r','s','b','c','l','M','x','y'))})) /\\ "
            f"(({_mod('M','y','x',tag='iff_mod_reverse',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_solution_terms('r','s','b','c','l','y',tag='iff_candidate_reverse',context=('r','s','b','c','l','M','x','y'))})))",
            ("crt_prefix_solutions_congruent_lcm", "crt_prefix_solution_transport_common_multiple"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro M", "intro x", "intro y",
                "intro hlcm", "intro hx", "split", "intro hy",
                "specialize crt_prefix_solutions_congruent_lcm r", "specialize crt_prefix_solutions_congruent_lcm s",
                "specialize crt_prefix_solutions_congruent_lcm b", "specialize crt_prefix_solutions_congruent_lcm c",
                "specialize crt_prefix_solutions_congruent_lcm l", "specialize crt_prefix_solutions_congruent_lcm M",
                "specialize crt_prefix_solutions_congruent_lcm y", "specialize crt_prefix_solutions_congruent_lcm x",
                "apply crt_prefix_solutions_congruent_lcm", "exact hlcm", "exact hy", "exact hx",
                "intro hmod", "cases hlcm", "specialize crt_prefix_solution_transport_common_multiple r",
                "specialize crt_prefix_solution_transport_common_multiple s",
                "specialize crt_prefix_solution_transport_common_multiple b",
                "specialize crt_prefix_solution_transport_common_multiple c",
                "specialize crt_prefix_solution_transport_common_multiple l",
                "specialize crt_prefix_solution_transport_common_multiple M",
                "specialize crt_prefix_solution_transport_common_multiple x",
                "specialize crt_prefix_solution_transport_common_multiple y",
                "apply crt_prefix_solution_transport_common_multiple", "exact hlcm_left", "exact hx", "exact hmod",
            ),
            "The complete solution class of any finite system is exactly one congruence class modulo its list lcm.",
        ),
        spec(
            "crt_prefix_solution_canonical_remainder",
            f"forall r s b c l M x. ~(M = 0) -> "
            f"({_lcm_terms('b','c','l','M',tag='canonical_remainder_lcm',context=('r','s','b','c','l','M','x'))}) -> "
            f"({_solution_terms('r','s','b','c','l','x',tag='canonical_remainder_source',context=('r','s','b','c','l','M','x'))}) -> exists y. "
            f"({_canonical_terms('r','s','b','c','l','y','M',tag='canonical_remainder_result',context=('r','s','b','c','l','M','x','y'))})",
            (
                "canonical_remainder_exists", "remainder_decomposition_to_mod_eq",
                "mul_comm", "mod_eq_symm", "crt_prefix_solution_transport_common_multiple",
            ),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro M", "intro x",
                "intro hnonzero", "intro hlcm", "intro hx",
                "have hrem : exists y. ((exists q. x = M * q + y) /\\ exists gap. gap + S y = M)",
                "specialize canonical_remainder_exists M", "specialize canonical_remainder_exists x",
                "apply canonical_remainder_exists", "exact hnonzero", "cases hrem", "cases hrem_witness",
                "cases hrem_witness_left",
                f"have hforward : {_mod('M','x','x1',tag='canonical_forward',context=('r','s','b','c','l','M','x','x1','x2'))}",
                "specialize remainder_decomposition_to_mod_eq M", "specialize remainder_decomposition_to_mod_eq x",
                "specialize remainder_decomposition_to_mod_eq x2", "specialize remainder_decomposition_to_mod_eq x1",
                "apply remainder_decomposition_to_mod_eq", "trans M * x2 + x1",
                "exact hrem_witness_left_witness", "congr", "apply mul_comm", "refl",
                f"have hreverse : {_mod('M','x1','x',tag='canonical_reverse',context=('r','s','b','c','l','M','x','x1','x2'))}",
                "specialize mod_eq_symm M", "specialize mod_eq_symm x", "specialize mod_eq_symm x1",
                "apply mod_eq_symm", "exact hforward", "exists x1", "split", "exact hlcm", "split",
                "exact hrem_witness_right", "cases hlcm", "specialize crt_prefix_solution_transport_common_multiple r",
                "specialize crt_prefix_solution_transport_common_multiple s",
                "specialize crt_prefix_solution_transport_common_multiple b",
                "specialize crt_prefix_solution_transport_common_multiple c",
                "specialize crt_prefix_solution_transport_common_multiple l",
                "specialize crt_prefix_solution_transport_common_multiple M",
                "specialize crt_prefix_solution_transport_common_multiple x",
                "specialize crt_prefix_solution_transport_common_multiple x1",
                "apply crt_prefix_solution_transport_common_multiple", "exact hlcm_left", "exact hx", "exact hreverse",
            ),
            "Every existing finite-list solution has an actual canonical representative strictly below its nonzero list lcm.",
        ),
        spec(
            "crt_canonical_prefix_solution_unique",
            f"forall r s b c l M x y. "
            f"({_canonical_terms('r','s','b','c','l','x','M',tag='canonical_unique_left',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_canonical_terms('r','s','b','c','l','y','M',tag='canonical_unique_right',context=('r','s','b','c','l','M','x','y'))}) -> y = x",
            ("crt_prefix_solutions_congruent_lcm", "mod_eq_bounded_unique"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro M", "intro x", "intro y",
                "intro hx", "intro hy", "cases hx", "cases hx_right", "cases hy", "cases hy_right",
                "specialize mod_eq_bounded_unique M", "specialize mod_eq_bounded_unique y",
                "specialize mod_eq_bounded_unique x", "apply mod_eq_bounded_unique",
                "exact hy_right_left", "exact hx_right_left",
                "specialize crt_prefix_solutions_congruent_lcm r", "specialize crt_prefix_solutions_congruent_lcm s",
                "specialize crt_prefix_solutions_congruent_lcm b", "specialize crt_prefix_solutions_congruent_lcm c",
                "specialize crt_prefix_solutions_congruent_lcm l", "specialize crt_prefix_solutions_congruent_lcm M",
                "specialize crt_prefix_solutions_congruent_lcm y", "specialize crt_prefix_solutions_congruent_lcm x",
                "apply crt_prefix_solutions_congruent_lcm", "exact hx_left", "exact hy_right_right", "exact hx_right_right",
            ),
            "The strictly bounded canonical representative of any finite decoded CRT system is unique.",
        ),
        spec(
            "crt_pairwise_coprime_prefix_canonical_exists_unique",
            f"forall r s b c l. ({positive('l', 'final_positive')}) -> "
            f"({pairwise('l', 'final_pairwise')}) -> exists x M. "
            f"(({_canonical_terms('r','s','b','c','l','x','M',tag='final_chosen',context=('r','s','b','c','l','x','M'))}) /\\ "
            f"forall y. ({_canonical_terms('r','s','b','c','l','y','M',tag='final_compared',context=('r','s','b','c','l','M','y'))}) -> y = x)",
            (
                "beta_product_exists_unique", "crt_positive_moduli_prefix_product_nonzero",
                "crt_pairwise_coprime_prefix_product_is_lcm", "crt_pairwise_coprime_prefix_solution_exists",
                "crt_prefix_solution_canonical_remainder", "crt_canonical_prefix_solution_unique",
            ),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro hpositive", "intro hpairs",
                "specialize beta_product_exists_unique b", "specialize beta_product_exists_unique c",
                "specialize beta_product_exists_unique l", "cases beta_product_exists_unique",
                "cases beta_product_exists_unique_witness",
                "have hnonzero : ~(x = 0)", "specialize crt_positive_moduli_prefix_product_nonzero b",
                "specialize crt_positive_moduli_prefix_product_nonzero c",
                "specialize crt_positive_moduli_prefix_product_nonzero l",
                "specialize crt_positive_moduli_prefix_product_nonzero x", "intro hzero",
                "apply crt_positive_moduli_prefix_product_nonzero", "exact hpositive",
                "exact beta_product_exists_unique_witness_left", "exact hzero",
                f"have hlcm : {_lcm_terms('b','c','l','x',tag='final_actual_lcm',context=('r','s','b','c','l','x'))}",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm b",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm c",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm l",
                "specialize crt_pairwise_coprime_prefix_product_is_lcm x",
                "apply crt_pairwise_coprime_prefix_product_is_lcm", "exact hpairs",
                "exact beta_product_exists_unique_witness_left",
                "have hsolution : exists y. "
                f"({_solution_terms('r','s','b','c','l','y',tag='final_unbounded',context=('r','s','b','c','l','x','y'))})",
                "specialize crt_pairwise_coprime_prefix_solution_exists r",
                "specialize crt_pairwise_coprime_prefix_solution_exists s",
                "specialize crt_pairwise_coprime_prefix_solution_exists b",
                "specialize crt_pairwise_coprime_prefix_solution_exists c",
                "specialize crt_pairwise_coprime_prefix_solution_exists l",
                "apply crt_pairwise_coprime_prefix_solution_exists", "exact hpositive", "exact hpairs",
                "cases hsolution",
                "have hcanonical : exists z. "
                f"({_canonical_terms('r','s','b','c','l','z','x',tag='final_canonical',context=('r','s','b','c','l','x','x1','z'))})",
                "specialize crt_prefix_solution_canonical_remainder r",
                "specialize crt_prefix_solution_canonical_remainder s",
                "specialize crt_prefix_solution_canonical_remainder b",
                "specialize crt_prefix_solution_canonical_remainder c",
                "specialize crt_prefix_solution_canonical_remainder l",
                "specialize crt_prefix_solution_canonical_remainder x",
                "specialize crt_prefix_solution_canonical_remainder x1",
                "apply crt_prefix_solution_canonical_remainder", "exact hnonzero", "exact hlcm", "exact hsolution_witness",
                "cases hcanonical", "exists x2", "exists x", "split", "exact hcanonical_witness", "intro y", "intro hy",
                "specialize crt_canonical_prefix_solution_unique r",
                "specialize crt_canonical_prefix_solution_unique s",
                "specialize crt_canonical_prefix_solution_unique b",
                "specialize crt_canonical_prefix_solution_unique c",
                "specialize crt_canonical_prefix_solution_unique l",
                "specialize crt_canonical_prefix_solution_unique x",
                "specialize crt_canonical_prefix_solution_unique x2",
                "specialize crt_canonical_prefix_solution_unique y",
                "apply crt_canonical_prefix_solution_unique", "exact hcanonical_witness", "exact hy",
            ),
            "Every arbitrary finite list of positive pairwise-coprime moduli has its exact lcm and a unique actual bounded CRT solution.",
        ),
    )


__all__ = [
    "GeneralizedCRTFoldError",
    "crt_canonical_prefix_solution",
    "crt_pairwise_coprime_prefix",
    "crt_positive_moduli_prefix",
    "crt_prefix_lcm",
    "crt_prefix_solution",
    "make_generalized_crt_fold_candidate_theorems",
]
