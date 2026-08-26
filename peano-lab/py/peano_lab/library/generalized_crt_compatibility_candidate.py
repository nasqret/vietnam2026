"""Constructive compatibility and non-coprime finite Chinese-remainder folds.

Every relation below is a hygienic expansion into unchanged first-order
Heyting arithmetic.  Pairwise gcd compatibility is kept distinct from the
stronger operational merge invariant; no implication between them is assumed.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_product_candidate import coprime
from .finite_fold_surface import product_relation
from .generalized_crt_fold_candidate import (
    GeneralizedCRTFoldError,
    _arguments as _fold_arguments,
    _at,
    _bound,
    _canonical_terms,
    _common_terms,
    _lcm_terms,
    _mod,
    _positive_terms,
    _safe,
    _solution_terms,
)
from .ha_canonical_gcd_candidate import is_gcd
from .ha_relational_lcm_candidate import is_lcm


class GeneralizedCRTCompatibilityError(ValueError):
    """A compatibility definition would capture a binder or escape HA."""


def _arguments(*values: tuple[str, str]) -> tuple[str, ...]:
    try:
        result = _fold_arguments(*values)
        if any(value.startswith(("gcomp_", "hag_")) for value in result):
            raise ValueError("generated CRT-compatibility binder captures an argument")
        return result
    except (GeneralizedCRTFoldError, ValueError) as error:
        raise GeneralizedCRTCompatibilityError(str(error)) from error


def _tag(value: str) -> str:
    try:
        return _safe(value)
    except (GeneralizedCRTFoldError, ValueError) as error:
        raise GeneralizedCRTCompatibilityError(str(error)) from error


def _fresh(tag: str, context: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    result = tuple(f"gcomp_{role}_{_tag(tag)}" for role in roles)
    if len(set(result)) != len(result) or set(result) & set(context):
        raise GeneralizedCRTCompatibilityError(
            "generated CRT-compatibility binder captures an argument"
        )
    return result


def _gcd(value: str, left: str, right: str, *, tag: str) -> str:
    return is_gcd(value, left, right, tag=f"gcomp_{_tag(tag)}")


def _pairwise_terms(
    residue_code: str,
    residue_scale: str,
    modulus_code: str,
    modulus_scale: str,
    length: str,
    *,
    tag: str,
    context: tuple[str, ...],
) -> str:
    i, j, a, d, m, n, g = _fresh(
        tag, context, "left_index", "right_index", "left_residue",
        "right_residue", "left_modulus", "right_modulus", "pair_gcd",
    )
    local = context + (i, j, a, d, m, n, g)
    return (
        f"forall {i} {j} {a} {d} {m} {n} {g}. "
        f"({_bound(i, length, tag=f'{tag}_left_bound', context=local)}) -> "
        f"({_bound(j, length, tag=f'{tag}_right_bound', context=local)}) -> "
        f"({_at(residue_code, residue_scale, i, a, tag=f'{tag}_left_residue', context=local)}) -> "
        f"({_at(residue_code, residue_scale, j, d, tag=f'{tag}_right_residue', context=local)}) -> "
        f"({_at(modulus_code, modulus_scale, i, m, tag=f'{tag}_left_modulus', context=local)}) -> "
        f"({_at(modulus_code, modulus_scale, j, n, tag=f'{tag}_right_modulus', context=local)}) -> "
        f"({_gcd(g, m, n, tag=f'{tag}_gcd')}) -> "
        f"({_mod(g, a, d, tag=f'{tag}_result', context=local)})"
    )


def crt_pairwise_compatible_prefix(
    residue_code: str,
    residue_scale: str,
    modulus_code: str,
    modulus_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand actual pairwise residue congruence modulo every relational gcd."""

    arguments = _arguments(
        (residue_code, "residue code"), (residue_scale, "residue scale"),
        (modulus_code, "modulus code"), (modulus_scale, "modulus scale"),
        (length, "prefix length"),
    )
    return _pairwise_terms(*arguments, tag=_tag(tag), context=arguments)


def _merge_terms(
    residue_code: str,
    residue_scale: str,
    modulus_code: str,
    modulus_scale: str,
    length: str,
    *,
    tag: str,
    context: tuple[str, ...],
) -> str:
    i, x, modulus, a, n, g = _fresh(
        tag, context, "merge_index", "merge_solution", "merge_lcm",
        "merge_residue", "merge_modulus", "merge_gcd",
    )
    local = context + (i, x, modulus, a, n, g)
    return (
        f"forall {i} {x} {modulus} {a} {n} {g}. "
        f"({_bound(i, length, tag=f'{tag}_bound', context=local)}) -> "
        f"({_lcm_terms(modulus_code, modulus_scale, i, modulus, tag=f'{tag}_lcm', context=local)}) -> "
        f"({_solution_terms(residue_code, residue_scale, modulus_code, modulus_scale, i, x, tag=f'{tag}_solution', context=local)}) -> "
        f"({_at(residue_code, residue_scale, i, a, tag=f'{tag}_residue', context=local)}) -> "
        f"({_at(modulus_code, modulus_scale, i, n, tag=f'{tag}_modulus', context=local)}) -> "
        f"({_gcd(g, modulus, n, tag=f'{tag}_gcd')}) -> "
        f"({_mod(g, x, a, tag=f'{tag}_result', context=local)})"
    )


def crt_merge_compatible_prefix(
    residue_code: str,
    residue_scale: str,
    modulus_code: str,
    modulus_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand exact gcd compatibility at every actual predecessor-LCM merge."""

    arguments = _arguments(
        (residue_code, "residue code"), (residue_scale, "residue scale"),
        (modulus_code, "modulus code"), (modulus_scale, "modulus scale"),
        (length, "prefix length"),
    )
    return _merge_terms(*arguments, tag=_tag(tag), context=arguments)


def make_generalized_crt_compatibility_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return dependency-ordered, original-kernel-checkable theorem bodies."""

    context = ("r", "s", "b", "c", "l")
    pairs = lambda length, tag: _pairwise_terms(
        "r", "s", "b", "c", length, tag=tag, context=context
    )
    merge = lambda length, tag: _merge_terms(
        "r", "s", "b", "c", length, tag=tag, context=context
    )

    return (
        spec(
            "crt_mod_one_universal",
            f"forall a b. ({_mod('1', 'a', 'b', tag='gcomp_one', context=('a', 'b'))})",
            ("one_mul", "add_comm"),
            (
                "intro a", "intro b", "exists b", "exists a",
                "trans a + b", "congr", "refl", "apply one_mul",
                "trans b + a", "apply add_comm", "congr", "refl", "symm",
                "apply one_mul",
            ),
            "Every pair of natural residues is constructively congruent modulo one.",
        ),
        spec(
            "crt_coprime_divisor_pair",
            f"forall a b d e. ({coprime('a', 'b', tag='gcomp_divisor_source')}) -> "
            "(exists u. a = d * u) -> (exists v. b = e * v) -> "
            f"({coprime('d', 'e', tag='gcomp_divisor_result')})",
            ("multiple_trans",),
            (
                "intro a", "intro b", "intro d", "intro e", "intro hcoprime",
                "intro hd", "intro he", "intro k", "intro hkd", "intro hke",
                "specialize hcoprime k", "apply hcoprime",
                "specialize multiple_trans d", "specialize multiple_trans k",
                "specialize multiple_trans a", "apply multiple_trans", "exact hd", "exact hkd",
                "specialize multiple_trans e", "specialize multiple_trans k",
                "specialize multiple_trans b", "apply multiple_trans", "exact he", "exact hke",
            ),
            "Any divisors of two coprime naturals are themselves constructively coprime.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_empty",
            f"forall r s b c l. l = 0 -> ({pairs('l', 'pairs_empty')})",
            ("le_zero", "succ_ne_zero"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro hzero",
                "intro i", "intro j", "intro a", "intro d", "intro m", "intro n", "intro g",
                "intro hi", "intro hj", "intro ha", "intro hd", "intro hm", "intro hn",
                "intro hg", "exfalso", "rewrite hzero at hi", "have hbad : S i = 0",
                "specialize le_zero (S i)", "apply le_zero", "exact hi",
                "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hbad",
            ),
            "The empty actual residue/modulus list is pairwise gcd-compatible.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_drop_last",
            f"forall r s b c l. ({pairs('S l', 'pairs_drop_source')}) -> "
            f"({pairs('l', 'pairs_drop_result')})",
            ("le_succ",),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro hpairs",
                "intro i", "intro j", "intro a", "intro d", "intro m", "intro n", "intro g",
                "intro hi", "intro hj", "intro ha", "intro hd", "intro hm", "intro hn", "intro hg",
                "specialize hpairs i", "specialize hpairs j", "specialize hpairs a",
                "specialize hpairs d", "specialize hpairs m", "specialize hpairs n",
                "specialize hpairs g", "apply hpairs",
                "specialize le_succ (S i)", "specialize le_succ l", "apply le_succ", "exact hi",
                "specialize le_succ (S j)", "specialize le_succ l", "apply le_succ", "exact hj",
                "exact ha", "exact hd", "exact hm", "exact hn", "exact hg",
            ),
            "Pairwise gcd compatibility of any finite list restricts to its predecessor prefix.",
        ),
        spec(
            "crt_prefix_solution_implies_pairwise_compatible",
            f"forall r s b c l x. "
            f"({_solution_terms('r','s','b','c','l','x',tag='gcomp_necessity_solution',context=('r','s','b','c','l','x'))}) -> "
            f"({_pairwise_terms('r','s','b','c','l',tag='gcomp_necessity_pairs',context=('r','s','b','c','l','x'))})",
            ("crt_common_solution_implies_gcd_compatible",),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro x", "intro hsolution",
                "intro i", "intro j", "intro a", "intro d", "intro m", "intro n", "intro g",
                "intro hi", "intro hj", "intro ha", "intro hd", "intro hm", "intro hn", "intro hg",
                "specialize crt_common_solution_implies_gcd_compatible g",
                "specialize crt_common_solution_implies_gcd_compatible m",
                "specialize crt_common_solution_implies_gcd_compatible n",
                "specialize crt_common_solution_implies_gcd_compatible a",
                "specialize crt_common_solution_implies_gcd_compatible d",
                "specialize crt_common_solution_implies_gcd_compatible x",
                "apply crt_common_solution_implies_gcd_compatible", "exact hg", "split",
                "specialize hsolution i", "specialize hsolution a", "specialize hsolution m",
                "apply hsolution", "exact hi", "exact ha", "exact hm",
                "specialize hsolution j", "specialize hsolution d", "specialize hsolution n",
                "apply hsolution", "exact hj", "exact hd", "exact hn",
            ),
            "Every actual simultaneous solution forces exact pairwise gcd compatibility, including zero and non-coprime moduli.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_last",
            f"forall r s b c l i a d m n g. "
            f"({_pairwise_terms('r','s','b','c','S l',tag='gcomp_last_source',context=('r','s','b','c','l','i','a','d','m','n','g'))}) -> "
            f"({_bound('i','l',tag='gcomp_last_old_bound',context=('r','s','b','c','l','i','a','d','m','n','g'))}) -> "
            f"({_at('r','s','i','a',tag='gcomp_last_old_residue',context=('r','s','b','c','l','i','a','d','m','n','g'))}) -> "
            f"({_at('r','s','l','d',tag='gcomp_last_new_residue',context=('r','s','b','c','l','i','a','d','m','n','g'))}) -> "
            f"({_at('b','c','i','m',tag='gcomp_last_old_modulus',context=('r','s','b','c','l','i','a','d','m','n','g'))}) -> "
            f"({_at('b','c','l','n',tag='gcomp_last_new_modulus',context=('r','s','b','c','l','i','a','d','m','n','g'))}) -> "
            f"({_gcd('g','m','n',tag='last_actual_gcd')}) -> "
            f"({_mod('g','a','d',tag='gcomp_last_result',context=('r','s','b','c','l','i','a','d','m','n','g'))})",
            ("le_succ", "le_refl"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro i", "intro a",
                "intro d", "intro m", "intro n", "intro g", "intro hpairs", "intro hi",
                "intro ha", "intro hd", "intro hm", "intro hn", "intro hg",
                "specialize hpairs i", "specialize hpairs l", "specialize hpairs a",
                "specialize hpairs d", "specialize hpairs m", "specialize hpairs n",
                "specialize hpairs g", "apply hpairs",
                "specialize le_succ (S i)", "specialize le_succ l", "apply le_succ", "exact hi",
                "specialize le_refl (S l)", "exact le_refl", "exact ha", "exact hd",
                "exact hm", "exact hn", "exact hg",
            ),
            "The last residue of a compatible successor list is gcd-compatible with each earlier actual decoded pair.",
        ),
        spec(
            "crt_merge_compatible_prefix_drop_last",
            f"forall r s b c l. ({merge('S l', 'merge_drop_source')}) -> "
            f"({merge('l', 'merge_drop_result')})",
            ("le_succ",),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro hmerge",
                "intro i", "intro x", "intro M", "intro a", "intro n", "intro g",
                "intro hi", "intro hlcm", "intro hx", "intro ha", "intro hn", "intro hg",
                "specialize hmerge i", "specialize hmerge x", "specialize hmerge M",
                "specialize hmerge a", "specialize hmerge n", "specialize hmerge g",
                "apply hmerge", "specialize le_succ (S i)", "specialize le_succ l",
                "apply le_succ", "exact hi", "exact hlcm", "exact hx", "exact ha",
                "exact hn", "exact hg",
            ),
            "The exact operational generalized-CRT merge invariant restricts to any predecessor prefix.",
        ),
        spec(
            "generalized_binary_crt_merge_step",
            f"forall P n x a g. ({_gcd('g','P','n',tag='binary_merge_gcd')}) -> "
            f"({_mod('g','x','a',tag='gcomp_binary_merge_compatible',context=('P','n','x','a','g'))}) -> exists z. "
            f"((({_mod('P','z','x',tag='gcomp_binary_merge_left',context=('P','n','x','a','g','z'))}) /\\ "
            f"({_mod('n','z','a',tag='gcomp_binary_merge_right',context=('P','n','x','a','g','z'))})))",
            ("generalized_binary_crt_sufficient",),
            (
                "intro P", "intro n", "intro x", "intro a", "intro g", "intro hg", "intro hcompat",
                "specialize generalized_binary_crt_sufficient g",
                "specialize generalized_binary_crt_sufficient P",
                "specialize generalized_binary_crt_sufficient n",
                "specialize generalized_binary_crt_sufficient x",
                "specialize generalized_binary_crt_sufficient a",
                "apply generalized_binary_crt_sufficient", "exact hg", "exact hcompat",
            ),
            "Exact gcd compatibility merges two arbitrary natural moduli, including zero, without any coprimality assumption.",
        ),
        spec(
            "crt_merge_compatible_prefix_solution_exists",
            f"forall r s b c l. ({merge('l', 'fold_hypothesis')}) -> exists x. "
            f"({_solution_terms('r','s','b','c','l','x',tag='gcomp_fold_result',context=('r','s','b','c','l','x'))})",
            (
                "crt_prefix_solution_empty", "crt_merge_compatible_prefix_drop_last",
                "crt_prefix_lcm_exists_unique", "beta_at_exists", "gcd_exists_relational",
                "le_refl", "generalized_binary_crt_merge_step",
                "crt_prefix_solution_transport_common_multiple",
                "crt_prefix_solution_successor_intro",
            ),
            (
                "intro r", "intro s", "intro b", "intro c", "induction l",
                "intro hmerge", "exists 0", "specialize crt_prefix_solution_empty r",
                "specialize crt_prefix_solution_empty s", "specialize crt_prefix_solution_empty b",
                "specialize crt_prefix_solution_empty c", "specialize crt_prefix_solution_empty 0",
                "specialize crt_prefix_solution_empty 0", "apply crt_prefix_solution_empty", "refl",
                "intro hmerge",
                f"have hrestricted : {merge('l', 'fold_restricted')}",
                "specialize crt_merge_compatible_prefix_drop_last r",
                "specialize crt_merge_compatible_prefix_drop_last s",
                "specialize crt_merge_compatible_prefix_drop_last b",
                "specialize crt_merge_compatible_prefix_drop_last c",
                "specialize crt_merge_compatible_prefix_drop_last l",
                "apply crt_merge_compatible_prefix_drop_last", "exact hmerge",
                "have hprefix : exists x. "
                f"({_solution_terms('r','s','b','c','l','x',tag='gcomp_fold_old_solution',context=('r','s','b','c','l','x'))})",
                "apply IH", "exact hrestricted", "cases hprefix",
                "have hlcm : exists P. "
                f"(({_lcm_terms('b','c','l','P',tag='gcomp_fold_old_lcm',context=('r','s','b','c','l','x','P'))}) /\\ "
                f"forall z. ({_lcm_terms('b','c','l','z',tag='gcomp_fold_old_lcm_unique',context=('r','s','b','c','l','x','P','z'))}) -> z = P)",
                "specialize crt_prefix_lcm_exists_unique b",
                "specialize crt_prefix_lcm_exists_unique c",
                "specialize crt_prefix_lcm_exists_unique l",
                "exact crt_prefix_lcm_exists_unique", "cases hlcm", "cases hlcm_witness",
                "have hresidue : exists a. "
                f"({_at('r','s','l','a',tag='gcomp_fold_actual_residue',context=('r','s','b','c','l','x','x1','a'))})",
                "specialize beta_at_exists r", "specialize beta_at_exists s",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hresidue",
                "have hmodulus : exists n. "
                f"({_at('b','c','l','n',tag='gcomp_fold_actual_modulus',context=('r','s','b','c','l','x','x1','x2','n'))})",
                "specialize beta_at_exists b", "specialize beta_at_exists c",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hmodulus",
                f"have hgcd : exists g. ({_gcd('g','x1','x3',tag='fold_actual_gcd')})",
                "specialize gcd_exists_relational x1", "specialize gcd_exists_relational x3",
                "exact gcd_exists_relational", "cases hgcd",
                f"have hcompatible : {_mod('x4','x','x2',tag='gcomp_fold_actual_compatible',context=('r','s','b','c','l','x','x1','x2','x3','x4'))}",
                "specialize hmerge l", "specialize hmerge x", "specialize hmerge x1",
                "specialize hmerge x2", "specialize hmerge x3", "specialize hmerge x4",
                "apply hmerge", "specialize le_refl (S l)", "exact le_refl",
                "exact hlcm_witness_left", "exact hprefix_witness", "exact hresidue_witness",
                "exact hmodulus_witness", "exact hgcd_witness",
                "have hmerged : exists z. "
                f"((({_mod('x1','z','x',tag='gcomp_fold_merged_old',context=('r','s','b','c','l','x','x1','x2','x3','x4','z'))}) /\\ "
                f"({_mod('x3','z','x2',tag='gcomp_fold_merged_new',context=('r','s','b','c','l','x','x1','x2','x3','x4','z'))})))",
                "specialize generalized_binary_crt_merge_step x1",
                "specialize generalized_binary_crt_merge_step x3",
                "specialize generalized_binary_crt_merge_step x",
                "specialize generalized_binary_crt_merge_step x2",
                "specialize generalized_binary_crt_merge_step x4",
                "apply generalized_binary_crt_merge_step", "exact hgcd_witness",
                "exact hcompatible", "cases hmerged", "cases hmerged_witness",
                f"have htransported : {_solution_terms('r','s','b','c','l','x5',tag='gcomp_fold_transported',context=('r','s','b','c','l','x','x1','x2','x3','x4','x5'))}",
                "specialize crt_prefix_solution_transport_common_multiple r",
                "specialize crt_prefix_solution_transport_common_multiple s",
                "specialize crt_prefix_solution_transport_common_multiple b",
                "specialize crt_prefix_solution_transport_common_multiple c",
                "specialize crt_prefix_solution_transport_common_multiple l",
                "specialize crt_prefix_solution_transport_common_multiple x1",
                "specialize crt_prefix_solution_transport_common_multiple x",
                "specialize crt_prefix_solution_transport_common_multiple x5",
                "apply crt_prefix_solution_transport_common_multiple",
                "cases hlcm_witness_left", "exact hlcm_witness_left_left",
                "exact hprefix_witness", "exact hmerged_witness_left",
                "exists x5", "specialize crt_prefix_solution_successor_intro r",
                "specialize crt_prefix_solution_successor_intro s",
                "specialize crt_prefix_solution_successor_intro b",
                "specialize crt_prefix_solution_successor_intro c",
                "specialize crt_prefix_solution_successor_intro l",
                "specialize crt_prefix_solution_successor_intro x5",
                "specialize crt_prefix_solution_successor_intro x2",
                "specialize crt_prefix_solution_successor_intro x3",
                "apply crt_prefix_solution_successor_intro", "exact htransported",
                "exact hresidue_witness", "exact hmodulus_witness", "exact hmerged_witness_right",
            ),
            "Every arbitrary finite list, including non-coprime and zero moduli, has a genuine simultaneous solution whenever each exact predecessor-LCM merge is gcd-compatible.",
        ),
        spec(
            "crt_positive_prefix_lcm_nonzero",
            f"forall b c l M. "
            f"({_positive_terms('b','c','l',tag='gcomp_lcm_positive',context=('b','c','l','M'))}) -> "
            f"({_lcm_terms('b','c','l','M',tag='gcomp_lcm_nonzero_source',context=('b','c','l','M'))}) -> ~(M = 0)",
            (
                "beta_product_exists_unique", "crt_positive_moduli_prefix_product_nonzero",
                "crt_prefix_product_common_multiple", "mul_zero_left",
            ),
            (
                "intro b", "intro c", "intro l", "intro M", "intro hpositive", "intro hlcm",
                "intro hzero", "specialize beta_product_exists_unique b",
                "specialize beta_product_exists_unique c", "specialize beta_product_exists_unique l",
                "cases beta_product_exists_unique", "cases beta_product_exists_unique_witness",
                "have hnonzero : ~(x = 0)",
                "specialize crt_positive_moduli_prefix_product_nonzero b",
                "specialize crt_positive_moduli_prefix_product_nonzero c",
                "specialize crt_positive_moduli_prefix_product_nonzero l",
                "specialize crt_positive_moduli_prefix_product_nonzero x",
                "intro hxzero", "apply crt_positive_moduli_prefix_product_nonzero",
                "exact hpositive", "exact beta_product_exists_unique_witness_left", "exact hxzero",
                "cases hlcm", "have hmultiple : exists q. x = M * q",
                "specialize hlcm_right x", "apply hlcm_right",
                "specialize crt_prefix_product_common_multiple b",
                "specialize crt_prefix_product_common_multiple c",
                "specialize crt_prefix_product_common_multiple l",
                "specialize crt_prefix_product_common_multiple x",
                "apply crt_prefix_product_common_multiple",
                "exact beta_product_exists_unique_witness_left", "cases hmultiple",
                "have hxzero : x = 0", "trans M * x1", "exact hmultiple_witness",
                "rewrite hzero", "apply mul_zero_left", "apply hnonzero", "exact hxzero",
            ),
            "The exact universal-property LCM of every finite positive modulus prefix is nonzero, including the empty prefix.",
        ),
        spec(
            "crt_prefix_zero_lcm_solution_unique",
            f"forall r s b c l M x y. "
            f"({_lcm_terms('b','c','l','M',tag='gcomp_zero_lcm_source',context=('r','s','b','c','l','M','x','y'))}) -> M = 0 -> "
            f"({_solution_terms('r','s','b','c','l','x',tag='gcomp_zero_solution_left',context=('r','s','b','c','l','M','x','y'))}) -> "
            f"({_solution_terms('r','s','b','c','l','y',tag='gcomp_zero_solution_right',context=('r','s','b','c','l','M','x','y'))}) -> y = x",
            ("crt_prefix_solutions_congruent_lcm", "mod_eq_zero_iff_eq"),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro M", "intro x",
                "intro y", "intro hlcm", "intro hzero", "intro hx", "intro hy",
                f"have hmod : {_mod('M','y','x',tag='gcomp_zero_mod_actual',context=('r','s','b','c','l','M','x','y'))}",
                "specialize crt_prefix_solutions_congruent_lcm r",
                "specialize crt_prefix_solutions_congruent_lcm s",
                "specialize crt_prefix_solutions_congruent_lcm b",
                "specialize crt_prefix_solutions_congruent_lcm c",
                "specialize crt_prefix_solutions_congruent_lcm l",
                "specialize crt_prefix_solutions_congruent_lcm M",
                "specialize crt_prefix_solutions_congruent_lcm y",
                "specialize crt_prefix_solutions_congruent_lcm x",
                "apply crt_prefix_solutions_congruent_lcm", "exact hlcm", "exact hy", "exact hx",
                "rewrite hzero at hmod", "rewrite hzero at hmod",
                "specialize mod_eq_zero_iff_eq y",
                "specialize mod_eq_zero_iff_eq x", "cases mod_eq_zero_iff_eq",
                "apply mod_eq_zero_iff_eq_left", "exact hmod",
            ),
            "At list LCM zero, every simultaneous solution of an arbitrary decoded congruence system is literally unique.",
        ),
        spec(
            "crt_merge_compatible_prefix_canonical_exists_unique",
            f"forall r s b c l. "
            f"({_positive_terms('b','c','l',tag='gcomp_canonical_positive',context=('r','s','b','c','l'))}) -> "
            f"({_merge_terms('r','s','b','c','l',tag='gcomp_canonical_merge',context=('r','s','b','c','l'))}) -> exists x M. "
            f"(({_canonical_terms('r','s','b','c','l','x','M',tag='gcomp_canonical_chosen',context=('r','s','b','c','l','x','M'))}) /\\ "
            f"forall y. ({_canonical_terms('r','s','b','c','l','y','M',tag='gcomp_canonical_compared',context=('r','s','b','c','l','M','y'))}) -> y = x)",
            (
                "crt_merge_compatible_prefix_solution_exists", "crt_prefix_lcm_exists_unique",
                "crt_positive_prefix_lcm_nonzero", "crt_prefix_solution_canonical_remainder",
                "crt_canonical_prefix_solution_unique",
            ),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro hpositive", "intro hmerge",
                "have hsolution : exists z. "
                f"({_solution_terms('r','s','b','c','l','z',tag='gcomp_canonical_old_solution',context=('r','s','b','c','l','z'))})",
                "specialize crt_merge_compatible_prefix_solution_exists r",
                "specialize crt_merge_compatible_prefix_solution_exists s",
                "specialize crt_merge_compatible_prefix_solution_exists b",
                "specialize crt_merge_compatible_prefix_solution_exists c",
                "specialize crt_merge_compatible_prefix_solution_exists l",
                "apply crt_merge_compatible_prefix_solution_exists", "exact hmerge", "cases hsolution",
                "specialize crt_prefix_lcm_exists_unique b", "specialize crt_prefix_lcm_exists_unique c",
                "specialize crt_prefix_lcm_exists_unique l", "cases crt_prefix_lcm_exists_unique",
                "cases crt_prefix_lcm_exists_unique_witness",
                "have hnonzero : ~(x1 = 0)", "specialize crt_positive_prefix_lcm_nonzero b",
                "specialize crt_positive_prefix_lcm_nonzero c",
                "specialize crt_positive_prefix_lcm_nonzero l",
                "specialize crt_positive_prefix_lcm_nonzero x1", "intro hz",
                "apply crt_positive_prefix_lcm_nonzero", "exact hpositive",
                "exact crt_prefix_lcm_exists_unique_witness_left", "exact hz",
                "have hcanonical : exists z. "
                f"({_canonical_terms('r','s','b','c','l','z','x1',tag='gcomp_canonical_exists_actual',context=('r','s','b','c','l','x','x1','z'))})",
                "specialize crt_prefix_solution_canonical_remainder r",
                "specialize crt_prefix_solution_canonical_remainder s",
                "specialize crt_prefix_solution_canonical_remainder b",
                "specialize crt_prefix_solution_canonical_remainder c",
                "specialize crt_prefix_solution_canonical_remainder l",
                "specialize crt_prefix_solution_canonical_remainder x1",
                "specialize crt_prefix_solution_canonical_remainder x",
                "apply crt_prefix_solution_canonical_remainder", "exact hnonzero",
                "exact crt_prefix_lcm_exists_unique_witness_left", "exact hsolution_witness",
                "cases hcanonical", "exists x2", "exists x1", "split", "exact hcanonical_witness",
                "intro y", "intro hy", "specialize crt_canonical_prefix_solution_unique r",
                "specialize crt_canonical_prefix_solution_unique s",
                "specialize crt_canonical_prefix_solution_unique b",
                "specialize crt_canonical_prefix_solution_unique c",
                "specialize crt_canonical_prefix_solution_unique l",
                "specialize crt_canonical_prefix_solution_unique x1",
                "specialize crt_canonical_prefix_solution_unique x2",
                "specialize crt_canonical_prefix_solution_unique y",
                "apply crt_canonical_prefix_solution_unique", "exact hcanonical_witness", "exact hy",
            ),
            "Every arbitrary finite positive non-coprime congruence system satisfying the exact operational gcd-merge invariant has its genuine LCM and exactly one strictly bounded solution.",
        ),
        spec(
            "crt_balanced_bezout_scale",
            "forall k a b g xp yp xn yn. "
            "a * xp + b * yp = g + (a * xn + b * yn) -> "
            "(k * a) * xp + (k * b) * yp = "
            "k * g + ((k * a) * xn + (k * b) * yn)",
            ("mul_add", "mul_assoc"),
            (
                "intro k", "intro a", "intro b", "intro g", "intro xp", "intro yp",
                "intro xn", "intro yn", "intro hbezout",
                "trans k * (a * xp + b * yp)", "symm",
                "trans k * (a * xp) + k * (b * yp)", "apply mul_add",
                "congr", "symm", "apply mul_assoc", "symm", "apply mul_assoc",
                "rewrite hbezout",
                "trans k * g + k * (a * xn + b * yn)", "apply mul_add",
                "congr", "refl", "trans k * (a * xn) + k * (b * yn)",
                "apply mul_add", "congr", "symm", "apply mul_assoc", "symm",
                "apply mul_assoc",
            ),
            "Multiplying a subtraction-free balanced Bezout equation preserves all four witnessed natural coefficients.",
        ),
        spec(
            "crt_is_gcd_scale",
            f"forall k a b g A B G. A = k * a -> B = k * b -> G = k * g -> "
            f"({_gcd('g','a','b',tag='gcd_scale_source')}) -> "
            f"({_gcd('G','A','B',tag='gcd_scale_result')})",
            (
                "is_gcd_dvd_left", "is_gcd_dvd_right", "mul_assoc",
                "gcd_balanced_bezout_exists", "is_gcd_unique",
                "crt_balanced_bezout_scale", "common_divisor_divides_balanced_result",
            ),
            (
                "intro k", "intro a", "intro b", "intro g", "intro A", "intro B",
                "intro G", "intro hA", "intro hB", "intro hG", "intro hg",
                "have hleft : exists q. a = g * q", "specialize is_gcd_dvd_left g",
                "specialize is_gcd_dvd_left a", "specialize is_gcd_dvd_left b",
                "apply is_gcd_dvd_left", "exact hg", "cases hleft",
                "have hright : exists q. b = g * q", "specialize is_gcd_dvd_right g",
                "specialize is_gcd_dvd_right a", "specialize is_gcd_dvd_right b",
                "apply is_gcd_dvd_right", "exact hg", "cases hright",
                "specialize gcd_balanced_bezout_exists a",
                "specialize gcd_balanced_bezout_exists b", "cases gcd_balanced_bezout_exists",
                "cases gcd_balanced_bezout_exists_witness",
                "have heq : x2 = g", "specialize is_gcd_unique x2",
                "specialize is_gcd_unique g", "specialize is_gcd_unique a",
                "specialize is_gcd_unique b", "apply is_gcd_unique",
                "exact gcd_balanced_bezout_exists_witness_left", "exact hg",
                "cases gcd_balanced_bezout_exists_witness_right",
                "cases gcd_balanced_bezout_exists_witness_right_witness",
                "cases gcd_balanced_bezout_exists_witness_right_witness_witness",
                "cases gcd_balanced_bezout_exists_witness_right_witness_witness_witness",
                "rewrite heq at gcd_balanced_bezout_exists_witness_right_witness_witness_witness_witness",
                "have hscaled : A * x3 + B * x4 = G + (A * x5 + B * x6)",
                "rewrite hA", "rewrite hA", "rewrite hB", "rewrite hB", "rewrite hG",
                "specialize crt_balanced_bezout_scale k",
                "specialize crt_balanced_bezout_scale a",
                "specialize crt_balanced_bezout_scale b",
                "specialize crt_balanced_bezout_scale g",
                "specialize crt_balanced_bezout_scale x3",
                "specialize crt_balanced_bezout_scale x4",
                "specialize crt_balanced_bezout_scale x5",
                "specialize crt_balanced_bezout_scale x6",
                "apply crt_balanced_bezout_scale",
                "exact gcd_balanced_bezout_exists_witness_right_witness_witness_witness_witness",
                "split", "split", "exists x", "rewrite hA", "rewrite hG",
                "rewrite hleft_witness", "symm", "apply mul_assoc",
                "exists x1", "rewrite hB", "rewrite hG", "rewrite hright_witness",
                "symm", "apply mul_assoc", "intro d", "intro hdA", "intro hdB",
                "specialize common_divisor_divides_balanced_result d",
                "specialize common_divisor_divides_balanced_result A",
                "specialize common_divisor_divides_balanced_result B",
                "specialize common_divisor_divides_balanced_result G",
                "specialize common_divisor_divides_balanced_result x3",
                "specialize common_divisor_divides_balanced_result x4",
                "specialize common_divisor_divides_balanced_result x5",
                "specialize common_divisor_divides_balanced_result x6",
                "apply common_divisor_divides_balanced_result", "exact hdA", "exact hdB",
                "exact hscaled",
            ),
            "Every common natural scale, including zero, transports the full relational greatest-common-divisor specification constructively.",
        ),
        spec(
            "crt_is_gcd_coprime_factor_remove",
            f"forall s a n g A. A = s * a -> "
            f"({coprime('s','n',tag='gcomp_remove_coprime')}) -> "
            f"({_gcd('g','a','n',tag='remove_source')}) -> "
            f"({_gcd('g','A','n',tag='remove_result')})",
            (
                "is_gcd_dvd_left", "is_gcd_dvd_right", "mul_comm", "mul_assoc",
                "multiple_refl", "crt_coprime_divisor_pair", "coprime_symm",
                "gauss_coprime_cancel", "is_gcd_greatest",
            ),
            (
                "intro s", "intro a", "intro n", "intro g", "intro A", "intro hA",
                "intro hcoprime", "intro hg", "split", "split",
                "specialize is_gcd_dvd_left g", "specialize is_gcd_dvd_left a",
                "specialize is_gcd_dvd_left n", "have hdivides : exists q. a = g * q",
                "apply is_gcd_dvd_left", "exact hg", "cases hdivides", "exists s * x",
                "rewrite hA", "rewrite hdivides_witness",
                "trans (s * g) * x", "symm", "apply mul_assoc",
                "trans (g * s) * x", "congr", "apply mul_comm", "refl", "apply mul_assoc",
                "specialize is_gcd_dvd_right g", "specialize is_gcd_dvd_right a",
                "specialize is_gcd_dvd_right n", "apply is_gcd_dvd_right", "exact hg",
                "intro d", "intro hdA", "intro hdn",
                f"have hforward : {coprime('s','d',tag='gcomp_remove_forward')}",
                "specialize crt_coprime_divisor_pair s",
                "specialize crt_coprime_divisor_pair n",
                "specialize crt_coprime_divisor_pair s",
                "specialize crt_coprime_divisor_pair d",
                "apply crt_coprime_divisor_pair", "exact hcoprime",
                "specialize multiple_refl s", "exact multiple_refl", "exact hdn",
                f"have hreverse : {coprime('d','s',tag='gcomp_remove_reverse')}",
                "specialize coprime_symm s", "specialize coprime_symm d",
                "apply coprime_symm", "exact hforward",
                "have hda : exists q. a = d * q", "specialize gauss_coprime_cancel d",
                "specialize gauss_coprime_cancel s", "specialize gauss_coprime_cancel a",
                "apply gauss_coprime_cancel", "exact hreverse",
                "cases hdA", "exists x", "rewrite hA at hdA_witness", "exact hdA_witness",
                "specialize is_gcd_greatest g", "specialize is_gcd_greatest a",
                "specialize is_gcd_greatest n", "specialize is_gcd_greatest d",
                "apply is_gcd_greatest", "exact hg", "exact hda", "exact hdn",
            ),
            "A multiplier coprime to the fixed right input does not change the full relational gcd of the left input.",
        ),
        spec(
            "crt_product_witness",
            "forall a b. exists p. p = a * b",
            (),
            ("intro a", "intro b", "exists a * b", "refl"),
            "Every natural product has an explicit first-order value witness without adding multiplication as a new operation.",
        ),
        spec(
            "crt_is_gcd_coprime_product",
            f"forall a b n ga gb P T. ~(n = 0) -> T = a * b -> P = ga * gb -> "
            f"({coprime('a','b',tag='gcomp_product_coprime')}) -> "
            f"({_gcd('ga','a','n',tag='product_left')}) -> "
            f"({_gcd('gb','b','n',tag='product_right')}) -> "
            f"({_gcd('P','T','n',tag='product_result')})",
            (
                "is_gcd_dvd_left", "is_gcd_dvd_right", "factor_nonzero_left",
                "is_gcd_quotients_coprime_nonzero", "multiple_refl",
                "crt_coprime_divisor_pair", "canonical_gcd_exists",
                "is_gcd_symm", "crt_is_gcd_coprime_factor_remove",
                "is_gcd_unique", "crt_product_witness", "mul_assoc", "crt_is_gcd_scale",
            ),
            (
                "intro a", "intro b", "intro n", "intro ga", "intro gb", "intro P", "intro T",
                "intro hnzero", "intro hT", "intro hP", "intro hab", "intro hga", "intro hgb",
                "have haquot : exists q. a = ga * q", "specialize is_gcd_dvd_left ga",
                "specialize is_gcd_dvd_left a", "specialize is_gcd_dvd_left n",
                "apply is_gcd_dvd_left", "exact hga", "cases haquot",
                "have hnquot : exists q. n = ga * q", "specialize is_gcd_dvd_right ga",
                "specialize is_gcd_dvd_right a", "specialize is_gcd_dvd_right n",
                "apply is_gcd_dvd_right", "exact hga", "cases hnquot",
                "have hganzero : ~(ga = 0)", "specialize factor_nonzero_left n",
                "specialize factor_nonzero_left ga", "specialize factor_nonzero_left x1",
                "intro hzero", "apply factor_nonzero_left", "exact hnzero",
                "exact hnquot_witness", "exact hzero",
                f"have hquotcop : {coprime('x','x1',tag='gcomp_product_quotients')}",
                "specialize is_gcd_quotients_coprime_nonzero ga",
                "specialize is_gcd_quotients_coprime_nonzero a",
                "specialize is_gcd_quotients_coprime_nonzero n",
                "specialize is_gcd_quotients_coprime_nonzero x",
                "specialize is_gcd_quotients_coprime_nonzero x1",
                "apply is_gcd_quotients_coprime_nonzero", "exact hga", "exact hganzero",
                "exact haquot_witness", "exact hnquot_witness",
                f"have hgbcop : {coprime('ga','b',tag='gcomp_product_scale_coprime')}",
                "specialize crt_coprime_divisor_pair a",
                "specialize crt_coprime_divisor_pair b",
                "specialize crt_coprime_divisor_pair ga",
                "specialize crt_coprime_divisor_pair b",
                "apply crt_coprime_divisor_pair", "exact hab",
                "exists x", "exact haquot_witness", "specialize multiple_refl b", "exact multiple_refl",
                "specialize canonical_gcd_exists b", "specialize canonical_gcd_exists x1",
                "cases canonical_gcd_exists",
                f"have hswap : {_gcd('x2','x1','b',tag='product_intermediate_swap')}",
                "specialize is_gcd_symm x2", "specialize is_gcd_symm b",
                "specialize is_gcd_symm x1", "apply is_gcd_symm",
                "exact canonical_gcd_exists_witness",
                f"have hrestore : {_gcd('x2','n','b',tag='product_restore_scaled')}",
                "specialize crt_is_gcd_coprime_factor_remove ga",
                "specialize crt_is_gcd_coprime_factor_remove x1",
                "specialize crt_is_gcd_coprime_factor_remove b",
                "specialize crt_is_gcd_coprime_factor_remove x2",
                "specialize crt_is_gcd_coprime_factor_remove n",
                "apply crt_is_gcd_coprime_factor_remove", "exact hnquot_witness",
                "exact hgbcop", "exact hswap",
                f"have hback : {_gcd('x2','b','n',tag='product_restore_back')}",
                "specialize is_gcd_symm x2", "specialize is_gcd_symm n",
                "specialize is_gcd_symm b", "apply is_gcd_symm", "exact hrestore",
                "have heq : x2 = gb", "specialize is_gcd_unique x2",
                "specialize is_gcd_unique gb", "specialize is_gcd_unique b",
                "specialize is_gcd_unique n", "apply is_gcd_unique", "exact hback", "exact hgb",
                "specialize crt_product_witness x", "specialize crt_product_witness b",
                "cases crt_product_witness",
                f"have hbase : {_gcd('x2','x3','x1',tag='product_base_temporary')}",
                "specialize crt_is_gcd_coprime_factor_remove x",
                "specialize crt_is_gcd_coprime_factor_remove b",
                "specialize crt_is_gcd_coprime_factor_remove x1",
                "specialize crt_is_gcd_coprime_factor_remove x2",
                "specialize crt_is_gcd_coprime_factor_remove x3",
                "apply crt_is_gcd_coprime_factor_remove",
                "exact crt_product_witness_witness",
                "exact hquotcop", "exact canonical_gcd_exists_witness",
                "specialize crt_is_gcd_scale ga", "specialize crt_is_gcd_scale x3",
                "specialize crt_is_gcd_scale x1", "specialize crt_is_gcd_scale x2",
                "specialize crt_is_gcd_scale T", "specialize crt_is_gcd_scale n",
                "specialize crt_is_gcd_scale P", "apply crt_is_gcd_scale",
                "trans a * b", "exact hT", "rewrite haquot_witness",
                "trans ga * (x * b)", "apply mul_assoc",
                "rewrite crt_product_witness_witness", "refl",
                "exact hnquot_witness", "rewrite heq", "exact hP", "exact hbase",
            ),
            "For coprime natural factors and any nonzero comparison input, the gcd of their product is exactly the product of their individual relational gcd values.",
        ),
        spec(
            "crt_lcm_gcd_cofactor_product",
            f"forall a b g A B L. ~(g = 0) -> a = g * A -> b = g * B -> "
            f"({_gcd('g','a','b',tag='lcm_factor_gcd')}) -> "
            f"({is_lcm('L','a','b',tag='gcomp_lcm_factor_source')}) -> "
            "L = g * (A * B)",
            ("gcd_lcm_product", "mul_assoc", "mul_comm", "mul_left_cancel_nonzero"),
            (
                "intro a", "intro b", "intro g", "intro A", "intro B", "intro L",
                "intro hnonzero", "intro ha", "intro hb", "intro hg", "intro hlcm",
                "have hproduct : g * L = a * b", "specialize gcd_lcm_product g",
                "specialize gcd_lcm_product L", "specialize gcd_lcm_product a",
                "specialize gcd_lcm_product b", "apply gcd_lcm_product", "exact hg", "exact hlcm",
                "rewrite ha at hproduct", "rewrite hb at hproduct",
                "have hshuffle : (g * A) * (g * B) = g * (g * (A * B))",
                "simp [mul_assoc, mul_comm]", "rewrite hshuffle at hproduct",
                "specialize mul_left_cancel_nonzero g",
                "specialize mul_left_cancel_nonzero L",
                "specialize mul_left_cancel_nonzero (g * (A * B))",
                "apply mul_left_cancel_nonzero", "exact hnonzero", "exact hproduct",
            ),
            "For a nonzero relational gcd, the actual binary LCM is exactly its gcd times the product of the two coprime cofactors.",
        ),
        spec(
            "crt_gcd_scaled_coprime_component",
            f"forall k n d K N a ga A G. k = d * K -> n = d * N -> "
            f"A = k * a -> G = d * ga -> "
            f"({coprime('K','N',tag='gcomp_scaled_component_coprime')}) -> "
            f"({_gcd('ga','a','N',tag='scaled_component_base')}) -> "
            f"({_gcd('G','A','n',tag='scaled_component_result')})",
            (
                "crt_product_witness", "crt_is_gcd_coprime_factor_remove",
                "mul_assoc", "crt_is_gcd_scale",
            ),
            (
                "intro k", "intro n", "intro d", "intro K", "intro N", "intro a",
                "intro ga", "intro A", "intro G", "intro hk", "intro hn", "intro hA",
                "intro hG", "intro hcoprime", "intro hga",
                "specialize crt_product_witness K", "specialize crt_product_witness a",
                "cases crt_product_witness",
                f"have hbase : {_gcd('ga','x','N',tag='scaled_component_coprime_product')}",
                "specialize crt_is_gcd_coprime_factor_remove K",
                "specialize crt_is_gcd_coprime_factor_remove a",
                "specialize crt_is_gcd_coprime_factor_remove N",
                "specialize crt_is_gcd_coprime_factor_remove ga",
                "specialize crt_is_gcd_coprime_factor_remove x",
                "apply crt_is_gcd_coprime_factor_remove", "exact crt_product_witness_witness",
                "exact hcoprime", "exact hga",
                "specialize crt_is_gcd_scale d", "specialize crt_is_gcd_scale x",
                "specialize crt_is_gcd_scale N", "specialize crt_is_gcd_scale ga",
                "specialize crt_is_gcd_scale A", "specialize crt_is_gcd_scale n",
                "specialize crt_is_gcd_scale G", "apply crt_is_gcd_scale",
                "trans k * a", "exact hA", "rewrite hk", "trans d * (K * a)",
                "apply mul_assoc", "rewrite crt_product_witness_witness", "refl",
                "exact hn", "exact hG", "exact hbase",
            ),
            "After factoring a common divisor from a multiplier and comparison input, the gcd is exactly that divisor times the gcd of the remaining coprime component.",
        ),
        spec(
            "crt_gcd_monotone_under_divisibility",
            f"forall a b n ga gb. (exists q. b = a * q) -> "
            f"({_gcd('ga','a','n',tag='monotone_small')}) -> "
            f"({_gcd('gb','b','n',tag='monotone_large')}) -> exists q. gb = ga * q",
            ("is_gcd_dvd_left", "is_gcd_dvd_right", "multiple_trans", "is_gcd_greatest"),
            (
                "intro a", "intro b", "intro n", "intro ga", "intro gb", "intro hab",
                "intro hga", "intro hgb", "specialize is_gcd_greatest gb",
                "specialize is_gcd_greatest b", "specialize is_gcd_greatest n",
                "specialize is_gcd_greatest ga", "apply is_gcd_greatest", "exact hgb",
                "specialize multiple_trans a", "specialize multiple_trans ga",
                "specialize multiple_trans b", "apply multiple_trans", "exact hab",
                "specialize is_gcd_dvd_left ga", "specialize is_gcd_dvd_left a",
                "specialize is_gcd_dvd_left n", "apply is_gcd_dvd_left", "exact hga",
                "specialize is_gcd_dvd_right ga", "specialize is_gcd_dvd_right a",
                "specialize is_gcd_dvd_right n", "apply is_gcd_dvd_right", "exact hga",
            ),
            "A divisibility relation between inputs transports monotonically to their relational gcd values with any fixed natural, including zero.",
        ),
        spec(
            "crt_gcd_lcm_distributes_divisibility",
            f"forall a b n L ga gb g. (exists q. b = a * q) -> "
            f"({is_lcm('L','a','b',tag='gcomp_distribute_lcm')}) -> "
            f"({_gcd('ga','a','n',tag='distribute_small')}) -> "
            f"({_gcd('gb','b','n',tag='distribute_large')}) -> "
            f"({_gcd('g','L','n',tag='distribute_result_gcd')}) -> "
            f"({is_lcm('g','ga','gb',tag='gcomp_distribute_result_lcm')})",
            (
                "is_lcm_of_dvd", "is_lcm_unique", "is_gcd_unique",
                "crt_gcd_monotone_under_divisibility",
            ),
            (
                "intro a", "intro b", "intro n", "intro L", "intro ga", "intro gb",
                "intro g", "intro hab", "intro hL", "intro hga", "intro hgb", "intro hg",
                "have hLeq : L = b", "specialize is_lcm_unique L",
                "specialize is_lcm_unique b", "specialize is_lcm_unique a",
                "specialize is_lcm_unique b", "apply is_lcm_unique", "exact hL",
                "specialize is_lcm_of_dvd a", "specialize is_lcm_of_dvd b",
                "apply is_lcm_of_dvd", "exact hab",
                "rewrite hLeq at hg", "rewrite hLeq at hg",
                "have hgeq : g = gb", "specialize is_gcd_unique g",
                "specialize is_gcd_unique gb", "specialize is_gcd_unique b",
                "specialize is_gcd_unique n", "apply is_gcd_unique", "exact hg", "exact hgb",
                "rewrite hgeq", "rewrite hgeq", "rewrite hgeq",
                "specialize is_lcm_of_dvd ga", "specialize is_lcm_of_dvd gb",
                "apply is_lcm_of_dvd", "specialize crt_gcd_monotone_under_divisibility a",
                "specialize crt_gcd_monotone_under_divisibility b",
                "specialize crt_gcd_monotone_under_divisibility n",
                "specialize crt_gcd_monotone_under_divisibility ga",
                "specialize crt_gcd_monotone_under_divisibility gb",
                "apply crt_gcd_monotone_under_divisibility", "exact hab", "exact hga", "exact hgb",
            ),
            "GCD genuinely distributes over binary LCM whenever one modulus divides the other, including arbitrary zero inputs.",
        ),
        spec(
            "crt_merge_compatible_prefix_implies_pairwise_compatible",
            f"forall r s b c l. ({merge('l', 'merge_implies_pairwise_source')}) -> "
            f"({pairs('l', 'merge_implies_pairwise_result')})",
            (
                "crt_merge_compatible_prefix_solution_exists",
                "crt_prefix_solution_implies_pairwise_compatible",
            ),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro hmerge",
                "specialize crt_merge_compatible_prefix_solution_exists r",
                "specialize crt_merge_compatible_prefix_solution_exists s",
                "specialize crt_merge_compatible_prefix_solution_exists b",
                "specialize crt_merge_compatible_prefix_solution_exists c",
                "specialize crt_merge_compatible_prefix_solution_exists l",
                "have hsolution : exists x. "
                f"({_solution_terms('r','s','b','c','l','x',tag='gcomp_implies_actual_solution',context=('r','s','b','c','l','x'))})",
                "apply crt_merge_compatible_prefix_solution_exists", "exact hmerge",
                "cases hsolution", "specialize crt_prefix_solution_implies_pairwise_compatible r",
                "specialize crt_prefix_solution_implies_pairwise_compatible s",
                "specialize crt_prefix_solution_implies_pairwise_compatible b",
                "specialize crt_prefix_solution_implies_pairwise_compatible c",
                "specialize crt_prefix_solution_implies_pairwise_compatible l",
                "specialize crt_prefix_solution_implies_pairwise_compatible x",
                "apply crt_prefix_solution_implies_pairwise_compatible", "exact hsolution_witness",
            ),
            "The operational predecessor-LCM merge invariant constructively implies exact pairwise gcd compatibility; the converse is not assumed.",
        ),
        spec(
            "crt_pairwise_compatible_dominating_last_solution",
            f"forall r s b c l a M. "
            f"({_pairwise_terms('r','s','b','c','S l',tag='dominating_pairs',context=('r','s','b','c','l','a','M'))}) -> "
            f"({_at('r','s','l','a',tag='dominating_residue',context=('r','s','b','c','l','a','M'))}) -> "
            f"({_at('b','c','l','M',tag='dominating_modulus',context=('r','s','b','c','l','a','M'))}) -> "
            f"({_common_terms('b','c','l','M',tag='dominating_common',context=('r','s','b','c','l','a','M'))}) -> "
            f"({_solution_terms('r','s','b','c','S l','a',tag='dominating_solution',context=('r','s','b','c','l','a','M'))})",
            (
                "crt_prefix_solution_successor_intro", "is_gcd_of_dvd",
                "crt_pairwise_compatible_prefix_last", "mod_eq_symm", "mod_eq_refl",
            ),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro a",
                "intro M", "intro hpairs", "intro ha", "intro hM", "intro hcommon",
                "specialize crt_prefix_solution_successor_intro r",
                "specialize crt_prefix_solution_successor_intro s",
                "specialize crt_prefix_solution_successor_intro b",
                "specialize crt_prefix_solution_successor_intro c",
                "specialize crt_prefix_solution_successor_intro l",
                "specialize crt_prefix_solution_successor_intro a",
                "specialize crt_prefix_solution_successor_intro a",
                "specialize crt_prefix_solution_successor_intro M",
                "apply crt_prefix_solution_successor_intro", "intro i", "intro d",
                "intro m", "intro hi", "intro hd", "intro hm",
                f"have hg : {_gcd('m','m','M',tag='dominating_actual_gcd')}",
                "specialize is_gcd_of_dvd m", "specialize is_gcd_of_dvd M",
                "apply is_gcd_of_dvd", "specialize hcommon i", "specialize hcommon m",
                "apply hcommon", "exact hi", "exact hm",
                "specialize mod_eq_symm m", "specialize mod_eq_symm d",
                "specialize mod_eq_symm a", "apply mod_eq_symm",
                "specialize crt_pairwise_compatible_prefix_last r",
                "specialize crt_pairwise_compatible_prefix_last s",
                "specialize crt_pairwise_compatible_prefix_last b",
                "specialize crt_pairwise_compatible_prefix_last c",
                "specialize crt_pairwise_compatible_prefix_last l",
                "specialize crt_pairwise_compatible_prefix_last i",
                "specialize crt_pairwise_compatible_prefix_last d",
                "specialize crt_pairwise_compatible_prefix_last a",
                "specialize crt_pairwise_compatible_prefix_last m",
                "specialize crt_pairwise_compatible_prefix_last M",
                "specialize crt_pairwise_compatible_prefix_last m",
                "apply crt_pairwise_compatible_prefix_last", "exact hpairs", "exact hi",
                "exact hd", "exact ha", "exact hm", "exact hM", "exact hg",
                "exact ha", "exact hM", "specialize mod_eq_refl M",
                "specialize mod_eq_refl a", "exact mod_eq_refl",
            ),
            "Whenever the last modulus is an actual common multiple of all predecessors, exact pairwise gcd compatibility makes the last residue itself a simultaneous solution, including zero and non-coprime moduli.",
        ),
        spec(
            "crt_pairwise_compatible_dominating_last_canonical_exists_unique",
            f"forall r s b c l a M. "
            f"({_positive_terms('b','c','S l',tag='dominating_canonical_positive',context=('r','s','b','c','l','a','M'))}) -> "
            f"({_pairwise_terms('r','s','b','c','S l',tag='dominating_canonical_pairs',context=('r','s','b','c','l','a','M'))}) -> "
            f"({_at('r','s','l','a',tag='dominating_canonical_residue',context=('r','s','b','c','l','a','M'))}) -> "
            f"({_at('b','c','l','M',tag='dominating_canonical_modulus',context=('r','s','b','c','l','a','M'))}) -> "
            f"({_common_terms('b','c','l','M',tag='dominating_canonical_common',context=('r','s','b','c','l','a','M'))}) -> exists x L. "
            f"(({_canonical_terms('r','s','b','c','S l','x','L',tag='dominating_canonical_chosen',context=('r','s','b','c','l','a','M','x','L'))}) /\\ "
            f"forall y. ({_canonical_terms('r','s','b','c','S l','y','L',tag='dominating_canonical_compared',context=('r','s','b','c','l','a','M','L','y'))}) -> y = x)",
            (
                "crt_pairwise_compatible_dominating_last_solution",
                "crt_prefix_lcm_exists_unique", "crt_positive_prefix_lcm_nonzero",
                "crt_prefix_solution_canonical_remainder",
                "crt_canonical_prefix_solution_unique",
            ),
            (
                "intro r", "intro s", "intro b", "intro c", "intro l", "intro a",
                "intro M", "intro hpositive", "intro hpairs", "intro ha", "intro hM",
                "intro hcommon", "specialize crt_prefix_lcm_exists_unique b",
                "specialize crt_prefix_lcm_exists_unique c",
                "specialize crt_prefix_lcm_exists_unique (S l)",
                "cases crt_prefix_lcm_exists_unique",
                "cases crt_prefix_lcm_exists_unique_witness",
                "have hnonzero : ~(x = 0)",
                "specialize crt_positive_prefix_lcm_nonzero b",
                "specialize crt_positive_prefix_lcm_nonzero c",
                "specialize crt_positive_prefix_lcm_nonzero (S l)",
                "specialize crt_positive_prefix_lcm_nonzero x", "intro hz",
                "apply crt_positive_prefix_lcm_nonzero", "exact hpositive",
                "exact crt_prefix_lcm_exists_unique_witness_left", "exact hz",
                "have hcanonical : exists z. "
                f"({_canonical_terms('r','s','b','c','S l','z','x',tag='dominating_canonical_actual',context=('r','s','b','c','l','a','M','x','z'))})",
                "specialize crt_prefix_solution_canonical_remainder r",
                "specialize crt_prefix_solution_canonical_remainder s",
                "specialize crt_prefix_solution_canonical_remainder b",
                "specialize crt_prefix_solution_canonical_remainder c",
                "specialize crt_prefix_solution_canonical_remainder (S l)",
                "specialize crt_prefix_solution_canonical_remainder x",
                "specialize crt_prefix_solution_canonical_remainder a",
                "apply crt_prefix_solution_canonical_remainder", "exact hnonzero",
                "exact crt_prefix_lcm_exists_unique_witness_left",
                "specialize crt_pairwise_compatible_dominating_last_solution r",
                "specialize crt_pairwise_compatible_dominating_last_solution s",
                "specialize crt_pairwise_compatible_dominating_last_solution b",
                "specialize crt_pairwise_compatible_dominating_last_solution c",
                "specialize crt_pairwise_compatible_dominating_last_solution l",
                "specialize crt_pairwise_compatible_dominating_last_solution a",
                "specialize crt_pairwise_compatible_dominating_last_solution M",
                "apply crt_pairwise_compatible_dominating_last_solution", "exact hpairs",
                "exact ha", "exact hM", "exact hcommon", "cases hcanonical",
                "exists x1", "exists x", "split", "exact hcanonical_witness",
                "intro y", "intro hy", "specialize crt_canonical_prefix_solution_unique r",
                "specialize crt_canonical_prefix_solution_unique s",
                "specialize crt_canonical_prefix_solution_unique b",
                "specialize crt_canonical_prefix_solution_unique c",
                "specialize crt_canonical_prefix_solution_unique (S l)",
                "specialize crt_canonical_prefix_solution_unique x",
                "specialize crt_canonical_prefix_solution_unique x1",
                "specialize crt_canonical_prefix_solution_unique y",
                "apply crt_canonical_prefix_solution_unique", "exact hcanonical_witness",
                "exact hy",
            ),
            "Every positive pairwise gcd-compatible successor list whose last modulus dominates all predecessors has its exact list LCM and a unique strictly bounded simultaneous solution without assuming pairwise coprimality or the stronger merge invariant.",
        ),
    )


__all__ = (
    "GeneralizedCRTCompatibilityError",
    "crt_merge_compatible_prefix",
    "crt_pairwise_compatible_prefix",
    "make_generalized_crt_compatibility_candidate_theorems",
)
