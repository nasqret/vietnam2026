"""Constructive squarefree kernels with actual unique natural square roots.

Squarefree means positive and free of squared PRIME divisors, exactly at the
blueprint's bounded prime range.  The existence proof performs a finite
decidable search and strict descent, not an assumed maximal square factor.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_gcd_candidate import is_gcd
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _dvd, _intro, _le, _lt, _part, _parts, _prime,
    _public, _rewrite,
)


def _squarefree(n: str, tag: str) -> str:
    p = "sfd_prime_" + tag
    return _and(
        f"~(({n}) = 0)",
        f"forall {p}. ({_prime(p,tag+'domain')}) -> ({_le(p,n,tag+'bound')}) -> ~({_dvd(f'{p} * {p}',n,tag+'square')})",
    )


def _no_squares(n: str, L: str, tag: str) -> str:
    p = "sfd_search_prime_" + tag
    return f"forall {p}. ({_lt(p,L,tag+'bound')}) -> ({_prime(p,tag+'domain')}) -> ~({_dvd(f'{p} * {p}',n,tag+'square')})"


def _found_square(n: str, L: str, p: str, tag: str) -> str:
    return _and(_lt(p,L,tag+'bound'),_prime(p,tag+'prime'),_dvd(f"{p} * {p}",n,tag+'square'))


def _cop(a: str, b: str, tag: str) -> str:
    d = "sfd_common_divisor_" + tag
    return f"forall {d}. ({_dvd(d,a,tag+'left')}) -> ({_dvd(d,b,tag+'right')}) -> {d} = 1"


def _decomposition(n: str, r: str, s: str, tag: str) -> str:
    return _and(_squarefree(r,tag+'kernel'),f"({n}) = ({r}) * (({s}) * ({s}))")


def squarefree_relation(n: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Positive n with no squared prime divisor p at or below n."""
    return _public(_squarefree,(n,),tag=tag,variables=variables)


def squarefree_decomposition_relation(n: str, r: str, s: str, *, tag: str, variables: tuple[str,...]) -> str:
    """An actual squarefree kernel and natural square-factor root."""
    return _public(_decomposition,(n,r,s),tag=tag,variables=variables)


def _basic_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "divides_square_of_divides",
            f"forall a b. ({_dvd('a','b','square_source')}) -> ({_dvd('a * a','b * b','square_result')})",
            ("four_square_product_square",),
            _intro("a","b","hdiv")+("cases hdiv","exists x * x","rewrite hdiv_witness","rewrite hdiv_witness","apply four_square_product_square"),
            "Squaring an actual divisor witness produces an actual squared divisor witness.",
        ),
        spec(
            "squarefree_excludes_prime_square",
            f"forall n p. ({_squarefree('n','exclusion_squarefree')}) -> ({_prime('p','exclusion_prime')}) -> ({_dvd('p * p','n','exclusion_divisor')}) -> false",
            ("divisor_le_nonzero", "multiple_trans"),
            _intro("n","p","hsf","hp","hdiv")+("cases hsf",)+_call("hsf_right","p")+("exact hp",)
            +_call("divisor_le_nonzero","p","n")+("exact hsf_left",)+_call("multiple_trans","p * p","p","n")
            +("exact hdiv","exists p","refl","exact hdiv"),
            "A squared prime divisor cannot evade the bounded squarefree definition: its base prime is itself a divisor and is at most the positive input.",
        ),
        spec(
            "prime_square_ne_one",
            f"forall p. ({_prime('p','square_nonunit_prime')}) -> ~(p * p = 1)",
            ("divisor_one",),
            _intro("p","hp","heq")+("cases hp","apply hp_left",)+_call("divisor_one","p")+("exists p","symm","exact heq"),
            "The square of a genuine prime is never the unit.",
        ),
        spec(
            "squarefree_squared_divisor_is_one",
            f"forall n a. ({_squarefree('n','squared_divisor_sf')}) -> ({_dvd('a * a','n','squared_divisor_input')}) -> a = 1",
            ("eq_decidable", "prime_divisor_exists", "squarefree_excludes_prime_square", "multiple_trans", "divides_square_of_divides", "mul_zero_left"),
            _intro("n","a","hsf","hdiv")+("have hzero : a = 0 \\/ ~(a = 0)",)+_call("eq_decidable","a","0")+("cases hzero","exfalso","cases hsf","apply hsf_left","cases hdiv","trans (a * a) * x","exact hdiv_witness","rewrite hzero_left","rewrite hzero_left","simp [mul_zero_left]",
                "have hone : a = 1 \\/ ~(a = 1)")+_call("eq_decidable","a","1")+("cases hone","exact hone_left",
                f"have hp : exists p. ({_prime('p','squared_divisor_prime')}) /\\ ({_dvd('p','a','squared_divisor_prime_at')})")
            +_call("prime_divisor_exists","a")+("exact hzero_right","exact hone_right","cases hp","cases hp_witness","exfalso")
            +_call("squarefree_excludes_prime_square","n","x")+("exact hsf","exact hp_witness_left")
            +_call("multiple_trans","a * a","x * x","n")+("exact hdiv",)+_call("divides_square_of_divides","x","a")+("exact hp_witness_right",),
            "Every squared divisor of a positive squarefree number has root one, not merely prime roots.",
        ),
        spec(
            "coprime_squared_pair",
            f"forall a b. ({_cop('a','b','square_coprime_source')}) -> ({_cop('a * a','b * b','square_coprime_result')})",
            ("coprime_mul_left","coprime_mul_right"),
            _intro("a","b","hcop")+(f"have hleft : {_cop('a * a','b','square_coprime_left')}",)
            +_call("coprime_mul_left","a","a","b")+("exact hcop","exact hcop")
            +_call("coprime_mul_right","a * a","b","b")+("exact hleft","exact hleft"),
            "The squares of two coprime naturals are genuinely coprime.",
        ),
        spec(
            "squarefree_coprime_square_factor_is_one",
            f"forall n a b. ({_squarefree('n','coprime_square_sf')}) -> ({_cop('a','b','coprime_square_pair')}) -> ({_dvd('a * a','n * (b * b)','coprime_square_divisor')}) -> a = 1",
            ("squarefree_squared_divisor_is_one","gauss_coprime_cancel","coprime_squared_pair","mul_comm"),
            _intro("n","a","b","hsf","hcop","hdiv")+_call("squarefree_squared_divisor_is_one","n","a")+("exact hsf",)
            +_call("gauss_coprime_cancel","a * a","b * b","n")+_call("coprime_squared_pair","a","b")+("exact hcop","cases hdiv","exists x","trans n * (b * b)","apply mul_comm","exact hdiv_witness"),
            "Coprime cancellation turns a squared divisor of n times another square into a squared divisor of the squarefree n itself.",
        ),
        spec(
            "squarefree_square_factor_reassociate",
            "forall p r s. (p * p) * (r * (s * s)) = r * ((p * s) * (p * s))",
            ("mul_assoc","mul_comm","four_square_product_square"),
            _intro("p","r","s")+("trans ((p * p) * r) * (s * s)","symm","apply mul_assoc","trans (r * (p * p)) * (s * s)","congr","apply mul_comm","refl","trans r * ((p * p) * (s * s))","apply mul_assoc","congr","refl","symm","apply four_square_product_square"),
            "Restoring a prime-square factor multiplies the actual square root and preserves the squarefree kernel.",
        ),
        spec(
            "nonzero_square_factor_root",
            "forall n r s. ~(n = 0) -> n = r * (s * s) -> ~(s = 0)",
            (),
            _intro("n","r","s","hn","heq","hszero")+("apply hn","trans r * (s * s)","exact heq","rewrite hszero","rewrite hszero","simp"),
            "The square-root factor of a positive input is itself nonzero.",
        ),
    )


def _search_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    # The two last-prime branches have the same bounded index split, but
    # conclude contradiction from different ordinary decidable predicates.
    script = ["intro L","induction L","intro n","left",*_intro("p","hbound","hp","hdiv"),*_call("factor_permutation_below_zero_impossible","p"),"exact hbound","intro n","specialize IH n","cases IH","specialize prime_decidable L","cases prime_decidable","specialize multiple_decidable (L * L)","specialize multiple_decidable n","cases multiple_decidable","right","exists L","split",*_call("le_refl","S L"),"split","exact prime_decidable_left","exact multiple_decidable_left"]
    for prime_known in (True,False):
        script += ["left",*_intro("p","hbound","hp","hdiv"),f"have hcase : p = L \\/ ({_lt('p','L','search_case')})",*_call("finite_lt_succ_eq_or_lt","L","p"),"exact hbound","cases hcase"]
        if prime_known:
            script += ["rewrite hcase_left at hdiv","rewrite hcase_left at hdiv","apply multiple_decidable_right","exact hdiv"]
        else:
            script += [*_rewrite("hcase_left",_prime("p","search_prime_rewrite"),"p","hp"),"apply prime_decidable_right","exact hp"]
        script += [*_call("IH_left","p"),"exact hcase_right","exact hp","exact hdiv"]
    script += ["right","cases IH_right",*_parts("IH_right_witness",3),"exists x","split",*_call("le_succ","S x","L"),"exact IH_right_witness_left","split","exact IH_right_witness_right_left","exact IH_right_witness_right_right"]
    return (
        spec(
            "bounded_prime_square_divisor_search",
            f"forall L n. ({_no_squares('n','L','search_absent')}) \\/ exists p. ({_found_square('n','L','p','search_present')})",
            ("factor_permutation_below_zero_impossible","prime_decidable","multiple_decidable","le_refl","finite_lt_succ_eq_or_lt","le_succ"),
            tuple(script),
            "Finite induction decides absence of all squared prime divisors below any bound or constructs an actual bounded prime-square divisor.",
        ),
        spec(
            "squarefree_or_prime_square_divisor",
            f"forall n. ~(n = 0) -> ({_squarefree('n','decision_squarefree')}) \\/ exists p. ({_prime('p','decision_prime')}) /\\ ({_dvd('p * p','n','decision_divisor')})",
            ("bounded_prime_square_divisor_search","succ_le_succ"),
            _intro("n","hn")+(f"have hsearch : ({_no_squares('n','S n','decision_absent')}) \\/ exists p. ({_found_square('n','S n','p','decision_present')})",)
            +_call("bounded_prime_square_divisor_search","S n","n")+("cases hsearch","left","split","exact hn")
            +_intro("p","hp","hle","hdiv")+_call("hsearch_left","p")+_call("succ_le_succ","p","n")
            +("exact hle","exact hp","exact hdiv","right","cases hsearch_right")+_parts("hsearch_right_witness",3)
            +("exists x","split","exact hsearch_right_witness_right_left","exact hsearch_right_witness_right_right"),
            "Every positive input is squarefree or has a constructed actual prime-square divisor; no excluded-middle or factoring oracle is assumed.",
        ),
    )


def _existence_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    script = (
        _intro("B")+("induction B",)+_intro("n","hn","hbound")+("exfalso",)+_call("factor_permutation_below_zero_impossible","n")+("exact hbound",)
        +_intro("n","hn","hbound")+(f"have hcase : ({_squarefree('n','exists_decision')}) \\/ exists p. ({_prime('p','exists_prime')}) /\\ ({_dvd('p * p','n','exists_divisor')})",)
        +_call("squarefree_or_prime_square_divisor","n")+("exact hn","cases hcase","exists n","exists 1","split","exact hcase_left","symm","trans n * 1","congr","refl","apply mul_one","apply mul_one","cases hcase_right","cases hcase_right_witness","cases hcase_right_witness_right",
            "have hu : ~(x1 = 0)","intro hzero")+_call("factor_nonzero_right","n","x * x","x1")+("exact hn","exact hcase_right_witness_right_witness","exact hzero",f"have hsmall : {_lt('x1','n','exists_descent')}")
        +_call("proper_factor_lt","n","x1","x * x")+("exact hn","trans (x * x) * x1","exact hcase_right_witness_right_witness","apply mul_comm","intro hone")
        +_call("prime_square_ne_one","x")+("exact hcase_right_witness_left","exact hone",f"have hrec : exists r s. ({_decomposition('x1','r','s','exists_recursive')})")
        +_call("IH","x1")+("exact hu",)+_call("lt_of_lt_of_le","x1","n","B")+("exact hsmall",)+_call("le_of_succ_le_succ","n","B")+("exact hbound",)
        +_cases("hrec",2)+("cases hrec_witness_witness","exists x2","exists x * x3","split","exact hrec_witness_witness_left","trans (x * x) * x1","exact hcase_right_witness_right_witness","rewrite hrec_witness_witness_right","apply squarefree_square_factor_reassociate")
    )
    return (
        spec(
            "squarefree_decomposition_bounded_exists",
            f"forall B n. ~(n = 0) -> ({_lt('n','B','decomposition_bound')}) -> exists r s. ({_decomposition('n','r','s','decomposition_result')})",
            ("factor_permutation_below_zero_impossible","squarefree_or_prime_square_divisor","mul_one","factor_nonzero_right","proper_factor_lt","mul_comm","prime_square_ne_one","lt_of_lt_of_le","le_of_succ_le_succ","squarefree_square_factor_reassociate"),
            script,
            "Finite prime-square search and ordinary bounded induction construct the squarefree kernel and its square-factor root for every positive input.",
        ),
        spec(
            "squarefree_decomposition_exists",
            f"forall n. ~(n = 0) -> exists r s. ({_decomposition('n','r','s','unbounded_decomposition')})",
            ("squarefree_decomposition_bounded_exists","le_refl"),
            _intro("n","hn")+_call("squarefree_decomposition_bounded_exists","S n","n")+("exact hn",)+_call("le_refl","S n"),
            "Every positive natural is an actual squarefree natural times an actual natural square.",
        ),
    )


def _uniqueness_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "squarefree_one",
            _squarefree("1","one"),
            ("divisor_one","multiple_trans"),
            ("split","intro hz","apply PA1","exact hz")+_intro("p","hp","hle","hdiv")
            +("cases hp","apply hp_left",)+_call("divisor_one","p")+_call("multiple_trans","p * p","p","1")+("exact hdiv","exists p","refl"),
            "The unit is squarefree under the exact positive, prime-square-free definition.",
        ),
        spec(
            "squarefree_coprime_square_balance",
            f"forall r u a b. ({_squarefree('r','balance_left')}) -> ({_squarefree('u','balance_right')}) -> ({_cop('a','b','balance_coprime')}) -> r * (a * a) = u * (b * b) -> u = r /\\ (a = 1 /\\ b = 1)",
            ("squarefree_coprime_square_factor_is_one","coprime_symm","mul_comm","mul_one"),
            _intro("r","u","a","b","hr","hu","hcop","heq")+("have ha : a = 1",)
            +_call("squarefree_coprime_square_factor_is_one","u","a","b")+("exact hu","exact hcop","exists r","trans r * (a * a)","symm","exact heq","apply mul_comm","have hb : b = 1")
            +_call("squarefree_coprime_square_factor_is_one","r","b","a")+("exact hr",)+_call("coprime_symm","a","b")
            +("exact hcop","exists u","trans u * (b * b)","exact heq","apply mul_comm","split","rewrite ha at heq","rewrite ha at heq","rewrite hb at heq","rewrite hb at heq","have hone : 1 * 1 = 1","apply mul_one","rewrite hone at heq","rewrite hone at heq","have hrone : r * 1 = r","apply mul_one","rewrite hrone at heq","have huone : u * 1 = u","apply mul_one","rewrite huone at heq","symm","exact heq","split","exact ha","exact hb"),
            "Equal squarefree-times-square values with coprime square roots force both reduced roots to be one and both squarefree factors to agree.",
        ),
        spec(
            "squarefree_decomposition_functional",
            f"forall n r s u v. ~(n = 0) -> ({_squarefree('r','unique_first')}) -> ({_squarefree('u','unique_second')}) -> n = r * (s * s) -> n = u * (v * v) -> u = r /\\ v = s",
            ("nonzero_square_factor_root","canonical_gcd_exists","is_gcd_dvd_left","is_gcd_dvd_right","factor_nonzero_left","is_gcd_quotients_coprime_nonzero","four_square_descent_square_factor_cancel","squarefree_square_factor_reassociate","squarefree_coprime_square_balance","mul_one"),
            _intro("n","r","s","u","v","hn","hr","hu","heqr","hequ")
            +("have hsnonzero : ~(s = 0)","intro hz")+_call("nonzero_square_factor_root","n","r","s")+("exact hn","exact heqr","exact hz",
                f"have hg : exists g. ({is_gcd('g','s','v',tag='sfd_unique_gcd')})")
            +_call("canonical_gcd_exists","s","v")+("cases hg","have hs : exists A. s = x * A")+_call("is_gcd_dvd_left","x","s","v")
            +("exact hg_witness","cases hs","have hv : exists B. v = x * B")+_call("is_gcd_dvd_right","x","s","v")
            +("exact hg_witness","cases hv","have hgnonzero : ~(x = 0)","intro hgzero")+_call("factor_nonzero_left","s","x","x1")
            +("exact hsnonzero","exact hs_witness","exact hgzero",f"have hcop : {_cop('x1','x2','unique_coprime')}")
            +_call("is_gcd_quotients_coprime_nonzero","x","s","v","x1","x2")+("exact hg_witness","exact hgnonzero","exact hs_witness","exact hv_witness",
                "have hbalance : r * (x1 * x1) = u * (x2 * x2)")
            +_call("four_square_descent_square_factor_cancel","x","r * (x1 * x1)","u * (x2 * x2)")
            +("exact hgnonzero","trans n","trans r * ((x * x1) * (x * x1))","apply squarefree_square_factor_reassociate","trans r * (s * s)","rewrite hs_witness","rewrite hs_witness","refl","symm","exact heqr","trans u * (v * v)","exact hequ","trans u * ((x * x2) * (x * x2))","rewrite hv_witness","rewrite hv_witness","refl","symm","apply squarefree_square_factor_reassociate",
                "have hunit : u = r /\\ (x1 = 1 /\\ x2 = 1)")
            +_call("squarefree_coprime_square_balance","r","u","x1","x2")+("exact hr","exact hu","exact hcop","exact hbalance","cases hunit","cases hunit_right","split","exact hunit_left","trans x","rewrite hv_witness","rewrite hunit_right_right","apply mul_one","symm","rewrite hs_witness","rewrite hunit_right_left","apply mul_one"),
            "Gcd reduction, coprime square cancellation and squarefreeness prove literal uniqueness of both the squarefree kernel and its natural square-factor root.",
        ),
        spec(
            "squarefree_decomposition_exists_unique",
            f"forall n. ~(n = 0) -> exists r s. ({_decomposition('n','r','s','canonical_squarefree')}) /\\ forall u v. ({_decomposition('n','u','v','other_squarefree')}) -> u = r /\\ v = s",
            ("squarefree_decomposition_exists","squarefree_decomposition_functional"),
            _intro("n","hn")+(f"have hexists : exists r s. ({_decomposition('n','r','s','canonical_exists')})",)
            +_call("squarefree_decomposition_exists","n")+("exact hn",)+_cases("hexists",2)
            +("exists x","exists x1","split","exact hexists_witness_witness")+_intro("u","v","hother")
            +("cases hexists_witness_witness","cases hother")+_call("squarefree_decomposition_functional","n","x","x1","u","v")
            +("exact hn","exact hexists_witness_witness_left","exact hother_left","exact hexists_witness_witness_right","exact hother_right"),
            "For every positive n, construct n=r*s² with squarefree r and prove every other natural such pair is exactly (r,s), including n=1.",
        ),
    )


def make_squarefree_decomposition_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _basic_rows(spec)+_search_rows(spec)+_existence_rows(spec)+_uniqueness_rows(spec)


__all__ = ["squarefree_relation","squarefree_decomposition_relation","make_squarefree_decomposition_candidate_theorems"]
