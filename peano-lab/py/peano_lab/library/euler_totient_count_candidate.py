"""Actual finite unit counts, independently of Euler's product formula.

The bit at index i is one exactly when Coprime(i,n). UnitCount(n,L,t)
is a witnessed beta sum of these bits on 0 <= i < L. Phi(n,t) additionally
requires n != 0 and sets L=n, preserving the blueprint's positive domain.
These are additive ordinary HA proof bodies, not admission certificates.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .finite_fold_surface import _identifier
from .finite_sum_theorems import _at, _sum_relation_terms


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return (*(f"specialize {name} ({argument})" for argument in arguments), f"apply {name}")


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _fresh(tag: str, terms: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    _identifier(tag, "unit-count definition tag")
    names = tuple(f"eut_{role}_{tag}" for role in roles)
    variables = set(re.findall(r"[A-Za-z_][A-Za-z_0-9']*", " ".join(terms)))
    if set(names) & variables:
        raise ValueError("unit-count definition binder captures an argument")
    return names


def _public(*arguments: str, tag: str) -> None:
    _identifier(tag, "unit-count definition tag")
    for argument in arguments:
        _identifier(argument, "unit-count definition argument")
        if argument.startswith(("eut_", "fs_", "ff_")):
            raise ValueError("unit-count definition binder captures an argument")


def _lt(a: str, b: str, *, tag: str) -> str:
    (gap,) = _fresh(tag, (a, b), "gap")
    return f"exists {gap}. {gap} + S ({a}) = ({b})"


def _le(a: str, b: str, *, tag: str) -> str:
    (gap,) = _fresh(tag, (a, b), "gap")
    return f"exists {gap}. {gap} + ({a}) = ({b})"


def _cop(a: str, n: str, *, tag: str) -> str:
    d, q, r = _fresh(tag, (a, n), "divisor", "left", "right")
    return f"forall {d}. (exists {q}. ({a}) = {d} * {q}) -> (exists {r}. ({n}) = {d} * {r}) -> {d} = 1"


def _sum(b: str, c: str, l: str, t: str, *, tag: str) -> str:
    return _sum_relation_terms(b, c, l, t, tag=f"eut_{tag}")


def _bits(b: str, c: str, l: str, *, tag: str) -> str:
    i, e = _fresh(tag, (b, c, l), "index", "bit")
    return f"forall {i}. ({_lt(i,l,tag=tag+'_bound')}) -> exists {e}. ({_at(b,c,i,e,tag='eut_'+tag+'_entry')}) /\\ ({e}=0 \\/ {e}=1)"


def _choice(n: str, i: str, e: str, *, tag: str) -> str:
    predicate = _cop(i, n, tag=tag+"_coprime")
    return f"((({predicate}) /\\ ({e}) = 1) \\/ (~({predicate}) /\\ ({e}) = 0))"


def _mask(n: str, b: str, c: str, l: str, *, tag: str) -> str:
    i, e = _fresh(tag, (n, b, c, l), "index", "bit")
    return (
        f"forall {i}. ({_lt(i,l,tag=tag+'_bound')}) -> exists {e}. "
        f"({_at(b,c,i,e,tag='eut_'+tag+'_entry')}) /\\ ({_choice(n,i,e,tag=tag+'_choice')})"
    )


def _count(n: str, l: str, t: str, *, tag: str) -> str:
    b, c = _fresh(tag, (n, l, t), "code", "scale")
    return f"exists {b} {c}. ({_mask(n,b,c,l,tag=tag+'_mask')}) /\\ ({_sum(b,c,l,t,tag=tag+'_sum')})"


def _phi(n: str, t: str, *, tag: str) -> str:
    return f"(~(({n})=0) /\\ ({_count(n,n,t,tag=tag+'_count')}))"


def unit_bit_prefix_relation(modulus: str, code: str, scale: str, length: str, *, tag: str) -> str:
    """Actual zero/one coprimality indicators at the indices below length."""
    _public(modulus, code, scale, length, tag=tag)
    return _mask(modulus, code, scale, length, tag=tag)


def unit_count_relation(modulus: str, length: str, count: str, *, tag: str) -> str:
    """Count units modulo modulus on 0 <= i < length; no product formula."""
    _public(modulus, length, count, tag=tag)
    return _count(modulus, length, count, tag=tag)


def totient_relation(modulus: str, count: str, *, tag: str) -> str:
    """Positive modulus and its actual count of canonical unit residues."""
    _public(modulus, count, tag=tag)
    return _phi(modulus, count, tag=tag)


def _mask_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "totient_coprime_decidable",
            f"forall a n. ({_cop('a','n',tag='dec_yes')}) \\/ ~({_cop('a','n',tag='dec_no')})",
            ("gcd_exists_relational", "eq_decidable", "is_gcd_one_to_coprime", "is_gcd_dvd_left", "is_gcd_dvd_right"),
            (*_intro("a","n"), "specialize gcd_exists_relational a", "specialize gcd_exists_relational n", "cases gcd_exists_relational",
             "have hd : x=1 \\/ ~(x=1)", *_call("eq_decidable","x","1"), "cases hd", "left",
             "rewrite hd_left at gcd_exists_relational_witness", "rewrite hd_left at gcd_exists_relational_witness", "rewrite hd_left at gcd_exists_relational_witness",
             *_call("is_gcd_one_to_coprime","a","n"), "exact gcd_exists_relational_witness",
             "right", "intro hc", "apply hd_right", "specialize hc x", "apply hc",
             *_call("is_gcd_dvd_left","x","a","n"), "exact gcd_exists_relational_witness",
             *_call("is_gcd_dvd_right","x","a","n"), "exact gcd_exists_relational_witness"),
            "Decide common-divisor coprimality from the actual canonical gcd; includes both zero coordinates.",
        ),
        spec(
            "totient_unit_bit_choice_exists",
            f"forall n i. exists e. {_choice('n','i','e',tag='choice_exists')}",
            ("totient_coprime_decidable",),
            (*_intro("n","i"), f"have hc : ({_cop('i','n',tag='choice_dec_yes')}) \\/ ~({_cop('i','n',tag='choice_dec_no')})",
             *_call("totient_coprime_decidable","i","n"), "cases hc", "exists 1", "left", "split", "exact hc_left", "refl",
             "exists 0", "right", "split", "exact hc_right", "refl"),
            "Construct the bit from the actual decidable unit predicate, not from a proposed totient value.",
        ),
        spec(
            "totient_unit_bit_choice_functional",
            f"forall n i e f. ({_choice('n','i','e',tag='choice_left')}) -> ({_choice('n','i','f',tag='choice_right')}) -> e=f",
            (),
            (*_intro("n","i","e","f","he","hf"), "cases he", "cases he_left", "cases hf", "cases hf_left",
             "trans 1", "exact he_left_right", "symm", "exact hf_left_right", "cases hf_right", "exfalso", "apply hf_right_left", "exact he_left_left",
             "cases he_right", "cases hf", "cases hf_left", "exfalso", "apply he_right_left", "exact hf_left_left", "cases hf_right",
             "trans 0", "exact he_right_right", "symm", "exact hf_right_right"),
            "The independently decided unit indicator is literally unique.",
        ),
        spec(
            "totient_unit_prefix_empty",
            f"forall n b c. {_mask('n','b','c','0',tag='mask_empty')}",
            ("lt_not_le", "zero_le"),
            (*_intro("n","b","c","i","hi"), "exfalso", *_call("lt_not_le","i","0"), "exact hi", *_call("zero_le","i")),
            "The empty unit prefix has no undecided entries.",
        ),
        spec(
            "totient_unit_prefix_drop_last",
            f"forall n b c l. ({_mask('n','b','c','S l',tag='drop_source')}) -> ({_mask('n','b','c','l',tag='drop_target')})",
            ("le_succ",),
            (*_intro("n","b","c","l","h","i","hi"), "specialize h i", "apply h", *_call("le_succ","S i","l"), "exact hi"),
            "Restrict a complete prefix of unit bits to its predecessor.",
        ),
        spec(
            "totient_unit_prefix_entry",
            f"forall n b c l i e. ({_mask('n','b','c','l',tag='entry_mask')}) -> ({_lt('i','l',tag='entry_bound')}) -> "
            f"({_at('b','c','i','e',tag='eut_entry')}) -> ({_choice('n','i','e',tag='entry_choice')})",
            ("beta_at_unique",),
            (*_intro("n","b","c","l","i","e","h","hi","he"),
             f"have hp : exists a. ({_at('b','c','i','a',tag='eut_entry_actual')}) /\\ ({_choice('n','i','a',tag='entry_actual_choice')})",
             "specialize h i", "apply h", "exact hi", "cases hp", "cases hp_witness",
             "have heq : x=e", *_call("beta_at_unique","b","c","i","x","e"), "exact hp_witness_left", "exact he",
             "rewrite heq at hp_witness_right", "rewrite heq at hp_witness_right", "exact hp_witness_right"),
            "Every decoded bit has the actual common-divisor meaning, regardless of the chosen beta encoding.",
        ),
        spec(
            "totient_unit_prefix_extend",
            f"forall n b c l e. ({_mask('n','b','c','l',tag='extend_source')}) -> ({_choice('n','l','e',tag='extend_last')}) -> "
            f"exists d f. {_mask('n','d','f','S l',tag='extend_target')}",
            ("beta_prefix_extend", "le_eq_or_lt", "le_of_succ_le_succ"),
            (*_intro("n","b","c","l","e","h","he"),
             f"have hext : exists d f. ({_at('d','f','l','e',tag='eut_extend_last')}) /\\ forall i a. "
             f"({_lt('i','l',tag='extend_bound')}) -> ({_at('b','c','i','a',tag='eut_extend_old')}) -> ({_at('d','f','i','a',tag='eut_extend_new')})",
             *_call("beta_prefix_extend","l","b","c","e"), "cases hext", "cases hext_witness", "cases hext_witness_witness",
             "exists x", "exists x1", "intro i", "intro hi", "have hcases : i=l \\/ exists g. g+S i=l",
             *_call("le_eq_or_lt","i","l"), *_call("le_of_succ_le_succ","i","l"), "exact hi", "cases hcases",
             "exists e", "split", "rewrite hcases_left", "rewrite hcases_left", "exact hext_witness_witness_left",
             "rewrite hcases_left", "rewrite hcases_left", "exact he",
             f"have hp : exists a. ({_at('b','c','i','a',tag='eut_extend_point')}) /\\ ({_choice('n','i','a',tag='extend_point_choice')})",
             "specialize h i", "apply h", "exact hcases_right", "cases hp", "cases hp_witness", "exists x2", "split",
             "specialize hext_witness_witness_right i", "specialize hext_witness_witness_right x2", "apply hext_witness_witness_right",
             "exact hcases_right", "exact hp_witness_left", "exact hp_witness_right"),
            "Actually append the decided unit bit using beta-prefix extension.",
        ),
        spec(
            "totient_unit_prefix_exists",
            f"forall n l. exists b c. {_mask('n','b','c','l',tag='mask_exists')}",
            ("totient_unit_prefix_empty", "totient_unit_bit_choice_exists", "totient_unit_prefix_extend"),
            ("intro n", "induction l", "exists 0", "exists 0", *_call("totient_unit_prefix_empty","n","0","0"),
             f"have hpre : exists b c. {_mask('n','b','c','l',tag='mask_pre')}", "apply IH", "cases hpre", "cases hpre_witness",
             f"have he : exists e. {_choice('n','l','e',tag='mask_last')}", *_call("totient_unit_bit_choice_exists","n","l"), "cases he",
             *_call("totient_unit_prefix_extend","n","x","x1","l","x2"), "exact hpre_witness_witness", "exact he_witness"),
            "HA induction constructs the complete mask for every modulus and every finite interval.",
        ),
        spec(
            "totient_unit_prefix_all_bits",
            f"forall n b c l. ({_mask('n','b','c','l',tag='bits_mask')}) -> ({_bits('b','c','l',tag='bits_result')})",
            (),
            (*_intro("n","b","c","l","h","i","hi"),
             f"have hp : exists e. ({_at('b','c','i','e',tag='eut_bits_entry')}) /\\ ({_choice('n','i','e',tag='bits_choice')})",
             "specialize h i", "apply h", "exact hi", "cases hp", "cases hp_witness", "exists x", "split", "exact hp_witness_left",
             "cases hp_witness_right", "cases hp_witness_right_left", "right", "exact hp_witness_right_left_right",
             "cases hp_witness_right_right", "left", "exact hp_witness_right_right_right"),
            "Unit masks consist of genuine zero/one entries.",
        ),
        spec(
            "totient_unit_prefix_equal_entry",
            f"forall n b c d f l i e a. ({_mask('n','b','c','l',tag='equal_left')}) -> ({_mask('n','d','f','l',tag='equal_right')}) -> "
            f"({_lt('i','l',tag='equal_bound')}) -> ({_at('b','c','i','e',tag='eut_equal_e')}) -> ({_at('d','f','i','a',tag='eut_equal_a')}) -> e=a",
            ("totient_unit_bit_choice_functional", "totient_unit_prefix_entry"),
            (*_intro("n","b","c","d","f","l","i","e","a","hb","hd","hi","he","ha"),
             *_call("totient_unit_bit_choice_functional","n","i","e","a"),
             *_call("totient_unit_prefix_entry","n","b","c","l","i","e"), "exact hb", "exact hi", "exact he",
             *_call("totient_unit_prefix_entry","n","d","f","l","i","a"), "exact hd", "exact hi", "exact ha"),
            "All unit masks encode the same bits on their common interval.",
        ),
    )


def _count_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "totient_unit_count_exists",
            f"forall n l. exists t. {_count('n','l','t',tag='count_exists')}",
            ("totient_unit_prefix_exists", "beta_sum_exists"),
            (*_intro("n","l"), f"have hm : exists b c. {_mask('n','b','c','l',tag='count_mask')}", *_call("totient_unit_prefix_exists","n","l"),
             "cases hm", "cases hm_witness", f"have hs : exists t. {_sum('x','x1','l','t',tag='count_sum')}", *_call("beta_sum_exists","x","x1","l"),
             "cases hs", "exists x2", "exists x", "exists x1", "split", "exact hm_witness_witness", "exact hs_witness"),
            "Construct an actual finite unit count, with both characteristic and sum traces witnessed.",
        ),
        spec(
            "totient_unit_count_functional",
            f"forall n l t T. ({_count('n','l','t',tag='count_left')}) -> ({_count('n','l','T',tag='count_right')}) -> t=T",
            ("le_antisymm", "beta_sum_pointwise_le", "totient_unit_prefix_equal_entry", "le_refl"),
            (*_intro("n","l","t","T","ht","hT"), "cases ht", "cases ht_witness", "cases ht_witness_witness", "cases hT", "cases hT_witness", "cases hT_witness_witness",
             *_call("le_antisymm","t","T"), *_call("beta_sum_pointwise_le","x","x1","x2","x3","l","t","T"),
             *_intro("i","a","z","hi","ha","hz"), "have heq : a=z", *_call("totient_unit_prefix_equal_entry","n","x","x1","x2","x3","l","i","a","z"),
             "exact ht_witness_witness_left", "exact hT_witness_witness_left", "exact hi", "exact ha", "exact hz", "rewrite heq", *_call("le_refl","z"),
             "exact ht_witness_witness_right", "exact hT_witness_witness_right",
             *_call("beta_sum_pointwise_le","x2","x3","x","x1","l","T","t"), *_intro("i","a","z","hi","ha","hz"), "have heq : a=z",
             *_call("totient_unit_prefix_equal_entry","n","x2","x3","x","x1","l","i","a","z"),
             "exact hT_witness_witness_left", "exact ht_witness_witness_left", "exact hi", "exact ha", "exact hz", "rewrite heq", *_call("le_refl","z"),
             "exact hT_witness_witness_right", "exact ht_witness_witness_right"),
            "The count is independent of all beta-mask and sum-trace choices.",
        ),
        spec(
            "totient_unit_count_bounded",
            f"forall n l t. ({_count('n','l','t',tag='count_bounded')}) -> ({_le('t','l',tag='count_bound')})",
            ("bit_count_bounded", "totient_unit_prefix_all_bits"),
            (*_intro("n","l","t","h"), "cases h", "cases h_witness", "cases h_witness_witness", *_call("bit_count_bounded","x","x1","l","t"),
             "split", "exact h_witness_witness_right", *_call("totient_unit_prefix_all_bits","n","x","x1","l"), "exact h_witness_witness_left"),
            "The unit count never exceeds the actual interval length.",
        ),
        spec(
            "totient_unit_count_zero_length",
            f"forall n t. ({_count('n','0','t',tag='empty_count')}) -> t=0",
            ("beta_sum_zero",),
            (*_intro("n","t","h"), "cases h", "cases h_witness", "cases h_witness_witness", *_call("beta_sum_zero","x","x1","t"), "exact h_witness_witness_right"),
            "The auxiliary empty interval count is zero even at modulus zero; this does not assert Phi(0,0).",
        ),
        spec(
            "totient_unit_count_succ_decompose",
            f"forall n l t. ({_count('n','S l','t',tag='succ_count')}) -> exists r e. "
            f"({_count('n','l','r',tag='succ_previous')}) /\\ (({_choice('n','l','e',tag='succ_choice')}) /\\ t=r+e)",
            ("beta_sum_succ_decompose", "totient_unit_prefix_drop_last", "totient_unit_prefix_entry", "le_refl"),
            (*_intro("n","l","t","h"), "cases h", "cases h_witness", "cases h_witness_witness",
             f"have hd : exists a r. ({_at('x','x1','l','a',tag='eut_succ_entry')}) /\\ (({_sum('x','x1','l','r',tag='succ_prefix_sum')}) /\\ t=r+a)",
             *_call("beta_sum_succ_decompose","x","x1","l","t"), "exact h_witness_witness_right",
             "cases hd", "cases hd_witness", "cases hd_witness_witness", "cases hd_witness_witness_right", "exists x3", "exists x2", "split",
             "exists x", "exists x1", "split", *_call("totient_unit_prefix_drop_last","n","x","x1","l"), "exact h_witness_witness_left", "exact hd_witness_witness_right_left",
             "split", *_call("totient_unit_prefix_entry","n","x","x1","S l","l","x2"), "exact h_witness_witness_left", *_call("le_refl","S l"),
             "exact hd_witness_witness_left", "exact hd_witness_witness_right_right"),
            "A successor interval decomposes into its real previous count and the independently decided last unit bit.",
        ),
        spec(
            "totient_unit_count_succ_intro",
            f"forall n l r e. ({_count('n','l','r',tag='intro_previous')}) -> ({_choice('n','l','e',tag='intro_choice')}) -> ({_count('n','S l','r+e',tag='intro_result')})",
            ("totient_unit_count_exists", "totient_unit_count_succ_decompose", "totient_unit_count_functional", "totient_unit_bit_choice_functional"),
            (*_intro("n","l","r","e","hr","he"), f"have hc : exists t. {_count('n','S l','t',tag='intro_actual')}", *_call("totient_unit_count_exists","n","S l"), "cases hc",
             f"have hd : exists u v. ({_count('n','l','u',tag='intro_actual_pre')}) /\\ (({_choice('n','l','v',tag='intro_actual_bit')}) /\\ x=u+v)",
             *_call("totient_unit_count_succ_decompose","n","l","x"), "exact hc_witness", "cases hd", "cases hd_witness", "cases hd_witness_witness", "cases hd_witness_witness_right",
             "have hu : x1=r", *_call("totient_unit_count_functional","n","l","x1","r"), "exact hd_witness_witness_left", "exact hr",
             "have hv : x2=e", *_call("totient_unit_bit_choice_functional","n","l","x2","e"), "exact hd_witness_witness_right_left", "exact he",
             "have ht : x=r+e", "rewrite hd_witness_witness_right_right", "rewrite hu", "rewrite hv", "refl",
             "rewrite ht at hc_witness", "rewrite ht at hc_witness", "exact hc_witness"),
            "The computed predecessor count and next bit construct the real successor count, not a supplied cardinality oracle.",
        ),
        spec(
            "totient_unit_choice_mod_one",
            f"forall i e. ({_choice('1','i','e',tag='mod_one_bit')}) -> e=1",
            ("coprime_one_right",),
            (*_intro("i","e","h"), "cases h", "cases h_left", "exact h_left_right", "cases h_right", "exfalso", "apply h_right_left", *_call("coprime_one_right","i")),
            "Every integer, including zero, is a unit modulo one in the common-divisor sense.",
        ),
        spec(
            "totient_unit_count_mod_one",
            f"forall l t. ({_count('1','l','t',tag='mod_one_count')}) -> t=l",
            ("totient_unit_count_zero_length", "totient_unit_count_succ_decompose", "totient_unit_choice_mod_one"),
            ("induction l", *_intro("t","h"), *_call("totient_unit_count_zero_length","1","t"), "exact h",
             *_intro("t","h"), f"have hd : exists r e. ({_count('1','l','r',tag='mod_one_pre')}) /\\ (({_choice('1','l','e',tag='mod_one_last')}) /\\ t=r+e)",
             *_call("totient_unit_count_succ_decompose","1","l","t"), "exact h", "cases hd", "cases hd_witness", "cases hd_witness_witness", "cases hd_witness_witness_right",
             "have hr : x=l", "specialize IH x", "apply IH", "exact hd_witness_witness_left",
             "have he : x1=1", *_call("totient_unit_choice_mod_one","l","x1"), "exact hd_witness_witness_right_left",
             "rewrite hd_witness_witness_right_right", "rewrite hr", "rewrite he", "simp"),
            "The independently constructed unit count modulo one equals the actual interval length.",
        ),
    )


def _phi_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "totient_exists",
            f"forall n. ~(n=0) -> exists t. {_phi('n','t',tag='phi_exists')}",
            ("totient_unit_count_exists",),
            (*_intro("n","hn"), f"have hc : exists t. {_count('n','n','t',tag='phi_exists_count')}", *_call("totient_unit_count_exists","n","n"),
             "cases hc", "exists x", "split", "exact hn", "exact hc_witness"),
            "Every positive modulus has a genuinely constructed totient on its canonical residue interval.",
        ),
        spec(
            "totient_functional",
            f"forall n t u. ({_phi('n','t',tag='phi_left')}) -> ({_phi('n','u',tag='phi_right')}) -> t=u",
            ("totient_unit_count_functional",),
            (*_intro("n","t","u","ht","hu"), "cases ht", "cases hu", *_call("totient_unit_count_functional","n","n","t","u"), "exact ht_right", "exact hu_right"),
            "The totient value is unique independently of all finite encoding choices.",
        ),
        spec(
            "totient_bounded",
            f"forall n t. ({_phi('n','t',tag='phi_bounded')}) -> ({_le('t','n',tag='phi_bound')})",
            ("totient_unit_count_bounded",),
            (*_intro("n","t","h"), "cases h", *_call("totient_unit_count_bounded","n","n","t"), "exact h_right"),
            "The totient does not exceed its positive modulus.",
        ),
        spec(
            "totient_zero_excluded",
            f"forall t. ~({_phi('0','t',tag='phi_zero')})",
            (),
            (*_intro("t","h"), "cases h", "apply h_left", "refl"),
            "Phi keeps the blueprint's positive-domain boundary; auxiliary empty counting does not manufacture Phi(0,0).",
        ),
        spec(
            "totient_one",
            f"forall t. ({_phi('1','t',tag='phi_one')}) -> t=1",
            ("totient_unit_count_mod_one",),
            (*_intro("t","h"), "cases h", *_call("totient_unit_count_mod_one","1","t"), "exact h_right"),
            "Phi(1)=1 because the sole canonical residue zero is coprime to one.",
        ),
        spec(
            "totient_one_value",
            _phi('1','1',tag='phi_one_value'),
            ("totient_unit_count_exists", "totient_unit_count_mod_one", "succ_ne_zero"),
            (f"have hc : exists t. {_count('1','1','t',tag='one_actual_count')}", *_call("totient_unit_count_exists","1","1"), "cases hc",
             "have ht : x=1", *_call("totient_unit_count_mod_one","1","x"), "exact hc_witness",
             "split", *_call("succ_ne_zero","0"), "rewrite ht at hc_witness", "rewrite ht at hc_witness", "exact hc_witness"),
            "Construct the actual Phi(1,1) count witnesses, including the zero residue.",
        ),
        spec(
            "totient_exists_unique",
            f"forall n. ~(n=0) -> exists t. ({_phi('n','t',tag='phi_chosen')}) /\\ forall u. ({_phi('n','u',tag='phi_other')}) -> t=u",
            ("totient_exists", "totient_functional"),
            (*_intro("n","hn"), f"have ht : exists t. {_phi('n','t',tag='phi_chosen_actual')}", *_call("totient_exists","n"), "exact hn", "cases ht",
             "exists x", "split", "exact ht_witness", *_intro("u","hu"), *_call("totient_functional","n","x","u"), "exact ht_witness", "exact hu"),
            "Total uniquely determined totient on all positive naturals, independently of the still separate Euler product theorem.",
        ),
    )


def make_euler_totient_count_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_mask_rows(spec), *_count_rows(spec), *_phi_rows(spec))


__all__ = ["unit_bit_prefix_relation", "unit_count_relation", "totient_relation", "make_euler_totient_count_candidate_theorems"]
