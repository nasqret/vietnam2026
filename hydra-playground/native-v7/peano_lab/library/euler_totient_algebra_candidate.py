"""Prime-power values and coprime multiplicativity of the actual totient.

The count graph is independently defined in euler_totient_count_candidate.
Multiplicativity is proved by induction on an actually witnessed prime list,
then that list is constructed for every positive input by the frozen G004.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_totient_count_candidate import _call, _intro, _cop, _count, _phi
from .euler_totient_prime_step_candidate import _prime, _dvd
from .finite_sum_theorems import _at
from .foundation_saturation_candidate import _product, _allprime, _factorization
from .power_algebra_theorems import _power_terms


def _pow(p: str, e: str, P: str, *, tag: str) -> str:
    return _power_terms(p,e,P,tag='euta_'+tag)


def _prime_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "totient_repeated_prime_factor",
            f"forall n p u. ({_prime('p',tag='repeated_prime')}) -> ({_phi('n','u',tag='repeated_original')}) -> ({_dvd('p','n',tag='repeated_divisor')}) -> "
            f"({_phi('n*p','p*u',tag='repeated_value')})",
            ("mul_ne_zero", "prime_nonzero", "totient_unit_count_exists", "totient_unit_count_value_transport", "totient_unit_count_repeated_prime_factor"),
            (*_intro("n","p","u","hp","hu","hd"), "cases hu", "split", "intro hz", *_call("mul_ne_zero","n","p"), "exact hu_left", "intro hpz", *_call("prime_nonzero","p"), "exact hp", "exact hpz", "exact hz",
             f"have hc : exists t. {_count('n*p','n*p','t',tag='repeated_chosen')}", *_call("totient_unit_count_exists","n*p","n*p"), "cases hc",
             *_call("totient_unit_count_value_transport","n*p","n*p","x","p*u"), *_call("totient_unit_count_repeated_prime_factor","n","p","u","x"),
             "exact hd", "exact hu_right", "exact hc_witness", "exact hc_witness"),
            "Construct Phi(n*p,p*Phi(n)) when the prime p already divides n, using the actual finite unit-count identity.",
        ),
        spec(
            "totient_new_prime_factor",
            f"forall n p h u. ({_prime('p',tag='new_prime')}) -> p=S h -> ({_phi('n','u',tag='new_original')}) -> ({_cop('p','n',tag='new_coprime')}) -> "
            f"({_phi('n*p','h*u',tag='new_value')})",
            ("mul_ne_zero", "prime_nonzero", "totient_unit_count_exists", "totient_unit_count_value_transport", "totient_unit_count_new_prime_factor"),
            (*_intro("n","p","h","u","hp","hpred","hu","hcop"), "cases hu", "split", "intro hz", *_call("mul_ne_zero","n","p"), "exact hu_left", "intro hpz", *_call("prime_nonzero","p"), "exact hp", "exact hpz", "exact hz",
             f"have hc : exists t. {_count('n*p','n*p','t',tag='new_chosen')}", *_call("totient_unit_count_exists","n*p","n*p"), "cases hc",
             *_call("totient_unit_count_value_transport","n*p","n*p","x","h*u"), *_call("totient_unit_count_new_prime_factor","p","h","n","u","x"),
             "exact hp", "exact hpred", "exact hcop", "exact hu_right", "exact hc_witness", "exact hc_witness"),
            "Construct Phi(n*p,(p-1)*Phi(n)) for a new prime factor; the predecessor is represented by p=S h.",
        ),
        spec(
            "totient_prime_value",
            f"forall p h. ({_prime('p',tag='value_prime')}) -> p=S h -> ({_phi('p','h',tag='prime_value')})",
            ("totient_new_prime_factor", "totient_one_value", "coprime_one_right", "totient_modulus_transport", "totient_value_transport", "one_mul", "mul_one"),
            (*_intro("p","h","hp","hpred"), *_call("totient_modulus_transport","1*p","p","h"), *_call("one_mul","p"),
             *_call("totient_value_transport","1*p","h*1","h"), *_call("mul_one","h"), *_call("totient_new_prime_factor","1","p","h","1"),
             "exact hp", "exact hpred", "exact totient_one_value", *_call("coprime_one_right","p")),
            "A prime has exactly p-1 canonical units, with all beta witnesses constructed from Phi(1,1).",
        ),
        spec(
            "totient_prime_power_successor_value",
            f"forall e p h Q. ({_prime('p',tag='power_prime')}) -> p=S h -> ({_pow('p','e','Q',tag='power_previous')}) -> "
            f"({_phi('Q*p','h*Q',tag='power_successor_value')})",
            ("pow_zero", "pow_successor_decompose", "totient_prime_value", "totient_modulus_transport", "totient_value_transport", "totient_repeated_prime_factor",
             "one_mul", "mul_one", "mul_comm", "mul_assoc", "natural_mul_swap_right_tail"),
            ("induction e", *_intro("p","h","Q","hp","hpred","hQ"), "have hQone : Q=1", *_call("pow_zero","p","0","Q"), "refl", "exact hQ",
             *_call("totient_modulus_transport","p","Q*p","h*Q"), "rewrite hQone", "symm", *_call("one_mul","p"),
             *_call("totient_value_transport","p","h","h*Q"), "rewrite hQone", "symm", *_call("mul_one","h"), *_call("totient_prime_value","p","h"), "exact hp", "exact hpred",
             *_intro("p","h","Q","hp","hpred","hQ"), f"have hd : exists R. ({_pow('p','e','R',tag='power_prefix')}) /\\ Q=R*p",
             *_call("pow_successor_decompose","p","e","S e","Q"), "refl", "exact hQ", "cases hd", "cases hd_witness",
             f"have hphi : {_phi('Q','h*x',tag='power_prefix_phi')}", *_call("totient_modulus_transport","x*p","Q","h*x"), "symm", "exact hd_witness_right",
             *_call("IH","p","h","x"), "exact hp", "exact hpred", "exact hd_witness_left",
             *_call("totient_value_transport","Q*p","p*(h*x)","h*Q"), "rewrite hd_witness_right", "simp [mul_assoc, mul_comm, natural_mul_swap_right_tail]",
             *_call("totient_repeated_prime_factor","Q","p","h*x"), "exact hp", "exact hphi", "exists x", "trans x*p", "exact hd_witness_right", *_call("mul_comm","x","p")),
            "Induction proves Phi(p^(e+1))=(p-1)*p^e for the independent unit count, starting with the prime case.",
        ),
        spec(
            "totient_prime_power_value",
            f"forall p e P. ({_prime('p',tag='full_power_prime')}) -> ~(e=0) -> ({_pow('p','e','P',tag='full_power')}) -> "
            f"exists h d Q. p=S h /\\ (e=S d /\\ (({_pow('p','d','Q',tag='full_power_predecessor')}) /\\ ({_phi('P','Q*h',tag='full_power_phi')})))",
            ("prime_nonzero", "nonzero_is_succ", "pow_successor_decompose", "totient_prime_power_successor_value", "totient_modulus_transport", "totient_value_transport", "mul_comm"),
            (*_intro("p","e","P","hp","he","hP"), "have hpred : exists h. p=S h", *_call("nonzero_is_succ","p"), "intro hpz", *_call("prime_nonzero","p"), "exact hp", "exact hpz", "cases hpred",
             "have hepred : exists d. e=S d", *_call("nonzero_is_succ","e"), "exact he", "cases hepred",
             f"have hd : exists Q. ({_pow('p','x1','Q',tag='full_power_actual_prefix')}) /\\ P=Q*p", *_call("pow_successor_decompose","p","x1","e","P"), "exact hepred_witness", "exact hP", "cases hd", "cases hd_witness",
             "exists x", "exists x1", "exists x2", "split", "exact hpred_witness", "split", "exact hepred_witness", "split", "exact hd_witness_left",
             *_call("totient_modulus_transport","x2*p","P","x2*x"), "symm", "exact hd_witness_right", *_call("totient_value_transport","x2*p","x*x2","x2*x"), *_call("mul_comm","x","x2"),
             *_call("totient_prime_power_successor_value","x1","p","x","x2"), "exact hp", "exact hpred_witness", "exact hd_witness_left"),
            "For every positive prime exponent, construct p-1, e-1, the actual preceding power, and its product giving the uniquely defined totient.",
        ),
    )


def _multiplicative_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "totient_coprime_divisor_left",
            f"forall a b c. ({_dvd('a','c',tag='left_divisor')}) -> ({_cop('c','b',tag='left_large')}) -> ({_cop('a','b',tag='left_small')})",
            ("coprime_symm", "totient_coprime_divisor_right"),
            (*_intro("a","b","c","hd","hc"), f"have hlarge : {_cop('b','c',tag='left_large_reverse')}", *_call("coprime_symm","c","b"), "exact hc",
             *_call("coprime_symm","b","a"), *_call("totient_coprime_divisor_right","b","a","c"), "exact hd", "exact hlarge"),
            "Coprimality passes to any genuinely witnessed divisor on the left.",
        ),
        spec(
            "totient_coprime_multiplication_prime_step",
            f"forall p h a b u v w. ({_prime('p',tag='mult_step_prime')}) -> p=S h -> ({_cop('p','b',tag='mult_step_coprime')}) -> "
            f"({_phi('a','u',tag='mult_step_first')}) -> ({_phi('a*b','u*v',tag='mult_step_previous')}) -> ({_phi('a*p','w',tag='mult_step_selected')}) -> "
            f"({_phi('(a*p)*b','w*v',tag='mult_step_result')})",
            ("prime_coprime_or_divides", "totient_functional", "totient_new_prime_factor", "totient_repeated_prime_factor", "coprime_mul_right", "totient_modulus_transport", "totient_value_transport",
             "mul_assoc", "mul_comm", "natural_mul_swap_right_tail"),
            (*_intro("p","h","a","b","u","v","w","hp","hpred","hpb","hu","huv","hw"),
             f"have hd : ({_cop('p','a',tag='mult_step_new_prime')}) \\/ ({_dvd('p','a',tag='mult_step_old_prime')})", *_call("prime_coprime_or_divides","p","a"), "exact hp", "cases hd",
             "have hwval : w=h*u", *_call("totient_functional","a*p","w","h*u"), "exact hw", *_call("totient_new_prime_factor","a","p","h","u"), "exact hp", "exact hpred", "exact hu", "exact hd_left",
             *_call("totient_modulus_transport","(a*b)*p","(a*p)*b","w*v"), "simp [mul_assoc, mul_comm, natural_mul_swap_right_tail]",
             *_call("totient_value_transport","(a*b)*p","h*(u*v)","w*v"), "rewrite hwval", "symm", *_call("mul_assoc","h","u","v"),
             *_call("totient_new_prime_factor","a*b","p","h","u*v"), "exact hp", "exact hpred", "exact huv", *_call("coprime_mul_right","p","a","b"), "exact hd_left", "exact hpb",
             "have hwval : w=p*u", *_call("totient_functional","a*p","w","p*u"), "exact hw", *_call("totient_repeated_prime_factor","a","p","u"), "exact hp", "exact hu", "exact hd_right",
             *_call("totient_modulus_transport","(a*b)*p","(a*p)*b","w*v"), "simp [mul_assoc, mul_comm, natural_mul_swap_right_tail]",
             *_call("totient_value_transport","(a*b)*p","p*(u*v)","w*v"), "rewrite hwval", "symm", *_call("mul_assoc","p","u","v"),
             *_call("totient_repeated_prime_factor","a*b","p","u*v"), "exact hp", "exact huv", "cases hd_right", "exists x*b", "rewrite hd_right_witness", *_call("mul_assoc","p","x","b")),
            "One genuine prime-factor step preserves multiplicativity, separating the new-prime and repeated-prime cases constructively.",
        ),
        spec(
            "totient_coprime_multiplicative_from_prime_list",
            f"forall l f g a b u v. ({_allprime('f','g','l','mult_primes')}) -> ({_product('f','g','l','a','mult_product')}) -> "
            f"({_phi('a','u',tag='mult_first')}) -> ({_phi('b','v',tag='mult_second')}) -> ({_cop('a','b',tag='mult_coprime')}) -> ({_phi('a*b','u*v',tag='mult_value')})",
            ("beta_product_zero", "totient_one", "totient_modulus_transport", "totient_value_transport", "one_mul", "beta_product_succ_decompose", "beta_all_prime_entry_is_prime", "le_refl",
             "mul_zero_left", "totient_exists", "totient_coprime_divisor_left", "all_prime_succ_elim_prefix", "prime_nonzero", "nonzero_is_succ", "totient_coprime_multiplication_prime_step", "mul_comm"),
            ("induction l", *_intro("f","g","a","b","u","v","hprimes","hprod","hu","hv","hcop"),
             "have ha : a=1", *_call("beta_product_zero","f","g","a"), "exact hprod",
             "have huone : u=1", *_call("totient_one","u"), *_call("totient_modulus_transport","a","1","u"), "exact ha", "exact hu",
             *_call("totient_modulus_transport","b","a*b","u*v"), "rewrite ha", "symm", *_call("one_mul","b"),
             *_call("totient_value_transport","b","v","u*v"), "rewrite huone", "symm", *_call("one_mul","v"), "exact hv",
             *_intro("f","g","a","b","u","v","hprimes","hprod","hu","hv","hcop"),
             f"have hd : exists p r. ({_at('f','g','l','p',tag='euta_mult_last')}) /\\ (({_product('f','g','l','r','mult_pre_product')}) /\\ a=r*p)",
             *_call("beta_product_succ_decompose","f","g","l","a"), "exact hprod", "cases hd", "cases hd_witness", "cases hd_witness_witness", "cases hd_witness_witness_right",
             f"have hp : {_prime('x',tag='mult_actual_prime')}", *_call("beta_all_prime_entry_is_prime","f","g","S l","l","x"), "exact hprimes", *_call("le_refl","S l"), "exact hd_witness_witness_left",
             "have hn : ~(a=0)", "cases hu", "exact hu_left", "have hrnz : ~(x1=0)", "intro hz", "apply hn", "rewrite hd_witness_witness_right_right", "rewrite hz", *_call("mul_zero_left","x"),
             f"have hphi : exists t. {_phi('x1','t',tag='mult_actual_prefix_phi')}", *_call("totient_exists","x1"), "exact hrnz", "cases hphi",
             f"have hrb : {_cop('x1','b',tag='mult_prefix_coprime')}", *_call("totient_coprime_divisor_left","x1","b","a"), "exists x", "exact hd_witness_witness_right_right", "exact hcop",
             f"have hpb : {_cop('x','b',tag='mult_last_coprime')}", *_call("totient_coprime_divisor_left","x","b","a"), "exists x1", "trans x1*x", "exact hd_witness_witness_right_right", *_call("mul_comm","x1","x"), "exact hcop",
             f"have hprevious : {_phi('x1*b','x2*v',tag='mult_previous_value')}", *_call("IH","f","g","x1","b","x2","v"),
             *_call("all_prime_succ_elim_prefix","f","g","l"), "exact hprimes", "exact hd_witness_witness_right_left", "exact hphi_witness", "exact hv", "exact hrb",
             "have hpred : exists h. x=S h", *_call("nonzero_is_succ","x"), "intro hpz", *_call("prime_nonzero","x"), "exact hp", "exact hpz", "cases hpred",
             f"have hselected : {_phi('x1*x','u',tag='mult_selected_value')}", *_call("totient_modulus_transport","a","x1*x","u"), "exact hd_witness_witness_right_right", "exact hu",
             *_call("totient_modulus_transport","(x1*x)*b","a*b","u*v"), "congr", "symm", "exact hd_witness_witness_right_right", "refl",
             *_call("totient_coprime_multiplication_prime_step","x","x3","x1","b","x2","v","u"), "exact hp", "exact hpred_witness", "exact hpb", "exact hphi_witness", "exact hprevious",
             "exact hselected"),
            "Induction on an actual beta-coded prime list proves multiplicativity; no sorting, supplied count, or omitted prime-factor case is assumed.",
        ),
        spec(
            "totient_coprime_multiplicative",
            f"forall a b u v. ({_phi('a','u',tag='multiplicative_first')}) -> ({_phi('b','v',tag='multiplicative_second')}) -> "
            f"({_cop('a','b',tag='multiplicative_coprime')}) -> ({_phi('a*b','u*v',tag='multiplicative_product')})",
            ("foundation_prime_factor_list_exists", "totient_coprime_multiplicative_from_prime_list"),
            (*_intro("a","b","u","v","hu","hv","hcop"), f"have hlist : exists l f g. {_factorization('a','f','g','l','multiplicative_actual_list')}",
             *_call("foundation_prime_factor_list_exists","a"), "cases hu", "exact hu_left", "cases hlist", "cases hlist_witness", "cases hlist_witness_witness", "cases hlist_witness_witness_witness", "cases hlist_witness_witness_witness_right",
             *_call("totient_coprime_multiplicative_from_prime_list","x","x1","x2","a","b","u","v"), "exact hlist_witness_witness_witness_right_right", "exact hlist_witness_witness_witness_right_left", "exact hu", "exact hv", "exact hcop"),
            "The actual totient is multiplicative for every pair of positive coprime moduli; the needed finite prime list is constructed, not supplied.",
        ),
    )


def make_euler_totient_algebra_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_prime_rows(spec), *_multiplicative_rows(spec))


__all__ = ["make_euler_totient_algebra_candidate_theorems"]
