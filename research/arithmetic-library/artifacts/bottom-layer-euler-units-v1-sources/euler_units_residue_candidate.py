"""Actual modular-unit multiplier permutations for the Euler theorem.

All relations are conservative first-order HA abbreviations.  These additive
candidate bodies use the immutable v30 parent; this module does not enroll
theorems, change the kernel, or confer checked-use authority.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from ..kernel.formulas import parse_formula_in_context
from ..kernel.terms import parse_term_in_context, pretty_term
from .euler_totient_count_candidate import _call, _cop, _intro, _lt
from .finite_fold_surface import _identifier
from .finite_permutation_theorems import bounded_prefix, injective_prefix, permutation_prefix
from .finite_sum_theorems import _at


def _mod(m: str, a: str, b: str, tag: str) -> str:
    u, v = f"eu_mod_left_{tag}", f"eu_mod_right_{tag}"
    return f"exists {u} {v}. ({a}) + ({m}) * {u} = ({b}) + ({m}) * {v}"


def _unit(a: str, m: str, tag: str) -> str:
    b = f"eu_inverse_{tag}"
    return f"({_lt('1',m,tag='eu_'+tag+'_domain')}) /\\ exists {b}. " \
        f"({_lt(b,m,tag='eu_'+tag+'_bound')}) /\\ ({_mod(m,f'({a})*{b}','1',tag+'_inverse')})"


def _map(a: str, m: str, b: str, c: str, l: str, tag: str) -> str:
    i, r = f"eu_index_{tag}", f"eu_residue_{tag}"
    return f"forall {i}. ({_lt(i,l,tag='eu_'+tag+'_index')}) -> exists {r}. " \
        f"({_at(b,c,i,r,tag='eu_'+tag+'_at')}) /\\ " \
        f"(({_lt(r,m,tag='eu_'+tag+'_bound')}) /\\ ({_mod(m,f'({a})*{i}',r,tag+'_mod')}))"


def _checked(builder: Callable[..., str], arguments: tuple[str, ...], tag: str, variables: tuple[str, ...] | None = None) -> str:
    _identifier(tag, "Euler-unit definition tag")
    if variables is None:
        context = tuple(dict.fromkeys(_identifier(argument, "Euler-unit definition argument") for argument in arguments))
    else:
        if not isinstance(variables, tuple) or not variables:
            raise ValueError("Euler-unit context must be a nonempty tuple")
        context = tuple(_identifier(variable, "Euler-unit context variable") for variable in variables)
        if len(set(context)) != len(context):
            raise ValueError("Euler-unit context variables must be distinct")
    terms = tuple(parse_term_in_context(argument, list(context)) for argument in arguments)
    sources = tuple("(" + pretty_term(term, list(context)).replace("·", "*") + ")" for term in terms)
    formula = builder(*sources, tag)
    binders = {name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", formula) for name in clause.split()}
    if binders.intersection(context):
        raise ValueError("Euler-unit definition binder captures a context variable")
    parse_formula_in_context(formula, list(context))
    return formula


def modular_unit_relation(value: str, modulus: str, *, tag: str, variables: tuple[str, ...] | None = None) -> str:
    """Exactly m>1 and an actual inverse b<m with a*b congruent to one."""
    return _checked(_unit, (value, modulus), tag, variables)


def unit_multiplier_prefix_relation(multiplier: str, modulus: str, code: str, scale: str, length: str, *, tag: str, variables: tuple[str, ...] | None = None) -> str:
    """Actual canonical residues of a*i, at every index 0<=i<length."""
    return _checked(_map, (multiplier, modulus, code, scale, length), tag, variables)


def _scalar_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "euler_coprime_mod_transport",
            f"forall m a b. ({_cop('a','m',tag='eu_transport_old')}) -> ({_mod('m','a','b','transport')}) -> ({_cop('b','m',tag='eu_transport_new')})",
            ("totient_coprime_periodic", "add_comm"),
            (*_intro("m","a","b","hc","hmod"), "cases hmod", "cases hmod_witness",
             f"have hp : ({_cop('m*x+a','m',tag='eu_transport_periodic')})",
             "specialize totient_coprime_periodic m", "specialize totient_coprime_periodic x", "specialize totient_coprime_periodic a",
             "cases totient_coprime_periodic", "apply totient_coprime_periodic_right", "exact hc",
             "have he : m*x+a=m*x1+b", "trans a+m*x", *_call("add_comm","m*x","a"), "trans b+m*x1", "exact hmod_witness_witness", *_call("add_comm","b","m*x1"),
             "rewrite he at hp", "specialize totient_coprime_periodic m", "specialize totient_coprime_periodic x1", "specialize totient_coprime_periodic b",
             "cases totient_coprime_periodic", "apply totient_coprime_periodic_left", "exact hp"),
            "Balanced congruence transports actual common-divisor coprimality, even at modulus zero or one.",
        ),
        spec(
            "euler_multiplier_coprime_iff",
            f"forall a m i r. ({_cop('a','m',tag='eu_multiplier_unit')}) -> ({_mod('m','a*i','r','multiplier_congruence')}) -> "
            f"((({_cop('i','m',tag='eu_source_unit')}) -> ({_cop('r','m',tag='eu_target_unit')})) /\\ "
            f"(({_cop('r','m',tag='eu_target_unit_back')}) -> ({_cop('i','m',tag='eu_source_unit_back')})))",
            ("euler_coprime_mod_transport", "coprime_mul_left", "totient_coprime_cancel_unit_factor", "mod_eq_symm"),
            (*_intro("a","m","i","r","ha","hmod"), "split", "intro hi",
             *_call("euler_coprime_mod_transport","m","a*i","r"), *_call("coprime_mul_left","a","i","m"), "exact ha", "exact hi", "exact hmod",
             "intro hr", "specialize totient_coprime_cancel_unit_factor a", "specialize totient_coprime_cancel_unit_factor m", "specialize totient_coprime_cancel_unit_factor i",
             f"have hc : (({_cop('a*i','m',tag='eu_cancel_product')}) -> ({_cop('i','m',tag='eu_cancel_factor')})) /\\ "
             f"(({_cop('i','m',tag='eu_cancel_factor_back')}) -> ({_cop('a*i','m',tag='eu_cancel_product_back')}))",
             "apply totient_coprime_cancel_unit_factor", "exact ha", "cases hc", "apply hc_left",
             *_call("euler_coprime_mod_transport","m","r","a*i"), "exact hr", *_call("mod_eq_symm","m","a*i","r"), "exact hmod"),
            "Multiplication by a coprime multiplier preserves and reflects precisely the unit predicate used by Phi.",
        ),
        spec(
            "euler_modulus_above_one_nonzero",
            f"forall m. ({_lt('1','m',tag='eu_domain')}) -> ~(m=0)",
            ("lt_not_le", "zero_le"),
            (*_intro("m","hm","hz"), "rewrite hz at hm", *_call("lt_not_le","1","0"), "exact hm", *_call("zero_le","1")),
            "The exact blueprint unit domain implies the nonzero modulus needed by division and cancellation.",
        ),
        spec(
            "euler_modular_unit_coprime",
            f"forall a m. ({_unit('a','m','unit_given')}) -> ({_cop('a','m',tag='eu_unit_coprime')})",
            ("mod_inverse_implies_coprime",),
            (*_intro("a","m","hu"), "cases hu", "cases hu_right", "cases hu_right_witness", *_call("mod_inverse_implies_coprime","a","m","x"), "exact hu_right_witness_right"),
            "An actual bounded inverse implies the frozen common-divisor coprimality graph.",
        ),
        spec(
            "euler_coprime_modular_unit",
            f"forall a m. ({_lt('1','m',tag='eu_unit_domain')}) -> ({_cop('a','m',tag='eu_unit_coprime_given')}) -> ({_unit('a','m','unit_built')})",
            ("euler_modulus_above_one_nonzero", "coprime_bounded_mod_inverse"),
            (*_intro("a","m","hm","hc"), "split", "exact hm", *_call("coprime_bounded_mod_inverse","a","m"), "intro hz", *_call("euler_modulus_above_one_nonzero","m"), "exact hm", "exact hz", "exact hc"),
            "Above modulus one, coprimality constructs the blueprint's actual bounded inverse without assuming it.",
        ),
        spec(
            "euler_multiplier_residue_exists",
            f"forall a m i. ~(m=0) -> exists r. ({_lt('r','m',tag='eu_residue_bound')}) /\\ ({_mod('m','a*i','r','residue_congruence')})",
            ("division_remainder_exists", "remainder_decomposition_to_mod_eq", "mul_comm"),
            (*_intro("a","m","i","hm"), "specialize division_remainder_exists m", "specialize division_remainder_exists (a*i)",
             f"have hd : exists q r. a*i=m*q+r /\\ ({_lt('r','m',tag='eu_actual_division')})", "apply division_remainder_exists", "exact hm",
             "cases hd", "cases hd_witness", "cases hd_witness_witness", "exists x1", "split", "exact hd_witness_witness_right",
             *_call("remainder_decomposition_to_mod_eq","m","a*i","x","x1"), "trans m*x+x1", "exact hd_witness_witness_left", "congr", *_call("mul_comm","m","x"), "refl"),
            "Actual Euclidean division constructs a canonical residue of every multiplied index, including index zero.",
        ),
    )


def _map_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "euler_multiplier_prefix_empty",
            f"forall a m b c. {_map('a','m','b','c','0','map_empty')}",
            ("lt_not_le", "zero_le"),
            (*_intro("a","m","b","c","i","hi"), "exfalso", *_call("lt_not_le","i","0"), "exact hi", *_call("zero_le","i")),
            "The empty multiplier prefix has no residue obligations.",
        ),
        spec(
            "euler_multiplier_prefix_extend",
            f"forall a m b c l r. ({_map('a','m','b','c','l','map_extend_old')}) -> ({_lt('r','m',tag='eu_extend_bound')}) -> "
            f"({_mod('m','a*l','r','extend_last_mod')}) -> exists d e. ({_map('a','m','d','e','S l','map_extend_new')})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (*_intro("a","m","b","c","l","r","h","hr","hmod"),
             "specialize beta_prefix_extend l", "specialize beta_prefix_extend b", "specialize beta_prefix_extend c", "specialize beta_prefix_extend r",
             "cases beta_prefix_extend", "cases beta_prefix_extend_witness", "cases beta_prefix_extend_witness_witness",
             "exists x", "exists x1", *_intro("i","hi"), f"have hs : i=l \\/ ({_lt('i','l',tag='eu_extend_index')})",
             *_call("finite_lt_succ_eq_or_lt","l","i"), "exact hi", "cases hs", "exists r", "split",
             "rewrite hs_left", "rewrite hs_left", "exact beta_prefix_extend_witness_witness_left", "split", "exact hr", "rewrite hs_left", "exact hmod",
             f"have hp : exists s. ({_at('b','c','i','s',tag='eu_extend_old')}) /\\ (({_lt('s','m',tag='eu_extend_old_bound')}) /\\ ({_mod('m','a*i','s','extend_old_mod')}))",
             *_call("h","i"), "exact hs_right", "cases hp", "cases hp_witness", "exists x2", "split",
             *_call("beta_prefix_extend_witness_witness_right","i","x2"), "exact hs_right", "exact hp_witness_left", "exact hp_witness_right"),
            "Append the actual next canonical residue, preserving every earlier decoded multiplier value.",
        ),
        spec(
            "euler_multiplier_prefix_exists",
            f"forall a m l. ~(m=0) -> exists b c. ({_map('a','m','b','c','l','map_exists')})",
            ("euler_multiplier_prefix_empty", "euler_multiplier_residue_exists", "euler_multiplier_prefix_extend"),
            (*_intro("a","m"), "induction l", "intro hm", "exists 0", "exists 0", *_call("euler_multiplier_prefix_empty","a","m","0","0"),
             "intro hm", f"have hp : exists b c. ({_map('a','m','b','c','l','map_previous')})", "apply IH", "exact hm", "cases hp", "cases hp_witness",
             f"have hr : exists r. ({_lt('r','m',tag='eu_next_bound')}) /\\ ({_mod('m','a*l','r','next_mod')})",
             *_call("euler_multiplier_residue_exists","a","m","l"), "exact hm", "cases hr", "cases hr_witness",
             *_call("euler_multiplier_prefix_extend","a","m","x","x1","l","x2"), "exact hp_witness_witness", "exact hr_witness_left", "exact hr_witness_right"),
            "HA induction builds the complete beta-coded multiplier prefix; no map or bijection is supplied as a premise.",
        ),
        spec(
            "euler_multiplier_prefix_entry",
            f"forall a m b c l i r. ({_map('a','m','b','c','l','map_entry')}) -> ({_lt('i','l',tag='eu_entry_index')}) -> "
            f"({_at('b','c','i','r',tag='eu_entry_given')}) -> ({_lt('r','m',tag='eu_entry_bound')}) /\\ ({_mod('m','a*i','r','entry_mod')})",
            ("beta_at_unique",),
            (*_intro("a","m","b","c","l","i","r","h","hi","hr"),
             f"have hp : exists v. ({_at('b','c','i','v',tag='eu_entry_chosen')}) /\\ (({_lt('v','m',tag='eu_chosen_bound')}) /\\ ({_mod('m','a*i','v','chosen_mod')}))",
             *_call("h","i"), "exact hi", "cases hp", "cases hp_witness", "have he : x=r", *_call("beta_at_unique","b","c","i","x","r"), "exact hp_witness_left", "exact hr",
             "rewrite he at hp_witness_right", "rewrite he at hp_witness_right", "exact hp_witness_right"),
            "Every decoded map entry, not just its construction witness, has the required bound and balanced congruence.",
        ),
        spec(
            "euler_multiplier_prefix_bounded_injective",
            f"forall a m b c. ~(m=0) -> ({_cop('a','m',tag='eu_permutation_unit')}) -> ({_map('a','m','b','c','m','map_full')}) -> "
            f"({bounded_prefix('b','c','m',tag='eu_bounded')}) /\\ ({injective_prefix('b','c','m',tag='eu_injective')})",
            ("euler_multiplier_prefix_entry", "mod_eq_bounded_unique", "mod_eq_cancel_coprime", "mod_eq_trans", "mod_eq_symm"),
            (*_intro("a","m","b","c","hm","ha","h"), "split", *_intro("i","hi"),
             f"have hp : exists v. ({_at('b','c','i','v',tag='eu_bounded_entry')}) /\\ (({_lt('v','m',tag='eu_bounded_value')}) /\\ ({_mod('m','a*i','v','bounded_mod')}))",
             *_call("h","i"), "exact hi", "cases hp", "cases hp_witness", "cases hp_witness_right", "exists x", "split", "exact hp_witness_left", "exact hp_witness_right_left",
             *_intro("i","j","v","hi","hj","hiv","hjv"),
             f"have hl : ({_lt('v','m',tag='eu_left_bound')}) /\\ ({_mod('m','a*i','v','left_mod')})", *_call("euler_multiplier_prefix_entry","a","m","b","c","m","i","v"), "exact h", "exact hi", "exact hiv", "cases hl",
             f"have hr : ({_lt('v','m',tag='eu_right_bound')}) /\\ ({_mod('m','a*j','v','right_mod')})", *_call("euler_multiplier_prefix_entry","a","m","b","c","m","j","v"), "exact h", "exact hj", "exact hjv", "cases hr",
             *_call("mod_eq_bounded_unique","m","i","j"), "exact hi", "exact hj", *_call("mod_eq_cancel_coprime","m","a","i","j"), "exact hm", "exact ha",
             *_call("mod_eq_trans","m","a*i","v","a*j"), "exact hl_right", *_call("mod_eq_symm","m","a*j","v"), "exact hr_right"),
            "Coprime modular cancellation makes the genuinely constructed full multiplier map a bounded injection.",
        ),
        spec(
            "euler_multiplier_prefix_permutation",
            f"forall a m b c. ~(m=0) -> ({_cop('a','m',tag='eu_permutation_coprime')}) -> ({_map('a','m','b','c','m','permutation_map')}) -> ({permutation_prefix('b','c','m',tag='eu_actual_permutation')})",
            ("euler_multiplier_prefix_bounded_injective", "finite_bounded_injective_surjective"),
            (*_intro("a","m","b","c","hm","hc","h"),
             f"have hp : ({bounded_prefix('b','c','m',tag='eu_perm_bound')}) /\\ ({injective_prefix('b','c','m',tag='eu_perm_inj')})",
             *_call("euler_multiplier_prefix_bounded_injective","a","m","b","c"), "exact hm", "exact hc", "exact h", "cases hp",
             "split", "exact hp_left", "split", "exact hp_right", *_call("finite_bounded_injective_surjective","m","b","c"), "exact hp_left", "exact hp_right"),
            "The multiplier map has actual bounded, injective, and surjective prefix evidence, not an assumed permutation label.",
        ),
        spec(
            "euler_multiplier_permutation_exists",
            f"forall a m. ~(m=0) -> ({_cop('a','m',tag='eu_exists_unit')}) -> exists b c. ({_map('a','m','b','c','m','exists_map')}) /\\ ({permutation_prefix('b','c','m',tag='eu_exists_permutation')})",
            ("euler_multiplier_prefix_exists", "euler_multiplier_prefix_permutation"),
            (*_intro("a","m","hm","hc"), f"have h : exists b c. ({_map('a','m','b','c','m','constructed_map')})", *_call("euler_multiplier_prefix_exists","a","m","m"), "exact hm",
             "cases h", "cases h_witness", "exists x", "exists x1", "split", "exact h_witness_witness", *_call("euler_multiplier_prefix_permutation","a","m","x","x1"), "exact hm", "exact hc", "exact h_witness_witness"),
            "Every coprime multiplier at every positive modulus constructs a genuine canonical finite permutation, including modulus one.",
        ),
    )


def make_euler_units_residue_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_scalar_rows(spec), *_map_rows(spec))


__all__ = ["modular_unit_relation", "unit_multiplier_prefix_relation", "make_euler_units_residue_candidate_theorems"]
