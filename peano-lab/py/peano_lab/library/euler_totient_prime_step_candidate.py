"""Actual unit-count recurrences when a prime is adjoined to the modulus.

The proofs compare genuine coprimality masks and their beta sums.  In the
new-prime case precisely the multiples of that prime are excluded; no
counting formula is placed into the definition of the unit predicate.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_totient_count_candidate import _call, _intro, _cop, _count, _choice, _lt
from .euler_totient_interval_candidate import _equivalent


def _dvd(d: str, n: str, *, tag: str) -> str:
    return f"exists eutps_factor_{tag}. ({n})=({d})*eutps_factor_{tag}"


def _prime(p: str, *, tag: str) -> str:
    return f"~(({p})=1) /\\ forall eutps_a_{tag} eutps_b_{tag}. ({p})=eutps_a_{tag}*eutps_b_{tag} -> eutps_a_{tag}=1 \\/ eutps_b_{tag}=1"


def _scalar_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "totient_divisor_reflexive",
            f"forall a. {_dvd('a','a',tag='reflexive_divisor')}",
            ("zero_add",),
            ("intro a", "exists 1", "simp [zero_add]"),
            "Every natural divides itself with the explicit quotient one.",
        ),
        spec(
            "totient_coprime_divisor_right",
            f"forall a b c. ({_dvd('b','c',tag='cop_divisor')}) -> ({_cop('a','c',tag='cop_large')}) -> ({_cop('a','b',tag='cop_small')})",
            ("mul_assoc",),
            (*_intro("a","b","c","hd","hc","d","ha","hb"), "cases hd", "cases hb", "specialize hc d", "apply hc", "exact ha", "exists x1*x",
             "rewrite hd_witness", "rewrite hb_witness", *_call("mul_assoc","d","x1","x")),
            "Every divisor of a modulus is coprime to each unit of that modulus.",
        ),
        spec(
            "totient_coprime_product_iff",
            f"forall a n m. (({_cop('a','n*m',tag='product_whole')}) -> (({_cop('a','n',tag='product_left')}) /\\ ({_cop('a','m',tag='product_right')}))) /\\ "
            f"((({_cop('a','n',tag='product_given_left')}) /\\ ({_cop('a','m',tag='product_given_right')})) -> ({_cop('a','n*m',tag='product_built')}))",
            ("totient_coprime_divisor_right", "coprime_mul_right", "right_factor_divides_product"),
            (*_intro("a","n","m"), "split", "intro h", "split", *_call("totient_coprime_divisor_right","a","n","n*m"), "exists m", "refl", "exact h",
             *_call("totient_coprime_divisor_right","a","m","n*m"), *_call("right_factor_divides_product","n","m"), "exact h",
             "intro h", "cases h", *_call("coprime_mul_right","a","n","m"), "exact h_left", "exact h_right"),
            "Units of a product are exactly the simultaneous units of both factors, without a coprime-moduli assumption.",
        ),
        spec(
            "totient_prime_coprime_iff_nondivisor",
            f"forall p a. ({_prime('p',tag='unit_prime')}) -> ((({_cop('a','p',tag='prime_unit')}) -> ~({_dvd('p','a',tag='prime_nondivisor')})) /\\ "
            f"(~({_dvd('p','a',tag='prime_not_divides')}) -> ({_cop('a','p',tag='prime_unit_built')})))",
            ("prime_not_divides_coprime", "coprime_symm", "totient_divisor_reflexive"),
            (*_intro("p","a","hp"), "split", *_intro("hc","hd"), "cases hp", "apply hp_left", "specialize hc p", "apply hc", "exact hd", *_call("totient_divisor_reflexive","p"),
             "intro hd", *_call("coprime_symm","p","a"), *_call("prime_not_divides_coprime","p","a"), "exact hp", "exact hd"),
            "For a prime modulus the independently defined unit predicate is equivalent to nondivisibility.",
        ),
        spec(
            "totient_coprime_repeated_factor",
            f"forall n p a. ({_dvd('p','n',tag='repeat_divisor')}) -> ({_equivalent('n*p','n','a','a',tag='repeat_unit')})",
            ("totient_coprime_product_iff", "totient_coprime_divisor_right", "coprime_mul_right"),
            (*_intro("n","p","a","hd"), "split", "intro hc",
             f"have hh : (({_cop('a','n*p',tag='repeat_full')}) -> (({_cop('a','n',tag='repeat_left')}) /\\ ({_cop('a','p',tag='repeat_right')}))) /\\ "
             f"((({_cop('a','n',tag='repeat_given_left')}) /\\ ({_cop('a','p',tag='repeat_given_right')})) -> ({_cop('a','n*p',tag='repeat_built')}))",
             *_call("totient_coprime_product_iff","a","n","p"), "cases hh",
             f"have hparts : ({_cop('a','n',tag='repeat_parts_left')}) /\\ ({_cop('a','p',tag='repeat_parts_right')})", "apply hh_left", "exact hc", "cases hparts", "exact hparts_left",
             "intro hc", *_call("coprime_mul_right","a","n","p"), "exact hc", *_call("totient_coprime_divisor_right","a","p","n"), "exact hd", "exact hc"),
            "Adjoining a factor already dividing the modulus leaves the unit predicate unchanged.",
        ),
        spec(
            "totient_coprime_cancel_unit_factor",
            f"forall p n a. ({_cop('p','n',tag='cancel_unit')}) -> ({_equivalent('n','n','p*a','a',tag='cancel_predicate')})",
            ("coprime_mul_left", "coprime_symm", "totient_coprime_divisor_right", "mul_comm"),
            (*_intro("p","n","a","hp"), "split", "intro hc", f"have hnc : {_cop('n','p*a',tag='cancel_reverse')}", *_call("coprime_symm","p*a","n"), "exact hc",
             *_call("coprime_symm","n","a"), *_call("totient_coprime_divisor_right","n","a","p*a"),
             "exists p", *_call("mul_comm","p","a"), "exact hnc",
             "intro hc", *_call("coprime_mul_left","p","a","n"), "exact hp", "exact hc"),
            "Multiplication by a unit preserves common-divisor coprimality at every index.",
        ),
        spec(
            "totient_prime_multiple_is_not_unit",
            f"forall p n j. ({_prime('p',tag='multiple_prime')}) -> ~({_cop('p*j','n*p',tag='multiple_nonunit')})",
            ("mul_comm",),
            (*_intro("p","n","j","hp","hc"), "cases hp", "apply hp_left", "specialize hc p", "apply hc", "exists j", "refl", "exists n", *_call("mul_comm","n","p")),
            "A multiple of p is never a unit modulo n*p, including j=0.",
        ),
        spec(
            "totient_nonzero_prime_block_offset_not_divisible",
            f"forall p j r. ~(r=0) -> ({_lt('r','p',tag='offset_bound')}) -> ~({_dvd('p','p*j+r',tag='offset_not_divides')})",
            ("bounded_nonzero_not_divides", "divides_remainder", "totient_divisor_reflexive"),
            (*_intro("p","j","r","hr","hlt","hd"), *_call("bounded_nonzero_not_divides","p","r"), "exact hr", "exact hlt",
             *_call("divides_remainder","p","p*j+r","p","j","r"), "exact hd", *_call("totient_divisor_reflexive","p"), "refl"),
            "The positive offsets inside a prime-width block cannot be multiples of its width.",
        ),
        spec(
            "totient_prime_block_positive_offset_units",
            f"forall p n j r. ({_prime('p',tag='offset_prime')}) -> ~(r=0) -> ({_lt('r','p',tag='offset_range')}) -> "
            f"({_equivalent('n','n*p','p*j+r','p*j+r',tag='offset_units')})",
            ("coprime_mul_right", "coprime_symm", "prime_not_divides_coprime", "totient_nonzero_prime_block_offset_not_divisible", "totient_coprime_divisor_right"),
            (*_intro("p","n","j","r","hp","hr","hlt"), "split", "intro hc", *_call("coprime_mul_right","p*j+r","n","p"), "exact hc",
             *_call("coprime_symm","p","p*j+r"), *_call("prime_not_divides_coprime","p","p*j+r"), "exact hp",
             "intro hd", *_call("totient_nonzero_prime_block_offset_not_divisible","p","j","r"), "exact hr", "exact hlt", "exact hd",
             "intro hc", *_call("totient_coprime_divisor_right","p*j+r","n","n*p"), "exists p", "refl", "exact hc"),
            "Apart from its first index, each p-wide block has exactly the same unit mask for n and n*p.",
        ),
        spec(
            "totient_unit_count_repeated_prime_factor",
            f"forall n p u t. ({_dvd('p','n',tag='count_repeat_divisor')}) -> ({_count('n','n','u',tag='count_repeat_unit')}) -> "
            f"({_count('n*p','n*p','t',tag='count_repeat_full')}) -> t=p*u",
            ("totient_unit_count_exists", "totient_unit_count_pointwise_equal", "totient_coprime_repeated_factor", "totient_unit_count_periods"),
            (*_intro("n","p","u","t","hd","hu","ht"), f"have hc : exists v. {_count('n','n*p','v',tag='repeat_period_count')}",
             *_call("totient_unit_count_exists","n","n*p"), "cases hc", "trans x", *_call("totient_unit_count_pointwise_equal","n*p","n","n*p","t","x"),
             "exact ht", "exact hc_witness", *_intro("i","hi"), *_call("totient_coprime_repeated_factor","n","p","i"), "exact hd",
             *_call("totient_unit_count_periods","p","n","u","x"), "exact hu", "exact hc_witness"),
            "When p already divides n, the actual canonical unit count of n*p is p times that of n.",
        ),
        spec(
            "totient_unit_choice_transport",
            f"forall n m a b e. ({_equivalent('n','m','a','b',tag='choice_transport_equiv')}) -> ({_choice('n','a','e',tag='choice_transport_given')}) -> "
            f"({_choice('m','b','e',tag='choice_transport_built')})",
            (),
            (*_intro("n","m","a","b","e","heq","h"), "cases heq", "cases h", "cases h_left", "left", "split", "apply heq_left", "exact h_left_left", "exact h_left_right",
             "cases h_right", "right", "split", "intro hc", "apply h_right_left", "apply heq_right", "exact hc", "exact h_right_right"),
            "Transport an actually decided characteristic bit along proved equivalence of its predicates.",
        ),
        spec(
            "totient_prime_block_end",
            "forall p h j. p=S h -> S(p*j)+h=p*S j",
            ("add_succ_left",),
            (*_intro("p","h","j","hp"), "trans p*j+S h", "simp [add_succ_left]", "trans p*j+p", "congr", "refl", "symm", "exact hp", "simp"),
            "The one first index and h remaining indices are exactly a block of width p=S h.",
        ),
        spec(
            "totient_count_defect_step",
            "forall U V u v w e. u=v+w -> U+v=(V+u)+e -> U=V+(w+e)",
            ("add_right_cancel", "add_assoc", "add_comm", "four_square_add_swap_right_tail"),
            (*_intro("U","V","u","v","w","e","hpre","hstep"), *_call("add_right_cancel","U","V+(w+e)","v"), "trans (V+u)+e", "exact hstep",
             "rewrite hpre", "simp [add_assoc, add_comm, four_square_add_swap_right_tail]"),
            "Subtraction-free cancellation propagates an exact finite count defect by one actual bit.",
        ),
    )


def _block_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "totient_new_prime_block_count_balance",
            f"forall p h n j u v U V e. ({_prime('p',tag='block_prime')}) -> p=S h -> ({_cop('p','n',tag='block_unit_factor')}) -> "
            f"({_choice('n','j','e',tag='block_removed_bit')}) -> ({_count('n','p*j','u',tag='block_first_base')}) -> ({_count('n*p','p*j','v',tag='block_second_base')}) -> "
            f"({_count('n','p*S j','U',tag='block_first_end')}) -> ({_count('n*p','p*S j','V',tag='block_second_end')}) -> U+v=(V+u)+e",
            ("totient_coprime_cancel_unit_factor", "totient_unit_choice_transport", "totient_unit_count_succ_intro", "totient_prime_multiple_is_not_unit",
             "totient_unit_count_interval_balance", "totient_unit_count_length_transport", "totient_prime_block_end", "totient_prime_block_positive_offset_units",
             "add_succ_left", "succ_ne_zero", "succ_le_succ", "add_assoc"),
            (*_intro("p","h","n","j","u","v","U","V","e","hp","hpred","hc","he","hu","hv","hU","hV"),
             f"have hfactor : {_equivalent('n','n','p*j','j',tag='block_first_equiv')}", *_call("totient_coprime_cancel_unit_factor","p","n","j"), "exact hc", "cases hfactor",
             f"have hfirst : {_count('n','S(p*j)','u+e',tag='block_first_succ')}", *_call("totient_unit_count_succ_intro","n","p*j","u","e"), "exact hu",
             *_call("totient_unit_choice_transport","n","n","j","p*j","e"), "split", "exact hfactor_right", "exact hfactor_left", "exact he",
             f"have hsecond : {_count('n*p','S(p*j)','v+0',tag='block_second_succ')}", *_call("totient_unit_count_succ_intro","n*p","p*j","v","0"), "exact hv",
             "right", "split", "intro hbad", *_call("totient_prime_multiple_is_not_unit","p","n","j"), "exact hp", "exact hbad", "refl",
             "have hbalance : U+(v+0)=V+(u+e)", *_call("totient_unit_count_interval_balance","h","n","n*p","S(p*j)","S(p*j)","u+e","v+0","U","V"),
             "exact hfirst", "exact hsecond", *_call("totient_unit_count_length_transport","n","p*S j","S(p*j)+h","U"), "symm", *_call("totient_prime_block_end","p","h","j"), "exact hpred", "exact hU",
             *_call("totient_unit_count_length_transport","n*p","p*S j","S(p*j)+h","V"), "symm", *_call("totient_prime_block_end","p","h","j"), "exact hpred", "exact hV",
             *_intro("i","hi"), "have hindex : S(p*j)+i=p*j+S i", "simp [add_succ_left]", *("rewrite hindex" for _ in range(4)),
             *_call("totient_prime_block_positive_offset_units","p","n","j","S i"), "exact hp", *_call("succ_ne_zero","i"), "rewrite hpred", *_call("succ_le_succ","S i","h"), "exact hi",
             "trans U+(v+0)", "simp", "trans V+(u+e)", "exact hbalance", "symm", *_call("add_assoc","V","u","e")),
            "A genuine p-wide block loses exactly the unit indicator of j at its first index p*j; all positive offsets are unchanged.",
        ),
        spec(
            "totient_new_prime_multiple_blocks_balance",
            f"forall j p h n U V w. ({_prime('p',tag='blocks_prime')}) -> p=S h -> ({_cop('p','n',tag='blocks_unit_factor')}) -> "
            f"({_count('n','p*j','U',tag='blocks_first_count')}) -> ({_count('n*p','p*j','V',tag='blocks_second_count')}) -> ({_count('n','j','w',tag='blocks_removed_count')}) -> U=V+w",
            ("totient_unit_count_length_transport", "totient_unit_count_zero_length", "totient_unit_count_exists", "totient_unit_count_succ_decompose",
             "totient_new_prime_block_count_balance", "totient_count_defect_step"),
            ("induction j", *_intro("p","h","n","U","V","w","hp","hpred","hc","hU","hV","hw"),
             "have hUz : U=0", *_call("totient_unit_count_zero_length","n","U"), *_call("totient_unit_count_length_transport","n","p*0","0","U"), "simp", "exact hU",
             "have hVz : V=0", *_call("totient_unit_count_zero_length","n*p","V"), *_call("totient_unit_count_length_transport","n*p","p*0","0","V"), "simp", "exact hV",
             "have hwz : w=0", *_call("totient_unit_count_zero_length","n","w"), "exact hw", "rewrite hUz", "rewrite hVz", "rewrite hwz", "simp",
             *_intro("p","h","n","U","V","w","hp","hpred","hc","hU","hV","hw"),
             f"have hA : exists u. {_count('n','p*j','u',tag='blocks_previous_A')}", *_call("totient_unit_count_exists","n","p*j"), "cases hA",
             f"have hB : exists v. {_count('n*p','p*j','v',tag='blocks_previous_B')}", *_call("totient_unit_count_exists","n*p","p*j"), "cases hB",
             f"have hd : exists z e. ({_count('n','j','z',tag='blocks_removed_previous')}) /\\ (({_choice('n','j','e',tag='blocks_removed_last')}) /\\ w=z+e)",
             *_call("totient_unit_count_succ_decompose","n","j","w"), "exact hw", "cases hd", "cases hd_witness", "cases hd_witness_witness", "cases hd_witness_witness_right",
             "have hpre : x=x1+x2", *_call("IH","p","h","n","x","x1","x2"), "exact hp", "exact hpred", "exact hc", "exact hA_witness", "exact hB_witness", "exact hd_witness_witness_left",
             "have hstep : U+x1=(V+x)+x3", *_call("totient_new_prime_block_count_balance","p","h","n","j","x","x1","U","V","x3"),
             "exact hp", "exact hpred", "exact hc", "exact hd_witness_witness_right_left", "exact hA_witness", "exact hB_witness", "exact hU", "exact hV",
             "rewrite hd_witness_witness_right_right", *_call("totient_count_defect_step","U","V","x","x1","x2","x3"), "exact hpre", "exact hstep"),
            "Induction on the number of prime-width blocks counts all removed multiples using the actual unit count of their quotients.",
        ),
        spec(
            "totient_unit_count_new_prime_balance",
            f"forall p h n u t. ({_prime('p',tag='new_prime')}) -> p=S h -> ({_cop('p','n',tag='new_unit_factor')}) -> "
            f"({_count('n','n','u',tag='new_original_count')}) -> ({_count('n*p','n*p','t',tag='new_product_count')}) -> t+u=p*u",
            ("totient_unit_count_exists", "totient_new_prime_multiple_blocks_balance", "totient_unit_count_length_transport", "totient_unit_count_periods", "mul_comm"),
            (*_intro("p","h","n","u","t","hp","hpred","hc","hu","ht"), f"have hA : exists v. {_count('n','p*n','v',tag='new_all_original_units')}",
             *_call("totient_unit_count_exists","n","p*n"), "cases hA", "trans x", "symm", *_call("totient_new_prime_multiple_blocks_balance","n","p","h","n","x","t","u"),
             "exact hp", "exact hpred", "exact hc", "exact hA_witness", *_call("totient_unit_count_length_transport","n*p","n*p","p*n","t"), *_call("mul_comm","n","p"), "exact ht", "exact hu",
             *_call("totient_unit_count_periods","p","n","u","x"), "exact hu", *_call("totient_unit_count_length_transport","n","p*n","n*p","x"), *_call("mul_comm","p","n"), "exact hA_witness"),
            "For a new prime factor, the removed multiples account for exactly one old canonical unit count among p periods.",
        ),
        spec(
            "totient_unit_count_new_prime_factor",
            f"forall p h n u t. ({_prime('p',tag='new_factor_prime')}) -> p=S h -> ({_cop('p','n',tag='new_factor_unit')}) -> "
            f"({_count('n','n','u',tag='new_factor_original')}) -> ({_count('n*p','n*p','t',tag='new_factor_result')}) -> t=h*u",
            ("totient_unit_count_new_prime_balance", "add_right_cancel", "mul_succ_left"),
            (*_intro("p","h","n","u","t","hp","hpred","hc","hu","ht"), "have hbalance : t+u=p*u", *_call("totient_unit_count_new_prime_balance","p","h","n","u","t"),
             "exact hp", "exact hpred", "exact hc", "exact hu", "exact ht", *_call("add_right_cancel","t","h*u","u"), "trans p*u", "exact hbalance", "rewrite hpred", *_call("mul_succ_left","h","u")),
            "The actual canonical unit count of n*p is (p-1) times that of n when p is prime and coprime to n.",
        ),
    )


def make_euler_totient_prime_step_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_scalar_rows(spec), *_block_rows(spec))


__all__ = ["make_euler_totient_prime_step_candidate_theorems"]
