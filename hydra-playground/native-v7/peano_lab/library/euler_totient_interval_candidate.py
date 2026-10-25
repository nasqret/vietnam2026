"""Finite interval balance and periodicity for the independently counted units.

All intervals refer to the existing beta-coded characteristic sums.  The
comparison theorem proves an equality of differences without introducing
subtraction, a cardinality oracle, or an Euler-product definition of Phi.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_totient_count_candidate import _call, _intro, _cop, _count, _choice, _lt, _phi


def _equivalent(n: str, m: str, a: str, b: str, *, tag: str) -> str:
    left, right = _cop(a,n,tag=tag+"_left"), _cop(b,m,tag=tag+"_right")
    return f"((({left}) -> ({right})) /\\ (({right}) -> ({left})))"


def _interval(n: str, m: str, a: str, b: str, l: str, *, tag: str) -> str:
    i = f"euti_index_{tag}"
    return f"forall {i}. ({_lt(i,l,tag=tag+'_bound')}) -> ({_equivalent(n,m,f'({a})+{i}',f'({b})+{i}',tag=tag+'_point')})"


def make_euler_totient_interval_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "totient_unit_count_length_transport",
            f"forall n l L t. l=L -> ({_count('n','l','t',tag='length_old')}) -> ({_count('n','L','t',tag='length_new')})",
            (),
            (*_intro("n","l","L","t","he","h"), *("rewrite he at h" for _ in range(4)), "exact h"),
            "Transport the actual characteristic and summation traces along equality of interval lengths.",
        ),
        spec(
            "totient_unit_count_value_transport",
            f"forall n l t T. t=T -> ({_count('n','l','t',tag='value_old')}) -> ({_count('n','l','T',tag='value_new')})",
            (),
            (*_intro("n","l","t","T","he","h"), "rewrite he at h", "rewrite he at h", "exact h"),
            "Changing a proved equal terminal value preserves the real finite count.",
        ),
        spec(
            "totient_unit_count_zero_value",
            f"forall n. {_count('n','0','0',tag='zero_actual')}",
            ("totient_unit_count_exists", "totient_unit_count_zero_length", "totient_unit_count_value_transport"),
            ("intro n", f"have hc : exists t. {_count('n','0','t',tag='zero_chosen')}", *_call("totient_unit_count_exists","n","0"), "cases hc",
             *_call("totient_unit_count_value_transport","n","0","x","0"), *_call("totient_unit_count_zero_length","n","x"), "exact hc_witness", "exact hc_witness"),
            "Construct the empty-interval zero count for every modulus, without admitting Phi at modulus zero.",
        ),
        spec(
            "totient_unit_choices_equal_of_equivalence",
            f"forall n m a b e f. ({_equivalent('n','m','a','b',tag='choice_equivalence')}) -> "
            f"({_choice('n','a','e',tag='choice_first')}) -> ({_choice('m','b','f',tag='choice_second')}) -> e=f",
            (),
            (*_intro("n","m","a","b","e","f","heq","he","hf"), "cases heq", "cases he", "cases he_left", "cases hf", "cases hf_left",
             "trans 1", "exact he_left_right", "symm", "exact hf_left_right",
             "cases hf_right", "exfalso", "apply hf_right_left", "apply heq_left", "exact he_left_left",
             "cases he_right", "cases hf", "cases hf_left", "exfalso", "apply he_right_left", "apply heq_right", "exact hf_left_left",
             "cases hf_right", "trans 0", "exact he_right_right", "symm", "exact hf_right_right"),
            "Equivalent actual unit predicates have equal independently decided indicator bits.",
        ),
        spec(
            "totient_unit_count_interval_balance",
            f"forall l n m a b u v U V. ({_count('n','a','u',tag='interval_first_base')}) -> "
            f"({_count('m','b','v',tag='interval_second_base')}) -> ({_count('n','a+l','U',tag='interval_first_end')}) -> "
            f"({_count('m','b+l','V',tag='interval_second_end')}) -> ({_interval('n','m','a','b','l',tag='interval_same')}) -> U+v=V+u",
            ("totient_unit_count_length_transport", "totient_unit_count_functional", "totient_unit_count_succ_decompose", "totient_unit_choices_equal_of_equivalence", "le_succ", "le_refl", "add_comm", "four_square_euler_add_swap_last"),
            ("induction l", *_intro("n","m","a","b","u","v","U","V","hu","hv","hU","hV","heq"),
             f"have hUa : {_count('n','a','U',tag='interval_base_U')}", *_call("totient_unit_count_length_transport","n","a+0","a","U"), "simp", "exact hU",
             f"have hVb : {_count('m','b','V',tag='interval_base_V')}", *_call("totient_unit_count_length_transport","m","b+0","b","V"), "simp", "exact hV",
             "have hfirst : U=u", *_call("totient_unit_count_functional","n","a","U","u"), "exact hUa", "exact hu",
             "have hsecond : V=v", *_call("totient_unit_count_functional","m","b","V","v"), "exact hVb", "exact hv",
             "rewrite hfirst", "rewrite hsecond", *_call("add_comm","u","v"),
             *_intro("n","m","a","b","u","v","U","V","hu","hv","hU","hV","heq"),
             f"have hUs : {_count('n','S(a+l)','U',tag='interval_succ_U')}", *_call("totient_unit_count_length_transport","n","a+S l","S(a+l)","U"), "simp", "exact hU",
             f"have hVs : {_count('m','S(b+l)','V',tag='interval_succ_V')}", *_call("totient_unit_count_length_transport","m","b+S l","S(b+l)","V"), "simp", "exact hV",
             f"have hdU : exists r e. ({_count('n','a+l','r',tag='interval_pre_U')}) /\\ (({_choice('n','a+l','e',tag='interval_bit_U')}) /\\ U=r+e)",
             *_call("totient_unit_count_succ_decompose","n","a+l","U"), "exact hUs", "cases hdU", "cases hdU_witness", "cases hdU_witness_witness", "cases hdU_witness_witness_right",
             f"have hdV : exists s f. ({_count('m','b+l','s',tag='interval_pre_V')}) /\\ (({_choice('m','b+l','f',tag='interval_bit_V')}) /\\ V=s+f)",
             *_call("totient_unit_count_succ_decompose","m","b+l","V"), "exact hVs", "cases hdV", "cases hdV_witness", "cases hdV_witness_witness", "cases hdV_witness_witness_right",
             "have hbits : x1=x3", *_call("totient_unit_choices_equal_of_equivalence","n","m","a+l","b+l","x1","x3"),
             "specialize heq l", "apply heq", *_call("le_refl","S l"), "exact hdU_witness_witness_right_left", "exact hdV_witness_witness_right_left",
             "have hpre : x+v=x2+u", *_call("IH","n","m","a","b","u","v","x","x2"),
             "exact hu", "exact hv", "exact hdU_witness_witness_left", "exact hdV_witness_witness_left",
             *_intro("i","hi"), "specialize heq i", "apply heq", *_call("le_succ","S i","l"), "exact hi",
             "rewrite hdU_witness_witness_right_right", "rewrite hdV_witness_witness_right_right", "rewrite hbits",
             "trans (x+v)+x3", *_call("four_square_euler_add_swap_last","x","x3","v"), "rewrite hpre", "symm", *_call("four_square_euler_add_swap_last","x2","x3","u")),
            "HA induction proves equality of actual count increments on any two pointwise equivalent finite intervals.",
        ),
        spec(
            "totient_coprime_periodic",
            f"forall n k a. {_equivalent('n','n','n*k+a','a',tag='periodic')}",
            ("is_gcd_one_to_coprime", "coprime_to_is_gcd_one", "coprime_symm", "is_gcd_euclid_forward", "is_gcd_euclid_backward"),
            (*_intro("n","k","a"), "split", "intro h", *_call("coprime_symm","n","a"), *_call("is_gcd_one_to_coprime","n","a"),
             *_call("is_gcd_euclid_backward","1","n*k+a","n","k","a"), "refl", *_call("coprime_to_is_gcd_one","n*k+a","n"), "exact h",
             "intro h", *_call("is_gcd_one_to_coprime","n*k+a","n"), *_call("is_gcd_euclid_forward","1","n*k+a","n","k","a"), "refl",
             *_call("coprime_to_is_gcd_one","n","a"), *_call("coprime_symm","a","n"), "exact h"),
            "The actual common-divisor unit predicate is periodic modulo n, including the degenerate auxiliary modulus zero.",
        ),
        spec(
            "totient_unit_count_period_block",
            f"forall n k u v U. ({_count('n','n*k','u',tag='block_start')}) -> ({_count('n','n','v',tag='block_size')}) -> "
            f"({_count('n','n*k+n','U',tag='block_end')}) -> U=u+v",
            ("totient_unit_count_zero_value", "totient_unit_count_length_transport", "totient_unit_count_interval_balance", "totient_coprime_periodic", "zero_add", "add_comm"),
            (*_intro("n","k","u","v","U","hu","hv","hU"),
             "have hbalance : U+0=v+u", *_call("totient_unit_count_interval_balance","n","n","n","n*k","0","u","0","U","v"),
             "exact hu", *_call("totient_unit_count_zero_value","n"), "exact hU",
             *_call("totient_unit_count_length_transport","n","n","0+n","v"), "symm", *_call("zero_add","n"), "exact hv",
             *_intro("i","hi"), "have hzero : 0+i=i", *_call("zero_add","i"), "rewrite hzero", "rewrite hzero", *_call("totient_coprime_periodic","n","k","i"),
             "trans v+u", "trans U+0", "simp", "exact hbalance", *_call("add_comm","v","u")),
            "Each complete period contributes exactly the actual count of one canonical residue interval.",
        ),
        spec(
            "totient_unit_count_periods",
            f"forall k n u t. ({_count('n','n','u',tag='periods_unit')}) -> ({_count('n','n*k','t',tag='periods_full')}) -> t=k*u",
            ("totient_unit_count_exists", "totient_unit_count_zero_length", "totient_unit_count_length_transport", "totient_unit_count_period_block", "mul_zero_left", "mul_succ_left"),
            ("induction k", *_intro("n","u","t","hu","ht"), "trans 0", *_call("totient_unit_count_zero_length","n","t"),
             *_call("totient_unit_count_length_transport","n","n*0","0","t"), "simp", "exact ht", "symm", *_call("mul_zero_left","u"),
             *_intro("n","u","t","hu","ht"), f"have hc : exists v. {_count('n','n*k','v',tag='periods_previous')}", *_call("totient_unit_count_exists","n","n*k"), "cases hc",
             "have hpre : x=k*u", *_call("IH","n","u","x"), "exact hu", "exact hc_witness",
             "have hstep : t=x+u", *_call("totient_unit_count_period_block","n","k","x","u","t"), "exact hc_witness", "exact hu",
             *_call("totient_unit_count_length_transport","n","n*S k","n*k+n","t"), "simp", "exact ht",
             "rewrite hstep", "rewrite hpre", "symm", *_call("mul_succ_left","k","u")),
            "The actual unit count on k complete periods equals k times the actual canonical count.",
        ),
        spec(
            "totient_unit_count_pointwise_equal",
            f"forall n m l t u. ({_count('n','l','t',tag='pointwise_first')}) -> ({_count('m','l','u',tag='pointwise_second')}) -> "
            f"(forall i. ({_lt('i','l',tag='pointwise_bound')}) -> ({_equivalent('n','m','i','i',tag='pointwise_same')})) -> t=u",
            ("totient_unit_count_interval_balance", "totient_unit_count_zero_value", "totient_unit_count_length_transport", "zero_add"),
            (*_intro("n","m","l","t","u","ht","hu","heq"), "have hbalance : t+0=u+0",
             *_call("totient_unit_count_interval_balance","l","n","m","0","0","0","0","t","u"),
             *_call("totient_unit_count_zero_value","n"), *_call("totient_unit_count_zero_value","m"),
             *_call("totient_unit_count_length_transport","n","l","0+l","t"), "symm", *_call("zero_add","l"), "exact ht",
             *_call("totient_unit_count_length_transport","m","l","0+l","u"), "symm", *_call("zero_add","l"), "exact hu",
             *_intro("i","hi"), "have hzero : 0+i=i", *_call("zero_add","i"), *("rewrite hzero" for _ in range(4)), "specialize heq i", "apply heq", "exact hi",
             "trans t+0", "simp", "trans u+0", "exact hbalance", "simp"),
            "Equal actual unit predicates throughout a finite prefix have equal witnessed cardinalities.",
        ),
        spec(
            "totient_unit_count_modulus_transport",
            f"forall n N l t. n=N -> ({_count('n','l','t',tag='modulus_old')}) -> ({_count('N','l','t',tag='modulus_new')})",
            (),
            (*_intro("n","N","l","t","he","h"), "rewrite he at h", "rewrite he at h", "exact h"),
            "A proved equal modulus preserves the actual finite count without changing its interval.",
        ),
        spec(
            "totient_value_transport",
            f"forall n t T. t=T -> ({_phi('n','t',tag='phi_value_old')}) -> ({_phi('n','T',tag='phi_value_new')})",
            (),
            (*_intro("n","t","T","he","h"), "rewrite he at h", "rewrite he at h", "exact h"),
            "A proved equal value preserves the positive-domain actual totient graph.",
        ),
        spec(
            "totient_modulus_transport",
            f"forall n N t. n=N -> ({_phi('n','t',tag='phi_modulus_old')}) -> ({_phi('N','t',tag='phi_modulus_new')})",
            (),
            (*_intro("n","N","t","he","h"), *("rewrite he at h" for _ in range(7)), "exact h"),
            "A proved equal positive modulus preserves both the unit predicate and its canonical residue interval.",
        ),
    )


__all__ = ["make_euler_totient_interval_candidate_theorems"]
