"""Actual perfect-power roots and finite positive prime-exponent profiles.

Root existence is derived by strict prime-power cofactor descent in HA.
Finite profile and root-table witnesses are subsequently constructed from
that theorem; neither a root oracle nor an assumed exponent profile occurs
in the public positive-input existence endpoint.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_gcd_candidate import is_gcd
from .prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _dvd, _entries, _entry, _intro, _le, _lt, _part,
    _parts, _pow, _preserve, _prime, _product, _public, _rewrite, _strict_cofactor,
    _support, _support_exists, _val,
)
from .squarefree_decomposition_candidate import _decomposition, _squarefree


def _all_val_div(n: str, k: str, tag: str) -> str:
    p, e = "ppf_prime_"+tag, "ppf_exponent_"+tag
    return f"forall {p} {e}. ({_prime(p,tag+'domain')}) -> ({_val(p,n,e,tag+'valuation')}) -> ({_dvd(k,e,tag+'divides')})"


def _common(b: str, c: str, l: str, d: str, tag: str) -> str:
    i, e = "ppf_index_"+tag, "ppf_entry_"+tag
    return f"forall {i} {e}. ({_lt(i,l,tag+'bound')}) -> ({_at(b,c,i,e,tag+'entry')}) -> ({_dvd(d,e,tag+'divisor')})"


def _prefix_gcd(b: str, c: str, l: str, g: str, tag: str) -> str:
    d = "ppf_common_"+tag
    return _and(_common(b,c,l,g,tag+'common'),f"forall {d}. ({_common(b,c,l,d,tag+'other')}) -> ({_dvd(d,g,tag+'greatest')})")


def _root_available(n: str, g: str, tag: str) -> str:
    k, r = "ppf_degree_"+tag, "ppf_root_"+tag
    return f"forall {k}. ~({k} = 0) -> ({_dvd(k,g,tag+'divisor')}) -> exists {r}. ({_pow(r,k,n,tag+'power')})"


def _root_table_prefix(n: str, g: str, b: str, c: str, L: str, tag: str) -> str:
    k, r = "ppf_table_degree_"+tag, "ppf_table_root_"+tag
    return f"forall {k}. ({_lt(k,L,tag+'bound')}) -> ~({k} = 0) -> ({_dvd(k,g,tag+'divisor')}) -> exists {r}. ({_at(b,c,k,r,tag+'entry')}) /\\ ({_pow(r,k,n,tag+'power')})"


def _root_table(n: str, g: str, b: str, c: str, tag: str) -> str:
    k, r = "ppf_table_degree_"+tag, "ppf_table_root_"+tag
    return f"forall {k}. ~({k} = 0) -> ({_dvd(k,g,tag+'divisor')}) -> exists {r}. ({_at(b,c,k,r,tag+'entry')}) /\\ ({_pow(r,k,n,tag+'power')})"


def _pair(z: str, a: str, b: str) -> str:
    # The exact historical doubled-Cantor Pair relation, rendered for terms.
    return f"({z}) = (({a}) + ({b})) * S (({a}) + ({b})) + (({b}) + ({b}))"


def _profile_code(w: str, pb: str, pc: str, eb: str, ec: str, vb: str,
                  vc: str, l: str, g: str, rb: str, rc: str, tag: str) -> str:
    values = (pb,pc,eb,ec,vb,vc,l,g,rb,rc)
    intermediates = tuple(f"ppf_code_{i}_{tag}" for i in range(8))
    pairs = tuple(_pair(w if i == 0 else intermediates[i-1], values[i], intermediates[i]) for i in range(8))
    pairs += (_pair(intermediates[-1],values[-2],values[-1]),)
    return "exists " + " ".join(intermediates) + ". (" + _and(*pairs) + ")"


def _profile_data(n: str, w: str, pb: str, pc: str, eb: str, ec: str,
                  vb: str, vc: str, l: str, g: str, rb: str, rc: str, tag: str) -> str:
    return _and(
        f"~(({n}) = 1)", _profile_code(w,pb,pc,eb,ec,vb,vc,l,g,rb,rc,tag+'code'),
        _support(n,pb,pc,eb,ec,vb,vc,l,tag+'support'),
        _prefix_gcd(eb,ec,l,g,tag+'gcd'), f"~(({g}) = 0)",
        _root_table(n,g,rb,rc,tag+'roots'),
    )


def _unit_powers(tag: str) -> str:
    k = "ppf_unit_degree_"+tag
    return f"forall {k}. ~({k} = 0) -> ({_pow('1',k,'1',tag+'identity')})"


def _profile(n: str, w: str, tag: str) -> str:
    fields = tuple("ppf_"+role+"_"+tag for role in ("pb","pc","eb","ec","vb","vc","length","gcd","rb","rc"))
    unit = _and(f"({n}) = 1",f"({w}) = 0",_unit_powers(tag+'unit'))
    return f"({unit}) \\/ (exists {' '.join(fields)}. ({_profile_data(n,w,*fields,tag+'data')}))"


def prime_valuations_divisible_relation(n: str, k: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Every actual PRIME valuation of n is divisible by the positive root degree."""
    return _public(_all_val_div,(n,k),tag=tag,variables=variables)


def prime_exponent_prefix_gcd_relation(b: str, c: str, l: str, g: str, *, tag: str, variables: tuple[str,...]) -> str:
    """The ordinary greatest common divisor of all actual decoded exponents."""
    return _public(_prefix_gcd,(b,c,l,g),tag=tag,variables=variables)


def perfect_power_root_table_relation(n: str, g: str, b: str, c: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Actual beta-decoded roots at every positive degree dividing the exponent gcd."""
    return _public(_root_table,(n,g,b,c),tag=tag,variables=variables)


def perfect_power_profile_code_relation(w: str, pb: str, pc: str, eb: str, ec: str,
                                      vb: str, vc: str, l: str, g: str, rb: str, rc: str,
                                      *, tag: str, variables: tuple[str,...]) -> str:
    """A real nested historical Pair code for support, gcd and root-table data."""
    return _public(_profile_code,(w,pb,pc,eb,ec,vb,vc,l,g,rb,rc),tag=tag,variables=variables)


def perfect_power_profile_data_relation(n: str, w: str, pb: str, pc: str, eb: str, ec: str,
                                      vb: str, vc: str, l: str, g: str, rb: str, rc: str,
                                      *, tag: str, variables: tuple[str,...]) -> str:
    """Nonunit input and its actual encoded finite support, positive gcd and roots."""
    return _public(_profile_data,(n,w,pb,pc,eb,ec,vb,vc,l,g,rb,rc),tag=tag,variables=variables)


def perfect_power_profile_relation(n: str, w: str, *, tag: str, variables: tuple[str,...]) -> str:
    """The exact unit exception or genuinely coded nonunit prime-power profile."""
    return _public(_profile,(n,w),tag=tag,variables=variables)


def _power_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "power_value_eq_transport",
            f"forall a k u v. u = v -> ({_pow('a','k','u','transport_source')}) -> ({_pow('a','k','v','transport_target')})",
            (),
            _intro("a","k","u","v","heq","hpow")+_rewrite("heq",_pow("a","k","u","transport"),"u","hpow")+("exact hpow",),
            "Transport the actual terminal value of a power trace along equality.",
        ),
        spec(
            "power_one_base_value",
            f"forall k z. ({_pow('1','k','z','one_base')}) -> z = 1",
            ("pow_zero","pow_successor_decompose","mul_one"),
            _intro("k")+("induction k",)+_intro("z","hpow")+_call("pow_zero","1","0","z")+("refl","exact hpow",)
            +_intro("z","hpow")+(f"have hprev : exists r. ({_pow('1','k','r','one_previous')}) /\\ z = r * 1",)
            +_call("pow_successor_decompose","1","k","S k","z")+("refl","exact hpow","cases hprev","cases hprev_witness","have hone : x = 1")
            +_call("IH","x")+("exact hprev_witness_left","trans x * 1","exact hprev_witness_right","trans x","apply mul_one","exact hone"),
            "Every nonnegative power of the unit has value one, proved by ordinary exponent induction.",
        ),
        spec(
            "power_one_base_exists",
            f"forall k. ({_pow('1','k','1','uniform_unit')})",
            ("pow_exists","power_one_base_value","power_value_eq_transport"),
            _intro("k")+(f"have hex : exists z. ({_pow('1','k','z','one_total')})",)+_call("pow_exists","1","k")+("cases hex",)
            +_call("power_value_eq_transport","1","k","x","1")+_call("power_one_base_value","k","x")+("exact hex_witness","exact hex_witness"),
            "Construct the actual identity 1=1^k uniformly for all nonnegative exponents, in particular every positive exponent required by the n=1 profile.",
        ),
        spec(
            "power_product_construct",
            f"forall a b k u v. ({_pow('a','k','u','product_first')}) -> ({_pow('b','k','v','product_second')}) -> ({_pow('a * b','k','u * v','product_constructed')})",
            ("pow_exists","pow_mul_base","power_value_eq_transport"),
            _intro("a","b","k","u","v","hfirst","hsecond")+(f"have hex : exists z. ({_pow('a * b','k','z','product_total')})",)
            +_call("pow_exists","a * b","k")+("cases hex",)+_call("power_value_eq_transport","a * b","k","x","u * v")
            +_call("pow_mul_base","a","b","k","u","v","x")+("exact hfirst","exact hsecond","exact hex_witness","exact hex_witness"),
            "Two actual k-th power traces construct the power trace of the product of their roots.",
        ),
        spec(
            "power_divisible_exponent_root",
            f"forall p e k t P. e = k * t -> ({_pow('p','e','P','exponent_source')}) -> exists r. ({_pow('r','k','P','exponent_root')})",
            ("pow_exists","pow_mul_exp","mul_comm","power_value_eq_transport"),
            _intro("p","e","k","t","P","heq","hpow")+(f"have hroot : exists r. ({_pow('p','t','r','exponent_inner')})",)
            +_call("pow_exists","p","t")+("cases hroot",f"have houter : exists z. ({_pow('x','k','z','exponent_outer')})")
            +_call("pow_exists","x","k")+("cases houter","exists x",)+_call("power_value_eq_transport","x","k","x1","P")
            +_call("pow_mul_exp","p","t","k","e","x","x1","P")
            +("trans k * t","exact heq","apply mul_comm","exact hroot_witness","exact houter_witness","exact hpow","exact houter_witness"),
            "A witnessed exponent quotient constructs the corresponding natural root of an actual prime power; this algebraic lemma needs no prime assumption.",
        ),
        spec(
            "positive_power_nonzero_base",
            f"forall n k r. ~(n = 0) -> ~(k = 0) -> ({_pow('r','k','n','positive_output')}) -> ~(r = 0)",
            ("pow_positive_exponent_base_divides","mul_zero_left"),
            _intro("n","k","r","hn","hk","hpow","hr")+(f"have hdiv : {_dvd('r','n','positive_base_divisor')}",)
            +_call("pow_positive_exponent_base_divides","r","k","n")+("exact hk","exact hpow","cases hdiv","apply hn","trans r * x","exact hdiv_witness","rewrite hr","apply mul_zero_left"),
            "An actual positive-degree power with positive value has a nonzero natural base.",
        ),
        spec(
            "positive_power_prime_valuations_divisible",
            f"forall n k r. ~(n = 0) -> ~(k = 0) -> ({_pow('r','k','n','necessary_power')}) -> ({_all_val_div('n','k','necessary_valuations')})",
            ("positive_power_nonzero_base","power_valuation_exists","prime_power_valuation_pow_value"),
            _intro("n","k","r","hn","hk","hpow")+("have hr : ~(r = 0)","intro hz")
            +_call("positive_power_nonzero_base","n","k","r")+("exact hn","exact hk","exact hpow","exact hz")
            +_intro("p","e","hp","hval")+(f"have hbase : exists f. ({_val('p','r','f','necessary_base')})",)
            +_call("power_valuation_exists","p","r")+("cases hbase","exists x",)
            +_call("prime_power_valuation_pow_value","p","r","k","x","n","e")
            +("exact hp","exact hr","exact hbase_witness","exact hpow","exact hval"),
            "Every positive k-th power has every actual prime valuation divisible by k, with a constructed quotient valuation of its nonzero base.",
        ),
        spec(
            "prime_valuation_divisibility_cofactor",
            f"forall n k p e P u. ({_prime('p','cofactor_base')}) -> ~(u = 0) -> n = P * u -> ({_pow('p','e','P','cofactor_power')}) -> ~({_dvd('p','u','cofactor_fresh')}) -> ({_all_val_div('n','k','cofactor_source')}) -> ({_all_val_div('u','k','cofactor_target')})",
            ("eq_decidable","prime_valuation_zero_of_nondivisor","power_valuation_functional","power_valuation_value_eq_transport","prime_valuation_strip_other_prime"),
            _intro("n","k","p","e","P","u","hp","hu","heq","hpow","hfresh","hsource","q","f","hq","hval")
            +("have hcase : q = p \\/ ~(q = p)",)+_call("eq_decidable","q","p")+("cases hcase",)
            +_rewrite("hcase_left",_val("q","u","f","cofactor_same"),"q","hval")
            +("have hfzero : f = 0",)+_call("power_valuation_functional","p","u","f","0")+("exact hval",)
            +_call("prime_valuation_zero_of_nondivisor","p","u")+("exact hp","exact hu","exact hfresh","exists 0","rewrite hfzero","symm","apply PA5")
            +_call("hsource","q","f")+("exact hq",)+_call("power_valuation_value_eq_transport","q","P * u","n","f")
            +("symm","exact heq",)+_call("prime_valuation_strip_other_prime","p","q","e","P","u","f")
            +("exact hp","exact hq","exact hcase_right","exact hu","exact hpow","exact hval"),
            "If all input prime valuations are multiples of k, removing one full prime power leaves that same property on the strictly smaller cofactor.",
        ),
    )


def _root_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    fields = tuple(_part("hfactor"+"_witness"*4,8,i) for i in range(8))
    script = (
        _intro("B")+("induction B",)+_intro("n","k","hn","hk","hvalues","hbound")+("exfalso",)+_call("factor_permutation_below_zero_impossible","n")+("exact hbound",)
        +_intro("n","k","hn","hk","hvalues","hbound")+("have hcase : n = 1 \\/ ~(n = 1)",)+_call("eq_decidable","n","1")+("cases hcase","exists 1",)
        +_call("power_value_eq_transport","1","k","1","n")+("symm","exact hcase_left",)+_call("power_one_base_exists","k")
        +(f"have hfactor : exists p e P u. ({_strict_cofactor('n','p','e','P','u','root_factor')})",)+_call("prime_valuation_strict_cofactor_exists","n")
        +("exact hn","exact hcase_right",)+_cases("hfactor",4)+_parts("hfactor"+"_witness"*4,8)
        +(f"have hquotient : {_dvd('k','x1','root_exponent_quotient')}",)+_call("hvalues","x","x1")+(f"exact {fields[0]}",f"exact {fields[2]}","cases hquotient",
            f"have hpowerroot : exists r. ({_pow('r','k','x2','root_power_factor')})")
        +_call("power_divisible_exponent_root","x","x1","k","x4","x2")+("exact hquotient_witness",f"exact {fields[3]}","cases hpowerroot",
            f"have hrec : exists r. ({_pow('r','k','x3','root_recursive')})")
        +_call("IH","x3","k")+(f"exact {fields[5]}","exact hk",)
        +_call("prime_valuation_divisibility_cofactor","n","k","x","x1","x2","x3")
        +(f"exact {fields[0]}",f"exact {fields[5]}",f"exact {fields[4]}",f"exact {fields[3]}",f"exact {fields[6]}","exact hvalues")
        +_call("lt_of_lt_of_le","x3","n","B")+(f"exact {fields[7]}",)+_call("le_of_succ_le_succ","n","B")+("exact hbound","cases hrec","exists x5 * x6",)
        +_call("power_value_eq_transport","x5 * x6","k","x2 * x3","n")+("symm",f"exact {fields[4]}",)
        +_call("power_product_construct","x5","x6","k","x2","x3")+("exact hpowerroot_witness","exact hrec_witness")
    )
    return (
        spec(
            "prime_valuation_divisible_power_root_bounded",
            f"forall B n k. ~(n = 0) -> ~(k = 0) -> ({_all_val_div('n','k','root_divisibility')}) -> ({_lt('n','B','root_bound')}) -> exists r. ({_pow('r','k','n','root_result')})",
            ("factor_permutation_below_zero_impossible","eq_decidable","power_value_eq_transport","power_one_base_exists","prime_valuation_strict_cofactor_exists","power_divisible_exponent_root","prime_valuation_divisibility_cofactor","lt_of_lt_of_le","le_of_succ_le_succ","power_product_construct"),
            script,
            "Construct a k-th root from divisibility of every prime valuation by strict full-prime-power descent; every quotient and recursive root is actually derived.",
        ),
        spec(
            "prime_valuation_divisible_power_root_exists",
            f"forall n k. ~(n = 0) -> ~(k = 0) -> ({_all_val_div('n','k','root_unbounded_divisibility')}) -> exists r. ({_pow('r','k','n','root_unbounded_result')})",
            ("prime_valuation_divisible_power_root_bounded","le_refl"),
            _intro("n","k","hn","hk","hvalues")+_call("prime_valuation_divisible_power_root_bounded","S n","n","k")
            +("exact hn","exact hk","exact hvalues",)+_call("le_refl","S n"),
            "For every positive natural and positive degree, divisibility of all prime valuations constructs an actual natural root.",
        ),
    )


def _prefix_gcd_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "prime_exponent_common_divisor_drop",
            f"forall b c l d. ({_common('b','c','S l','d','common_successor')}) -> ({_common('b','c','l','d','common_previous')})",
            ("le_succ",),
            _intro("b","c","l","d","hcommon","i","e","hi","hat")+_call("hcommon","i","e")
            +_call("le_succ","S i","l")+("exact hi","exact hat"),
            "A common divisor of a successor beta prefix divides every entry of its predecessor.",
        ),
        spec(
            "prime_exponent_common_divisor_successor",
            f"forall b c l d v. ({_common('b','c','l','d','common_old')}) -> ({_at('b','c','l','v','common_last')}) -> ({_dvd('d','v','common_last_divides')}) -> ({_common('b','c','S l','d','common_next')})",
            ("finite_lt_succ_eq_or_lt","beta_at_unique"),
            _intro("b","c","l","d","v","hcommon","hlast","hdiv","i","e","hi","hat")
            +(f"have hcase : i = l \\/ ({_lt('i','l','common_case')})",)+_call("finite_lt_succ_eq_or_lt","l","i")
            +("exact hi","cases hcase",)+_rewrite("hcase_left",_at("b","c","i","e","common_at"),"i","hat")
            +("have heq : e = v",)+_call("beta_at_unique","b","c","l","e","v")+("exact hat","exact hlast","rewrite heq","exact hdiv")
            +_call("hcommon","i","e")+("exact hcase_right","exact hat"),
            "A common divisor and its actual final divisibility witness extend to the entire successor prefix.",
        ),
        spec(
            "prime_exponent_common_divisor_factor",
            f"forall b c l g d. ({_common('b','c','l','g','common_multiple')}) -> ({_dvd('d','g','common_factor')}) -> ({_common('b','c','l','d','common_factored')})",
            ("multiple_trans",),
            _intro("b","c","l","g","d","hcommon","hdiv","i","e","hi","hat")+_call("multiple_trans","g","d","e")
            +_call("hcommon","i","e")+("exact hi","exact hat","exact hdiv"),
            "Every divisor of a common divisor is an actual common divisor of the same finite exponent list.",
        ),
        spec(
            "prime_exponent_prefix_gcd_empty",
            f"forall b c. ({_prefix_gcd('b','c','0','0','empty_gcd')})",
            ("factor_permutation_below_zero_impossible",),
            _intro("b","c")+("split",)+_intro("i","e","hi","hat")+("exfalso",)+_call("factor_permutation_below_zero_impossible","i")
            +("exact hi","intro d","intro hcommon","exists 0","symm","apply PA5"),
            "The empty exponent prefix has greatest common divisor zero, including all common divisors of the empty family.",
        ),
        spec(
            "prime_exponent_prefix_gcd_successor",
            f"forall b c l g v h. ({_prefix_gcd('b','c','l','g','gcd_prefix')}) -> ({_at('b','c','l','v','gcd_last')}) -> ({is_gcd('h','g','v',tag='ppf_gcd_merge')}) -> ({_prefix_gcd('b','c','S l','h','gcd_successor')})",
            ("is_gcd_dvd_left","is_gcd_dvd_right","prime_exponent_common_divisor_factor","prime_exponent_common_divisor_successor","is_gcd_greatest","prime_exponent_common_divisor_drop","le_refl"),
            _intro("b","c","l","g","v","h","hprefix","hlast","hmerge")+("cases hprefix","split",)
            +_call("prime_exponent_common_divisor_successor","b","c","l","h","v")
            +_call("prime_exponent_common_divisor_factor","b","c","l","g","h")+("exact hprefix_left",)
            +_call("is_gcd_dvd_left","h","g","v")+("exact hmerge","exact hlast",)+_call("is_gcd_dvd_right","h","g","v")+("exact hmerge",)
            +_intro("d","hcommon")+_call("is_gcd_greatest","h","g","v","d")+("exact hmerge",)+_call("hprefix_right","d")
            +_call("prime_exponent_common_divisor_drop","b","c","l","d")+("exact hcommon",)+_call("hcommon","l","v")
            +_call("le_refl","S l")+("exact hlast",),
            "The canonical gcd of the old actual prefix gcd and final decoded exponent is the gcd of the successor prefix.",
        ),
        spec(
            "prime_exponent_prefix_gcd_exists",
            f"forall l b c. exists g. ({_prefix_gcd('b','c','l','g','gcd_exists')})",
            ("prime_exponent_prefix_gcd_empty","beta_at_exists","canonical_gcd_exists","prime_exponent_prefix_gcd_successor"),
            _intro("l")+("induction l",)+_intro("b","c")+("exists 0",)+_call("prime_exponent_prefix_gcd_empty","b","c")
            +_intro("b","c")+(f"have hprev : exists g. ({_prefix_gcd('b','c','l','g','gcd_previous')})",)+_call("IH","b","c")
            +("cases hprev",f"have hlast : exists v. ({_at('b','c','l','v','gcd_terminal')})")+_call("beta_at_exists","b","c","l")
            +("cases hlast",f"have hmerge : exists h. ({is_gcd('h','x','x1',tag='ppf_gcd_construct')})")+_call("canonical_gcd_exists","x","x1")
            +("cases hmerge","exists x2",)+_call("prime_exponent_prefix_gcd_successor","b","c","l","x","x1","x2")
            +("exact hprev_witness","exact hlast_witness","exact hmerge_witness"),
            "Ordinary finite induction constructs a genuine gcd of every actual beta prefix, including empty and zero-entry prefixes.",
        ),
        spec(
            "prime_exponent_prefix_gcd_functional",
            f"forall b c l g h. ({_prefix_gcd('b','c','l','g','gcd_unique_first')}) -> ({_prefix_gcd('b','c','l','h','gcd_unique_second')}) -> g = h",
            ("multiple_antisymm",),
            _intro("b","c","l","g","h","hfirst","hsecond")+("cases hfirst","cases hsecond",)+_call("multiple_antisymm","g","h")
            +_call("hsecond_right","g")+("exact hfirst_left",)+_call("hfirst_right","h")+("exact hsecond_left",),
            "The finite exponent gcd is literally unique by mutual actual divisibility.",
        ),
    )


def _support_gcd_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    codes = ("pb","pc","eb","ec","vb","vc","l")
    fields = tuple(_part("hrow"+"_witness"*3,7,i) for i in range(7))
    s = tuple(_part("hsupport",5,i) for i in range(5))
    return (
        spec(
            "prime_valuation_support_nonempty",
            f"forall n pb pc eb ec vb vc l. ({_support('n',*codes,'nonempty_support')}) -> ~(n = 1) -> ~(l = 0)",
            ("beta_product_zero",),
            _intro("n",*codes,"hsupport","hunit","hzero")+_parts("hsupport",5)
            +_rewrite("hzero",_product("vb","vc","l","n","nonempty_product"),"l",s[4])
            +("apply hunit",)+_call("beta_product_zero","vb","vc","n")+(f"exact {s[4]}",),
            "A positive nonunit cannot have an empty actual prime-power support, since its empty product would be one.",
        ),
        spec(
            "prime_valuation_support_exponent_gcd_nonzero",
            f"forall n pb pc eb ec vb vc l g. ({_support('n',*codes,'positive_gcd_support')}) -> ~(n = 1) -> ({_prefix_gcd('eb','ec','l','g','positive_gcd_graph')}) -> ~(g = 0)",
            ("prime_valuation_support_nonempty","one_le_of_ne_zero","mul_zero_left"),
            _intro("n",*codes,"g","hsupport","hunit","hgcd","hgzero")
            +(f"have hbound : {_lt('0','l','positive_first_index')}",)+_call("one_le_of_ne_zero","l")+("intro hlzero",)
            +_call("prime_valuation_support_nonempty","n",*codes)+("exact hsupport","exact hunit","exact hlzero",)+_parts("hsupport",5)
            +(f"have hrow : exists p e v. ({_entry('n',*codes[:6],'0','p','e','v','positive_gcd_entry')})",)+_call(s[2],"0")+("exact hbound",)
            +_cases("hrow",3)+_parts("hrow"+"_witness"*3,7)
            +("cases hgcd",f"have hdiv : {_dvd('g','x1','positive_gcd_divisor')}")+_call("hgcd_left","0","x1")
            +("exact hbound",f"exact {fields[1]}","cases hdiv",f"apply {fields[4]}","trans g * x3","exact hdiv_witness","rewrite hgzero","apply mul_zero_left"),
            "The actual gcd of the positive valuations of a nonunit is positive; a decoded positive exponent prevents a zero gcd.",
        ),
        spec(
            "prime_exponent_entry_has_prime_valuation",
            f"forall n pb pc eb ec vb vc l i e. ({_entries('n',*codes,'decoded_exponents')}) -> ({_lt('i','l','decoded_index')}) -> ({_at('eb','ec','i','e','decoded_exponent')}) -> exists p. ({_prime('p','decoded_prime')}) /\\ ({_val('p','n','e','decoded_valuation')})",
            ("beta_at_unique",),
            _intro("n",*codes,"i","e","hentries","hi","hat")
            +(f"have hrow : exists p f v. ({_entry('n',*codes[:6],'i','p','f','v','decoded_chosen')})",)+_call("hentries","i")+("exact hi",)
            +_cases("hrow",3)+_parts("hrow"+"_witness"*3,7)
            +("have heq : e = x1",)+_call("beta_at_unique","eb","ec","i","e","x1")
            +("exact hat",f"exact {fields[1]}","exists x","split",f"exact {fields[3]}")
            +_rewrite("heq",_val("x","n","e","decoded_final"),"e")+(f"exact {fields[5]}",),
            "Every actual decoded exponent belongs to an actual prime and its exact valuation of the input.",
        ),
        spec(
            "prime_support_common_divisor_implies_all_valuations",
            f"forall n pb pc eb ec vb vc l k. ({_support('n',*codes,'common_support')}) -> ({_common('eb','ec','l','k','common_exponents')}) -> ({_all_val_div('n','k','common_all_primes')})",
            ("eq_decidable","power_valuation_nonzero_exponent_divides_base","beta_at_unique","power_valuation_functional"),
            _intro("n",*codes,"k","hsupport","hcommon","p","e","hp","hval")
            +("have hcase : e = 0 \\/ ~(e = 0)",)+_call("eq_decidable","e","0")+("cases hcase","exists 0","rewrite hcase_left","symm","apply PA5",)+_parts("hsupport",5)
            +(f"have hmember : exists i. ({_lt('i','l','all_valuation_member_bound')}) /\\ ({_at('pb','pc','i','p','all_valuation_member_at')})",)
            +_call(s[3],"p")+("exact hp",)+_call("power_valuation_nonzero_exponent_divides_base","p","n","e")
            +("exact hval","exact hcase_right","cases hmember","cases hmember_witness",
                f"have hrow : exists q f v. ({_entry('n',*codes[:6],'x','q','f','v','all_valuation_row')})")
            +_call(s[2],"x")+("exact hmember_witness_left",)+_cases("hrow",3)+_parts("hrow"+"_witness"*3,7)
            +("have hprimeeq : p = x1",)+_call("beta_at_unique","pb","pc","x","p","x1")
            +("exact hmember_witness_right",f"exact {fields[0]}")+_rewrite("hprimeeq",_val("p","n","e","all_valuation_original"),"p","hval")
            +("have hexpeq : e = x2",)+_call("power_valuation_functional","x1","n","e","x2")
            +("exact hval",f"exact {fields[5]}","rewrite hexpeq",)+_call("hcommon","x","x2")
            +("exact hmember_witness_left",f"exact {fields[1]}"),
            "Dividing all listed positive valuations implies dividing every prime valuation, using actual support coverage and zero valuation for absent primes.",
        ),
        spec(
            "prime_support_all_valuations_implies_common_divisor",
            f"forall n pb pc eb ec vb vc l k. ({_support('n',*codes,'all_support')}) -> ({_all_val_div('n','k','all_valuation_hypothesis')}) -> ({_common('eb','ec','l','k','all_common_exponents')})",
            ("prime_exponent_entry_has_prime_valuation",),
            _intro("n",*codes,"k","hsupport","hall","i","e","hi","hat")+_parts("hsupport",5)
            +(f"have hex : exists p. ({_prime('p','all_chosen_prime')}) /\\ ({_val('p','n','e','all_chosen_valuation')})",)
            +_call("prime_exponent_entry_has_prime_valuation","n",*codes,"i","e")+(f"exact {s[2]}","exact hi","exact hat","cases hex","cases hex_witness")
            +_call("hall","x","e")+("exact hex_witness_left","exact hex_witness_right"),
            "Dividing every actual prime valuation implies being a common divisor of the actual finite exponent prefix.",
        ),
        spec(
            "prime_support_exponent_gcd_divisor_criterion",
            f"forall n pb pc eb ec vb vc l g k. ({_support('n',*codes,'criterion_support')}) -> ({_prefix_gcd('eb','ec','l','g','criterion_gcd')}) -> (({_dvd('k','g','criterion_divisor_first')}) -> ({_all_val_div('n','k','criterion_all_first')})) /\\ (({_all_val_div('n','k','criterion_all_second')}) -> ({_dvd('k','g','criterion_divisor_second')}))",
            ("prime_support_common_divisor_implies_all_valuations","prime_exponent_common_divisor_factor","prime_support_all_valuations_implies_common_divisor"),
            _intro("n",*codes,"g","k","hsupport","hgcd")+("cases hgcd","split","intro hdiv")
            +_call("prime_support_common_divisor_implies_all_valuations","n",*codes,"k")+("exact hsupport",)
            +_call("prime_exponent_common_divisor_factor","eb","ec","l","g","k")+("exact hgcd_left","exact hdiv","intro hall")
            +_call("hgcd_right","k")+_call("prime_support_all_valuations_implies_common_divisor","n",*codes,"k")+("exact hsupport","exact hall"),
            "A degree divides the finite exponent gcd exactly when it divides every prime valuation of the input.",
        ),
        spec(
            "prime_support_perfect_power_iff_degree_divides",
            f"forall n pb pc eb ec vb vc l g k. ({_support('n',*codes,'power_iff_support')}) -> ({_prefix_gcd('eb','ec','l','g','power_iff_gcd')}) -> ~(k = 0) -> ((exists r. ({_pow('r','k','n','power_iff_forward')})) -> ({_dvd('k','g','power_iff_divisor_first')})) /\\ (({_dvd('k','g','power_iff_divisor_second')}) -> exists r. ({_pow('r','k','n','power_iff_reverse')}))",
            ("prime_support_exponent_gcd_divisor_criterion","positive_power_prime_valuations_divisible","prime_valuation_divisible_power_root_exists"),
            _intro("n",*codes,"g","k","hsupport","hgcd","hk")
            +(f"have hcriterion : (({_dvd('k','g','power_criterion_divisor_first')}) -> ({_all_val_div('n','k','power_criterion_all_first')})) /\\ (({_all_val_div('n','k','power_criterion_all_second')}) -> ({_dvd('k','g','power_criterion_divisor_second')}))",)
            +_call("prime_support_exponent_gcd_divisor_criterion","n",*codes,"g","k")+("exact hsupport","exact hgcd","cases hcriterion","cases hsupport","split","intro hroot","cases hroot","apply hcriterion_right")
            +_call("positive_power_prime_valuations_divisible","n","k","x")+("exact hsupport_left","exact hk","exact hroot_witness","intro hdiv")
            +_call("prime_valuation_divisible_power_root_exists","n","k")+("exact hsupport_left","exact hk","apply hcriterion_left","exact hdiv"),
            "The positive perfect-power degrees are exactly the divisors of the actual finite exponent gcd; the reverse direction constructs a real root.",
        ),
        spec(
            "prime_support_exponent_gcd_roots_available",
            f"forall n pb pc eb ec vb vc l g. ({_support('n',*codes,'available_support')}) -> ({_prefix_gcd('eb','ec','l','g','available_gcd')}) -> ({_root_available('n','g','available_roots')})",
            ("prime_support_perfect_power_iff_degree_divides",),
            _intro("n",*codes,"g","hsupport","hgcd","k","hk","hdiv")
            +(f"have hiff : ((exists r. ({_pow('r','k','n','available_forward')})) -> ({_dvd('k','g','available_divisor_first')})) /\\ (({_dvd('k','g','available_divisor_second')}) -> exists r. ({_pow('r','k','n','available_reverse')}))",)
            +_call("prime_support_perfect_power_iff_degree_divides","n",*codes,"g","k")+("exact hsupport","exact hgcd","exact hk","cases hiff","apply hiff_right","exact hdiv"),
            "Each positive divisor of the actual exponent gcd has a constructively available actual root, ready for finite beta tabulation.",
        ),
    )


def _table_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "perfect_power_root_table_prefix_append",
            f"forall n g b c d e L R. ({_root_table_prefix('n','g','b','c','L','table_previous')}) -> ({_preserve('b','c','d','e','L','table_preserve')}) -> ({_at('d','e','L','R','table_last')}) -> (~(L = 0) -> ({_dvd('L','g','table_last_divisor')}) -> ({_pow('R','L','n','table_last_power')})) -> ({_root_table_prefix('n','g','d','e','S L','table_next')})",
            ("finite_lt_succ_eq_or_lt",),
            _intro("n","g","b","c","d","e","L","R","hprevious","hpreserve","hlast","hroot","k","hkbound","hk","hdiv")
            +(f"have hcase : k = L \\/ ({_lt('k','L','table_case')})",)+_call("finite_lt_succ_eq_or_lt","L","k")+("exact hkbound","cases hcase","exists R","split")
            +_rewrite("hcase_left",_at("d","e","k","R","table_final_at"),"k")+("exact hlast",)
            +_rewrite("hcase_left",_pow("R","k","n","table_final_power"),"k")+("apply hroot","intro hLzero","apply hk","trans L","exact hcase_left","exact hLzero","rewrite hcase_left at hdiv","exact hdiv",
                f"have hentry : exists r. ({_at('b','c','k','r','table_old_at')}) /\\ ({_pow('r','k','n','table_old_power')})")
            +_call("hprevious","k")+("exact hcase_right","exact hk","exact hdiv","cases hentry","cases hentry_witness","exists x","split")
            +_call("hpreserve","k","x")+("exact hcase_right","exact hentry_witness_left","exact hentry_witness_right"),
            "Append one actual conditional root and preserve all earlier actual decoded roots in a beta prefix.",
        ),
        spec(
            "perfect_power_root_table_conditional_entry",
            f"forall n g L. ({_root_available('n','g','table_available')}) -> exists R. ~(L = 0) -> ({_dvd('L','g','table_degree_divisor')}) -> ({_pow('R','L','n','table_selected_root')})",
            ("eq_decidable","multiple_decidable"),
            _intro("n","g","L","havailable")+("have hzero : L = 0 \\/ ~(L = 0)",)+_call("eq_decidable","L","0")
            +("cases hzero","exists 0","intro hL","intro hdiv","exfalso","apply hL","exact hzero_left",
                f"have hdiv : ({_dvd('L','g','table_decidable_divisor')}) \\/ ~({_dvd('L','g','table_decidable_nondivisor')})")
            +_call("multiple_decidable","L","g")+("cases hdiv",f"have hroot : exists R. ({_pow('R','L','n','table_chosen')})")
            +_call("havailable","L")+("exact hzero_right","exact hdiv_left","cases hroot","exists x","intro hL","intro hdivisor","exact hroot_witness","exists 0","intro hL","intro hdivisor","exfalso","apply hdiv_right","exact hdivisor"),
            "Decidable degree-zero and divisor tests construct a real root where required and a harmless zero filler elsewhere.",
        ),
        spec(
            "perfect_power_root_table_prefix_exists",
            f"forall L n g. ({_root_available('n','g','table_prefix_available')}) -> exists b c. ({_root_table_prefix('n','g','b','c','L','table_prefix_constructed')})",
            ("factor_permutation_below_zero_impossible","perfect_power_root_table_conditional_entry","beta_prefix_extend","perfect_power_root_table_prefix_append"),
            _intro("L")+("induction L",)+_intro("n","g","havailable")+("exists 0","exists 0",)+_intro("k","hbound","hk","hdiv")
            +("exfalso",)+_call("factor_permutation_below_zero_impossible","k")+("exact hbound",)
            +_intro("n","g","havailable")+(f"have hroot : exists R. ~(L = 0) -> ({_dvd('L','g','prefix_conditional_divisor')}) -> ({_pow('R','L','n','prefix_conditional_power')})",)
            +_call("perfect_power_root_table_conditional_entry","n","g","L")+("exact havailable","cases hroot",
                f"have hprevious : exists b c. ({_root_table_prefix('n','g','b','c','L','table_prefix_previous')})")
            +_call("IH","n","g")+("exact havailable",)+_cases("hprevious",2)
            +(f"have hextend : exists b c. ({_at('b','c','L','x','table_prefix_last')}) /\\ ({_preserve('x1','x2','b','c','L','table_prefix_preserve')})",)
            +_call("beta_prefix_extend","L","x1","x2","x")+_cases("hextend",2)+("cases hextend_witness_witness","exists x3","exists x4",)
            +_call("perfect_power_root_table_prefix_append","n","g","x1","x2","x3","x4","L","x")
            +("exact hprevious_witness_witness","exact hextend_witness_witness_right","exact hextend_witness_witness_left","exact hroot_witness"),
            "Finite induction constructs an actual beta table from the already proved pointwise root theorem, without any finite-choice axiom.",
        ),
        spec(
            "perfect_power_root_table_exists",
            f"forall n g. ~(g = 0) -> ({_root_available('n','g','complete_table_available')}) -> exists b c. ({_root_table('n','g','b','c','complete_table')})",
            ("perfect_power_root_table_prefix_exists","divisor_le_nonzero","succ_le_succ"),
            _intro("n","g","hg","havailable")+(f"have htable : exists b c. ({_root_table_prefix('n','g','b','c','S g','complete_prefix')})",)
            +_call("perfect_power_root_table_prefix_exists","S g","n","g")+("exact havailable",)+_cases("htable",2)
            +("exists x","exists x1",)+_intro("k","hk","hdiv")+_call("htable_witness_witness","k")
            +_call("succ_le_succ","k","g")+_call("divisor_le_nonzero","k","g")+("exact hg","exact hdiv","exact hk","exact hdiv"),
            "A positive gcd bounds all its positive divisors, so a finite table through index g covers every perfect-power degree.",
        ),
    )


def _profile_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    fields = ("pb","pc","eb","ec","vb","vc","l","g","rb","rc")
    code_script = list(_intro(*fields))
    for i in reversed(range(9)):
        right = fields[9] if i == 8 else ("x" if i == 7 else "x"+str(7-i))
        code_script += [f"have hpair{i} : exists z. ({_pair('z',fields[i],right)})", *_call("pair_code_constructor",fields[i],right), f"cases hpair{i}"]
    code_script += ["exists x8",*("exists x"+str(i) if i else "exists x" for i in reversed(range(8)))]
    for i in range(8):
        code_script += ["split",f"exact hpair{i}_witness"]
    code_script += ["exact hpair8_witness"]
    chosen = ("x",) + tuple("x"+str(i) for i in range(1,10))
    support = "hsupport"+"_witness"*7
    data_fields = tuple(_part("hdata",6,i) for i in range(6))
    return (
        spec(
            "perfect_power_profile_code_exists",
            f"forall {' '.join(fields)}. exists w. ({_profile_code('w',*fields,'code_constructed')})",
            ("pair_code_constructor",),
            tuple(code_script),
            "Nine actual historical Pair constructors package the ten finite data fields without expanding a huge nested arithmetic numeral.",
        ),
        spec(
            "perfect_power_profile_exists",
            f"forall n. ~(n = 0) -> exists w. ({_profile('n','w','profile_constructed')})",
            ("eq_decidable","power_one_base_exists","prime_valuation_support_exists","prime_exponent_prefix_gcd_exists","prime_valuation_support_exponent_gcd_nonzero","prime_support_exponent_gcd_roots_available","perfect_power_root_table_exists","perfect_power_profile_code_exists"),
            _intro("n","hn")+("have hcase : n = 1 \\/ ~(n = 1)",)+_call("eq_decidable","n","1")
            +("cases hcase","exists 0","left","split","exact hcase_left","split","refl","intro k","intro hk")+_call("power_one_base_exists","k")
            +(f"have hsupport : {_support_exists('n','profile_support')}",)+_call("prime_valuation_support_exists","n")+("exact hn",)+_cases("hsupport",7)
            +(f"have hgcd : exists g. ({_prefix_gcd('x2','x3','x6','g','profile_gcd')})",)+_call("prime_exponent_prefix_gcd_exists","x6","x2","x3")
            +("cases hgcd","have hgpositive : ~(x7 = 0)","intro hz")+_call("prime_valuation_support_exponent_gcd_nonzero","n",*chosen[:7],"x7")
            +(f"exact {support}","exact hcase_right","exact hgcd_witness","exact hz",f"have havailable : {_root_available('n','x7','profile_roots_available')}")
            +_call("prime_support_exponent_gcd_roots_available","n",*chosen[:7],"x7")+(f"exact {support}","exact hgcd_witness",
                f"have htable : exists b c. ({_root_table('n','x7','b','c','profile_root_table')})")
            +_call("perfect_power_root_table_exists","n","x7")+("exact hgpositive","exact havailable",)+_cases("htable",2)
            +(f"have hcode : exists w. ({_profile_code('w',*chosen,'profile_full_code')})",)+_call("perfect_power_profile_code_exists",*chosen)
            +("cases hcode","exists x10","right",)+tuple("exists "+v for v in chosen)
            +("split","exact hcase_right","split","exact hcode_witness","split",f"exact {support}","split","exact hgcd_witness","split","exact hgpositive","exact htable_witness_witness"),
            "Every positive input constructs a real profile code: the uniform unit case or finite distinct valuations, their positive gcd and actual roots for every positive divisor of that gcd.",
        ),
        spec(
            "perfect_power_profile_data_degree_classification",
            f"forall n w {' '.join(fields)} k. ({_profile_data('n','w',*fields,'encoded_classification')}) -> ~(k = 0) -> ((exists r. ({_pow('r','k','n','encoded_forward')})) -> ({_dvd('k','g','encoded_divisor_first')})) /\\ (({_dvd('k','g','encoded_divisor_second')}) -> exists r. ({_pow('r','k','n','encoded_reverse')}))",
            ("prime_support_perfect_power_iff_degree_divides",),
            _intro("n","w",*fields,"k","hdata","hk")+_parts("hdata",6)
            +_call("prime_support_perfect_power_iff_degree_divides","n",*fields[:7],"g","k")
            +(f"exact {data_fields[2]}",f"exact {data_fields[3]}","exact hk"),
            "The gcd actually decoded from the supplied profile code classifies all positive perfect-power degrees in both directions.",
        ),
        spec(
            "perfect_power_profile_data_root_lookup",
            f"forall n w {' '.join(fields)} k. ({_profile_data('n','w',*fields,'lookup_data')}) -> ~(k = 0) -> ({_dvd('k','g','lookup_degree')}) -> exists r. ({_at('rb','rc','k','r','lookup_decoded')}) /\\ ({_pow('r','k','n','lookup_power')})",
            (),
            _intro("n","w",*fields,"k","hdata","hk","hdiv")+_parts("hdata",6)+_call(data_fields[5],"k")+("exact hk","exact hdiv"),
            "A permitted positive degree retrieves an actual beta-decoded natural root from the constructed profile table, not a supplied arithmetic root.",
        ),
        spec(
            "perfect_power_profile_positive",
            f"forall n w. ({_profile('n','w','profile_domain')}) -> ~(n = 0)",
            (),
            _intro("n","w","hprofile","hnzero")+("cases hprofile","cases hprofile_left","rewrite hprofile_left_left at hnzero","apply PA1","exact hnzero")
            +_cases("hprofile_right",10)+_parts("hprofile_right"+"_witness"*10,6)
            +(f"cases {_part('hprofile_right'+'_witness'*10,6,2)}",f"apply {_part('hprofile_right'+'_witness'*10,6,2)}_left","exact hnzero"),
            "Every profile really describes a positive input; zero is excluded by both branches of the definition.",
        ),
        spec(
            "perfect_power_profile_unit_code",
            f"forall w. ({_profile('1','w','profile_unit_boundary')}) -> w = 0",
            (),
            _intro("w","hprofile")+("cases hprofile","cases hprofile_left","cases hprofile_left_right","exact hprofile_left_right_left")
            +_cases("hprofile_right",10)+_parts("hprofile_right"+"_witness"*10,6)
            +("exfalso",f"apply {_part('hprofile_right'+'_witness'*10,6,0)}","refl"),
            "The unit has exactly the distinguished uniform-identity profile tag, never a fictitious finite positive gcd of an empty valuation list.",
        ),
        spec(
            "perfect_power_profile_nonunit_decode",
            f"forall n w. ({_profile('n','w','profile_decode')}) -> ~(n = 1) -> exists {' '.join(fields)}. ({_profile_data('n','w',*fields,'profile_decoded_data')})",
            (),
            _intro("n","w","hprofile","hunit")+("cases hprofile","cases hprofile_left","exfalso","apply hunit","exact hprofile_left_left","exact hprofile_right"),
            "Every nonunit profile exposes real decoded support, positive gcd and root-table data; the unit exception cannot masquerade as a finite gcd profile.",
        ),
        spec(
            "positive_squarefree_kernel_and_power_profile",
            f"forall n. ~(n = 0) -> exists r s w. ({_squarefree('r','campaign_kernel')}) /\\ (n = r * (s * s) /\\ (({_profile('n','w','campaign_profile')}) /\\ forall u v. ({_squarefree('u','campaign_other_kernel')}) -> n = u * (v * v) -> u = r /\\ v = s))",
            ("squarefree_decomposition_exists_unique","perfect_power_profile_exists"),
            _intro("n","hn")
            +(f"have hkernel : exists r s. ({_decomposition('n','r','s','campaign_decomposition')}) /\\ forall u v. ({_decomposition('n','u','v','campaign_other_decomposition')}) -> u = r /\\ v = s",)
            +_call("squarefree_decomposition_exists_unique","n")+("exact hn",)+_cases("hkernel",2)+("cases hkernel_witness_witness","cases hkernel_witness_witness_left",
                f"have hprofile : exists w. ({_profile('n','w','campaign_profile_exists')})")
            +_call("perfect_power_profile_exists","n")+("exact hn","cases hprofile","exists x","exists x1","exists x2","split","exact hkernel_witness_witness_left_left","split","exact hkernel_witness_witness_left_right","split","exact hprofile_witness")
            +_intro("u","v","hsf","heq")+_call("hkernel_witness_witness_right","u","v")+("split","exact hsf","exact heq"),
            "G010: every positive natural has a unique actual squarefree-times-square decomposition together with a genuinely encoded complete perfect-power profile, including the uniform unit exception.",
        ),
    )


def make_perfect_power_profile_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (_power_rows(spec)+_root_rows(spec)+_prefix_gcd_rows(spec)+_support_gcd_rows(spec)
            +_table_rows(spec)+_profile_rows(spec))


__all__ = ["prime_valuations_divisible_relation","prime_exponent_prefix_gcd_relation",
           "perfect_power_root_table_relation","perfect_power_profile_code_relation",
           "perfect_power_profile_data_relation","perfect_power_profile_relation",
           "make_perfect_power_profile_candidate_theorems"]
