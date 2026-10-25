"""Constructive finite sets as actual beta-coded characteristic prefixes.

This additive authoring module introduces no set or cardinality primitives.
Every relation is an ordinary first-order HA formula; each tactic body must
pass the independent original kernel, and dependency closure remains a
separate release gate.  Set cardinality is the existing witnessed BitCount.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_division_prefix_candidate import division_prefix
from .finite_fold_surface import all_bits, range_relation, sum_relation
from .finite_permutation_theorems import bounded_prefix, injective_prefix
from .finite_sum_theorems import _at


_AND = "/\\"
_OR = "\\/"

class FiniteModularSetError(ValueError):
    """A finite-set surface argument is invalid or captures a bound name."""


def _safe(value: str) -> str:
    if (
        not isinstance(value, str) or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
        or value in {"S", "bot", "exists", "false", "forall"}
    ):
        raise FiniteModularSetError("expected a non-reserved Peano identifier")
    return value


def _arguments(*values: str) -> tuple[str, ...]:
    result = tuple(_safe(value) for value in values)
    if len(set(result)) != len(result):
        raise FiniteModularSetError("formal arguments must be distinct")
    if any(value.startswith(("fms_", "ff_", "fs_", "fp_", "fpr_", "fpmp_", "gspf_")) for value in result):
        raise FiniteModularSetError("generated finite-set binder captures an argument")
    return result


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return tuple(f"specialize {name} {argument}" for argument in arguments) + (f"apply {name}",)


def _lt(a: str, b: str, *, tag: str = "lt") -> str:
    return f"exists fms_gap_{_safe(tag)}. fms_gap_{tag} + S ({a}) = ({b})"


def _le(a: str, b: str, *, tag: str = "le") -> str:
    return f"exists fms_gap_{_safe(tag)}. fms_gap_{tag} + ({a}) = ({b})"


def _mod(p: str, a: str, b: str, *, tag: str = "mod") -> str:
    u, v = f"fms_u_{_safe(tag)}", f"fms_v_{tag}"
    return f"exists {u} {v}. ({a}) + ({p}) * {u} = ({b}) + ({p}) * {v}"


def _iff(left: str, right: str) -> str:
    return f"((({left}) -> ({right})) /\\ (({right}) -> ({left})))"


def _not(formula: str) -> str:
    return f"~({formula})"


def _sum(b: str, c: str, l: str, n: str, *, tag: str = "sum") -> str:
    # Substitutions occupy only audited internal term positions.  Public
    # surfaces validate distinct identifiers before reaching this helper.
    result = sum_relation("fms_code_arg", "fms_scale_arg", "fms_length_arg", "fms_count_arg", tag=f"fms_{_safe(tag)}")
    return (result.replace("fms_code_arg", f"({b})").replace("fms_scale_arg", f"({c})")
            .replace("fms_length_arg", f"({l})").replace("fms_count_arg", f"({n})"))


def _bits(b: str, c: str, l: str, *, tag: str = "bits") -> str:
    result = all_bits("fms_code_arg", "fms_scale_arg", "fms_length_arg", tag=f"fms_{_safe(tag)}")
    return result.replace("fms_code_arg", f"({b})").replace("fms_scale_arg", f"({c})").replace("fms_length_arg", f"({l})")


def _count(b: str, c: str, l: str, n: str, *, tag: str = "count") -> str:
    return f"(({_sum(b, c, l, n, tag=tag)}) /\\ ({_bits(b, c, l, tag=tag)}))"


def _member(b: str, c: str, p: str, i: str, *, tag: str = "member") -> str:
    return f"(({_lt(i, p, tag=tag)}) /\\ ({_at(b, c, i, '1', tag=f'fms_{tag}')}))"


def _subset(b: str, c: str, d: str, e: str, p: str, *, tag: str = "subset") -> str:
    i = f"fms_i_{_safe(tag)}"
    return (
        f"forall {i}. ({_lt(i, p, tag=tag)}) -> "
        f"({_at(b, c, i, '1', tag=f'fms_{tag}_left')}) -> "
        f"({_at(d, e, i, '1', tag=f'fms_{tag}_right')})"
    )


def _binary(b: str, c: str, d: str, e: str, u: str, v: str, p: str, op: str, *, tag: str = "binary") -> str:
    i = f"fms_i_{_safe(tag)}"
    member = _at(u, v, i, '1', tag=f'fms_{tag}_result')
    operand = f"(({_at(b, c, i, '1', tag=f'fms_{tag}_left')}) {op} ({_at(d, e, i, '1', tag=f'fms_{tag}_right')}))"
    return f"forall {i}. ({_lt(i, p, tag=tag)}) -> ({_iff(member,operand)})"


def _pullback(b: str, c: str, d: str, e: str, p: str, t: str, *, tag: str = "pullback") -> str:
    i, j = f"fms_i_{_safe(tag)}", f"fms_j_{tag}"
    return (
        f"forall {i} {j}. ({_lt(i, p, tag=f'{tag}_i')}) -> "
        f"({_lt(j, p, tag=f'{tag}_j')}) -> ({_mod(p, f'{i} + {t}', j, tag=tag)}) -> "
        f"({_iff(_at(d,e,i,'1',tag=f'fms_{tag}_target'),_at(b,c,j,'1',tag=f'fms_{tag}_source'))})"
    )


def _cover(b: str, c: str, d: str, e: str, u: str, v: str, p: str, *, tag: str = "cover") -> str:
    i, j, s = (f"fms_{stem}_{_safe(tag)}" for stem in ("i", "j", "s"))
    return (
        f"forall {i} {j} {s}. ({_lt(i, p, tag=f'{tag}_i')}) -> "
        f"({_lt(j, p, tag=f'{tag}_j')}) -> ({_lt(s, p, tag=f'{tag}_s')}) -> "
        f"({_at(b, c, i, '1', tag=f'fms_{tag}_left')}) -> "
        f"({_at(d, e, j, '1', tag=f'fms_{tag}_right')}) -> "
        f"({_mod(p, f'{i} + {j}', s, tag=tag)}) -> "
        f"({_at(u, v, s, '1', tag=f'fms_{tag}_result')})"
    )


def _sumset(b: str, c: str, d: str, e: str, u: str, v: str, p: str, *, tag: str = "sumset") -> str:
    i, j, s = (f"fms_{stem}_{_safe(tag)}" for stem in ("i", "j", "s"))
    witnesses = (
        f"exists {i} {j}. (({_member(b, c, p, i, tag=f'{tag}_left')}) /\\ "
        f"(({_member(d, e, p, j, tag=f'{tag}_right')}) /\\ "
        f"({_mod(p, f'{i} + {j}', s, tag=tag)})))"
    )
    return f"forall {s}. ({_lt(s,p,tag=f'{tag}_s')}) -> ({_iff(_at(u,v,s,'1',tag=f'fms_{tag}_result'),witnesses)})"


def _partial_sums(b: str, c: str, d: str, e: str, p: str, l: str, z: str, *, tag: str = "partial") -> str:
    a,v = f"fms_first_{_safe(tag)}", f"fms_second_{tag}"
    return (
        f"exists {a} {v}. ({_member(b,c,p,a,tag=f'{tag}_left')}) /\\ "
        f"(({_member(d,e,p,v,tag=f'{tag}_right')}) /\\ "
        f"(({_lt(v,l,tag=f'{tag}_cutoff')}) /\\ ({_mod(p,f'{a}+{v}',z,tag=f'{tag}_congruence')})))"
    )


def _partial_sumset(b: str, c: str, d: str, e: str, u: str, v: str, p: str, l: str, *, tag: str = "partial") -> str:
    z = f"fms_z_{_safe(tag)}"
    return f"forall {z}. ({_lt(z,p,tag=f'{tag}_bound')}) -> ({_iff(_at(u,v,z,'1',tag=f'fms_{tag}_result'),_partial_sums(b,c,d,e,p,l,z,tag=tag))})"


def finite_modular_set_relation(code: str, scale: str, modulus: str, cardinality: str, *, tag: str) -> str:
    """A genuine beta characteristic prefix with its exact witnessed count."""
    return _count(*_arguments(code, scale, modulus, cardinality), tag=_safe(tag))


def modular_set_member_relation(code: str, scale: str, modulus: str, element: str, *, tag: str) -> str:
    """The canonical element is below the modulus and its actual bit is one."""
    return _member(*_arguments(code, scale, modulus, element), tag=_safe(tag))


def modular_set_subset_relation(left_code: str, left_scale: str, right_code: str, right_scale: str, modulus: str, *, tag: str) -> str:
    return _subset(*_arguments(left_code, left_scale, right_code, right_scale, modulus), tag=_safe(tag))


def modular_set_union_relation(left_code: str, left_scale: str, right_code: str, right_scale: str, result_code: str, result_scale: str, modulus: str, *, tag: str) -> str:
    return _binary(*_arguments(left_code, left_scale, right_code, right_scale, result_code, result_scale, modulus), "\\/", tag=_safe(tag))


def modular_set_intersection_relation(left_code: str, left_scale: str, right_code: str, right_scale: str, result_code: str, result_scale: str, modulus: str, *, tag: str) -> str:
    return _binary(*_arguments(left_code, left_scale, right_code, right_scale, result_code, result_scale, modulus), "/\\", tag=_safe(tag))


def modular_set_pullback_relation(source_code: str, source_scale: str, target_code: str, target_scale: str, modulus: str, shift: str, *, tag: str) -> str:
    """The target is exactly source minus shift in the canonical residue interval."""
    return _pullback(*_arguments(source_code, source_scale, target_code, target_scale, modulus, shift), tag=_safe(tag))


def modular_set_sum_cover_relation(left_code: str, left_scale: str, right_code: str, right_scale: str, result_code: str, result_scale: str, modulus: str, *, tag: str) -> str:
    return _cover(*_arguments(left_code, left_scale, right_code, right_scale, result_code, result_scale, modulus), tag=_safe(tag))


def modular_set_sum_relation(left_code: str, left_scale: str, right_code: str, right_scale: str, result_code: str, result_scale: str, modulus: str, *, tag: str) -> str:
    """The target contains all and only canonical sums of actual input members."""
    return _sumset(*_arguments(left_code, left_scale, right_code, right_scale, result_code, result_scale, modulus), tag=_safe(tag))


def _pointwise_le(b: str, c: str, d: str, e: str, l: str, *, tag: str = "le") -> str:
    i, a, v = (f"fms_{stem}_{_safe(tag)}" for stem in ("i", "a", "v"))
    return (
        f"forall {i} {a} {v}. ({_lt(i, l, tag=tag)}) -> "
        f"({_at(b, c, i, a, tag=f'fms_{tag}_left')}) -> "
        f"({_at(d, e, i, v, tag=f'fms_{tag}_right')}) -> ({_le(a, v, tag=tag)})"
    )


def _product(b: str, c: str, d: str, e: str, u: str, v: str, l: str, *, tag: str = "product") -> str:
    i, a, z, w = (f"fms_{stem}_{_safe(tag)}" for stem in ("i", "a", "z", "w"))
    return (
        f"forall {i} {a} {z} {w}. ({_lt(i,l,tag=tag)}) -> "
        f"({_at(b,c,i,a,tag=f'fms_{tag}_a')}) -> ({_at(d,e,i,z,tag=f'fms_{tag}_b')}) -> "
        f"({_at(u,v,i,w,tag=f'fms_{tag}_w')}) -> {w}={a}*{z}"
    )


def _complement(b: str, c: str, d: str, e: str, l: str, *, tag: str = "complement") -> str:
    i, a, v = (f"fms_{stem}_{_safe(tag)}" for stem in ("i", "a", "v"))
    return (
        f"forall {i} {a} {v}. ({_lt(i,l,tag=tag)}) -> "
        f"({_at(b,c,i,a,tag=f'fms_{tag}_a')}) -> ({_at(d,e,i,v,tag=f'fms_{tag}_b')}) -> "
        f"(({a}=0 /\\ {v}=1) \\/ ({a}=1 /\\ {v}=0))"
    )


def _sign_complement(b: str, c: str, d: str, e: str, l: str, *, tag: str = "sign") -> str:
    i, a = f"fms_i_{_safe(tag)}", f"fms_a_{tag}"
    return (
        f"forall {i} {a}. ({_lt(i,l,tag=tag)}) -> ({_at(b,c,i,a,tag=f'fms_{tag}_a')}) -> "
        f"(({a}=0 /\\ ({_at(d,e,i,'1',tag=f'fms_{tag}_one')})) \\/ "
        f"({a}=1 /\\ ({_at(d,e,i,'0',tag=f'fms_{tag}_zero')})))"
    )


def _sum_balance(b: str, c: str, d: str, e: str, f: str, g: str, h: str, t: str, l: str, *, tag: str = "balance") -> str:
    i, a, v, w, z = (f"fms_{stem}_{_safe(tag)}" for stem in ("i", "a", "v", "w", "z"))
    return (
        f"forall {i} {a} {v} {w} {z}. ({_lt(i,l,tag=tag)}) -> "
        f"({_at(b,c,i,a,tag=f'fms_{tag}_a')}) -> ({_at(d,e,i,v,tag=f'fms_{tag}_b')}) -> "
        f"({_at(f,g,i,w,tag=f'fms_{tag}_c')}) -> ({_at(h,t,i,z,tag=f'fms_{tag}_d')}) -> {a}+{v}={w}+{z}"
    )


def _compose(r: str, s: str, b: str, c: str, z: str, d: str, l: str, *, tag: str = "compose") -> str:
    i,j,v = (f"fms_{stem}_{_safe(tag)}" for stem in ("i","j","v"))
    return (
        f"forall {i} {j} {v}. ({_lt(i,l,tag=tag)}) -> ({_at(r,s,i,j,tag=f'fms_{tag}_index')}) -> "
        f"({_at(b,c,j,v,tag=f'fms_{tag}_source')}) -> ({_at(z,d,i,v,tag=f'fms_{tag}_target')})"
    )


def _translation_indices(p: str, t: str, r: str, s: str, l: str, *, tag: str = "indices") -> str:
    i,j = f"fms_i_{_safe(tag)}", f"fms_j_{tag}"
    return (
        f"forall {i}. ({_lt(i,l,tag=tag)}) -> exists {j}. ({_at(r,s,i,j,tag=f'fms_{tag}_entry')}) /\\ "
        f"(({_lt(j,p,tag=f'{tag}_bound')}) /\\ ({_mod(p,f'{i}+{t}',j,tag=tag)}))"
    )


def make_finite_modular_set_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Build actual characteristic-set, counting, and modular transport proofs."""
    return (
        _make_counting_theorems(spec) + _make_strict_counting_theorems(spec)
        + _make_boolean_theorems(spec) + _make_union_theorems(spec)
        + _make_union_count_theorems(spec) + _make_translation_theorems(spec)
        + _make_modular_set_transport_theorems(spec) + _make_sumset_prefix_theorems(spec)
        + _make_sumset_existence_theorems(spec)
    )


def _sum_decompose(b: str, c: str, l: str, n: str, hypothesis: str, label: str) -> tuple[str, ...]:
    a, r = f"fms_term_{label}", f"fms_sum_{label}"
    return (
        f"have {label} : exists {a} {r}. ({_at(b,c,l,a,tag=f'fms_{label}')}) /\\ (({_sum(b,c,l,r,tag=label)}) /\\ {n}={r}+{a})",
        *_call("beta_sum_succ_decompose", b, c, l, n), f"exact {hypothesis}",
        f"cases {label}", f"cases {label}_witness", f"cases {label}_witness_witness", f"cases {label}_witness_witness_right",
    )


def _make_counting_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    rows = [
        spec(
            "finite_bit_entry_cases",
            f"forall b c l i a. ({_bits('b','c','l')}) -> ({_lt('i','l')}) -> "
            f"({_at('b','c','i','a',tag='fms_entry')}) -> a=0 \\/ a=1",
            ("beta_at_unique",),
            ("intro b", "intro c", "intro l", "intro i", "intro a", "intro hbits", "intro hi", "intro ha",
             f"have hbit : exists v. ({_at('b','c','i','v',tag='fms_chosen')}) /\\ (v=0 \\/ v=1)",
             *_call("hbits", "i"), "exact hi", "cases hbit", "cases hbit_witness",
             "have heq : a=x", *_call("beta_at_unique","b","c","i","a","x"),
             "exact ha", "exact hbit_witness_left", "rewrite heq", "rewrite heq", "exact hbit_witness_right"),
            "Every explicitly decoded entry of a genuine bit prefix is zero or one.",
        ),
        spec(
            "finite_bit_membership_decidable",
            f"forall b c l i. ({_bits('b','c','l')}) -> ({_lt('i','l')}) -> "
            f"({_at('b','c','i','1',tag='fms_member_yes')}) \\/ ~({_at('b','c','i','1',tag='fms_member_no')})",
            ("beta_at_exists", "finite_bit_entry_cases", "beta_at_unique", "succ_ne_zero"),
            ("intro b", "intro c", "intro l", "intro i", "intro hbits", "intro hi",
             "specialize beta_at_exists b", "specialize beta_at_exists c", "specialize beta_at_exists i", "cases beta_at_exists",
             "have hcase : x=0 \\/ x=1", *_call("finite_bit_entry_cases","b","c","l","i","x"),
             "exact hbits", "exact hi", "exact beta_at_exists_witness", "cases hcase",
             "right", "intro hone", "have heq : 1=x", *_call("beta_at_unique","b","c","i","1","x"),
             "exact hone", "exact beta_at_exists_witness", "rewrite hcase_left at heq", *_call("succ_ne_zero","0"), "exact heq",
             "left", "rewrite hcase_right at beta_at_exists_witness", "rewrite hcase_right at beta_at_exists_witness", "exact beta_at_exists_witness"),
            "Membership in a genuine finite characteristic set is constructively decidable.",
        ),
        spec(
            "finite_bit_count_positive_member",
            f"forall b c l n. ({_count('b','c','l','n')}) -> ~(n=0) -> exists i. ({_member('b','c','l','i')})",
            ("zero_or_succ", "bit_count_positive_last_one"),
            ("intro b", "intro c", "intro l", "intro n", "intro hcount", "intro hn",
             "specialize zero_or_succ n", "cases zero_or_succ", "exfalso", "apply hn", "exact zero_or_succ_left",
             "cases zero_or_succ_right", "rewrite zero_or_succ_right_witness at hcount", "rewrite zero_or_succ_right_witness at hcount",
             f"have hw : exists i. ({_lt('i','l')}) /\\ (({_at('b','c','i','1',tag='fms_last')}) /\\ ({_le('S x','S i')}))",
             *_call("bit_count_positive_last_one","b","c","l","x"), "exact hcount", "cases hw", "cases hw_witness", "cases hw_witness_right",
             "exists x1", "split", "exact hw_witness_left", "exact hw_witness_right_left"),
            "Every positive witnessed bit count supplies an actual bounded member.",
        ),
        spec(
            "finite_bit_subset_pointwise_le",
            f"forall b c d e l. ({_bits('b','c','l')}) -> ({_subset('b','c','d','e','l')}) -> ({_pointwise_le('b','c','d','e','l')})",
            ("finite_bit_entry_cases", "beta_at_unique", "le_refl"),
            ("intro b", "intro c", "intro d", "intro e", "intro l", "intro hbits", "intro hsub",
             "intro i", "intro a", "intro v", "intro hi", "intro ha", "intro hv",
             "have hcase : a=0 \\/ a=1", *_call("finite_bit_entry_cases","b","c","l","i","a"), "exact hbits", "exact hi", "exact ha",
             "cases hcase", "rewrite hcase_left", "exists v", "simp",
             f"have hone : {_at('d','e','i','1',tag='fms_subset_one')}", *_call("hsub","i"), "exact hi",
             "rewrite hcase_right at ha", "rewrite hcase_right at ha", "exact ha",
             "have heq : v=1", *_call("beta_at_unique","d","e","i","v","1"), "exact hv", "exact hone",
             "rewrite hcase_right", "rewrite heq", *_call("le_refl","1")),
            "Actual subset inclusion gives pointwise monotonicity of the characteristic bits.",
        ),
        spec(
            "finite_bit_count_subset_le",
            f"forall b c d e l n m. ({_count('b','c','l','n')}) -> ({_count('d','e','l','m')}) -> "
            f"({_subset('b','c','d','e','l')}) -> ({_le('n','m')})",
            ("finite_bit_subset_pointwise_le", "beta_sum_pointwise_le"),
            ("intro b", "intro c", "intro d", "intro e", "intro l", "intro n", "intro m", "intro hn", "intro hm", "intro hsub",
             "cases hn", "cases hm", *_call("beta_sum_pointwise_le","b","c","d","e","l","n","m"),
             *_call("finite_bit_subset_pointwise_le","b","c","d","e","l"), "exact hn_right", "exact hsub", "exact hn_left", "exact hm_left"),
            "Subset inclusion implies the exact inequality between the two witnessed finite cardinalities.",
        ),
    ]
    return tuple(rows)


def _make_strict_counting_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "finite_add_le_add",
            f"forall a b c d. ({_le('a','b')}) -> ({_le('c','d')}) -> ({_le('a+c','b+d')})",
            ("add_le_add_right", "add_le_add_left", "le_trans"),
            ("intro a", "intro b", "intro c", "intro d", "intro hab", "intro hcd",
             *_call("le_trans","a+c","b+c","b+d"), *_call("add_le_add_right","a","b","c"), "exact hab",
             *_call("add_le_add_left","c","d","b"), "exact hcd"),
            "The two genuine finite-order witnesses add componentwise.",
        ),
        spec(
            "finite_add_lt_of_lt_of_le",
            f"forall a b c d. ({_lt('a','b')}) -> ({_le('c','d')}) -> ({_lt('a+c','b+d')})",
            ("finite_add_le_add", "add_succ_left"),
            ("intro a", "intro b", "intro c", "intro d", "intro hab", "intro hcd",
             f"have ht : {_le('(S a)+c','b+d')}", *_call("finite_add_le_add","S a","b","c","d"), "exact hab", "exact hcd",
             "have he : (S a)+c=S(a+c)", *_call("add_succ_left","a","c"), "rewrite he at ht", "exact ht"),
            "A strict left inequality and weak right inequality give a strict sum inequality.",
        ),
        spec(
            "finite_add_lt_of_le_of_lt",
            f"forall a b c d. ({_le('a','b')}) -> ({_lt('c','d')}) -> ({_lt('a+c','b+d')})",
            ("finite_add_le_add",),
            ("intro a", "intro b", "intro c", "intro d", "intro hab", "intro hcd",
             f"have ht : {_le('a+(S c)','b+d')}", *_call("finite_add_le_add","a","b","S c","d"), "exact hab", "exact hcd",
             "have he : a+(S c)=S(a+c)", "apply PA4", "rewrite he at ht", "exact ht"),
            "A weak left inequality and strict right inequality give a strict sum inequality.",
        ),
        spec(
            "finite_sum_entry_le",
            f"forall b c l n i a. ({_sum('b','c','l','n')}) -> ({_lt('i','l')}) -> "
            f"({_at('b','c','i','a',tag='fms_entry_le')}) -> ({_le('a','n')})",
            ("beta_sum_succ_decompose", "finite_lt_succ_eq_or_lt", "beta_at_unique", "le_add_left", "le_add_right", "le_trans", "add_eq_zero_right", "succ_ne_zero"),
            ("intro b", "intro c", "induction l",
             "intro n", "intro i", "intro a", "intro hsum", "intro hi", "intro ha", "exfalso", "cases hi",
             "have hz : S i=0", *_call("add_eq_zero_right","x","S i"), "exact hi_witness", *_call("succ_ne_zero","i"), "exact hz",
             "intro n", "intro i", "intro a", "intro hsum", "intro hi", "intro ha",
             *_sum_decompose("b","c","l","n","hsum","hd"),
             f"have hcase : i=l \\/ ({_lt('i','l')})", *_call("finite_lt_succ_eq_or_lt","l","i"), "exact hi", "cases hcase",
             "rewrite hcase_left at ha", "rewrite hcase_left at ha", "have he : a=x", *_call("beta_at_unique","b","c","l","a","x"),
             "exact ha", "exact hd_witness_witness_left", "rewrite he", "rewrite hd_witness_witness_right_right", *_call("le_add_left","x","x1"),
             "rewrite hd_witness_witness_right_right", *_call("le_trans","a","x1","x1+x"), *_call("IH","x1","i","a"),
             "exact hd_witness_witness_right_left", "exact hcase_right", "exact ha", *_call("le_add_right","x1","x")),
            "Every genuinely decoded summand is bounded by the exact finite sum containing it.",
        ),
        spec(
            "finite_bit_member_count_nonzero",
            f"forall b c l n i. ({_count('b','c','l','n')}) -> ({_member('b','c','l','i')}) -> ~(n=0)",
            ("finite_sum_entry_le", "ne_zero_of_one_le"),
            ("intro b", "intro c", "intro l", "intro n", "intro i", "intro hcount", "intro hmember", "intro hz",
             "cases hcount", "cases hmember", *_call("ne_zero_of_one_le","n"), *_call("finite_sum_entry_le","b","c","l","n","i","1"),
             "exact hcount_left", "exact hmember_left", "exact hmember_right", "exact hz"),
            "An actual bounded member rules out zero for the witnessed set cardinality.",
        ),
        spec(
            "finite_sum_pointwise_strict_at",
            f"forall b c d e l n m i a v. ({_pointwise_le('b','c','d','e','l')}) -> "
            f"({_sum('b','c','l','n')}) -> ({_sum('d','e','l','m')}) -> ({_lt('i','l')}) -> "
            f"({_at('b','c','i','a',tag='fms_strict_left')}) -> ({_at('d','e','i','v',tag='fms_strict_right')}) -> "
            f"({_lt('a','v')}) -> ({_lt('n','m')})",
            ("beta_sum_succ_decompose", "finite_lt_succ_eq_or_lt", "beta_at_unique", "beta_sum_pointwise_le", "le_succ", "le_refl",
             "finite_add_lt_of_lt_of_le", "finite_add_lt_of_le_of_lt", "add_eq_zero_right", "succ_ne_zero"),
            ("intro b", "intro c", "intro d", "intro e", "induction l",
             "intro n", "intro m", "intro i", "intro a", "intro v", "intro hpoint", "intro hn", "intro hm", "intro hi", "intro ha", "intro hv", "intro hav",
             "exfalso", "cases hi", "have hz : S i=0", *_call("add_eq_zero_right","x","S i"), "exact hi_witness", *_call("succ_ne_zero","i"), "exact hz",
             "intro n", "intro m", "intro i", "intro a", "intro v", "intro hpoint", "intro hn", "intro hm", "intro hi", "intro ha", "intro hv", "intro hav",
             *_sum_decompose("b","c","l","n","hn","hdA"), *_sum_decompose("d","e","l","m","hm","hdB"),
             f"have hprefix : {_pointwise_le('b','c','d','e','l')}", "intro j", "intro A", "intro B", "intro hj", "intro hA", "intro hB",
             *_call("hpoint","j","A","B"), *_call("le_succ","S j","l"), "exact hj", "exact hA", "exact hB",
             f"have hlast : {_le('x','x2')}", *_call("hpoint","l","x","x2"), *_call("le_refl","S l"), "exact hdA_witness_witness_left", "exact hdB_witness_witness_left",
             f"have hcase : i=l \\/ ({_lt('i','l')})", *_call("finite_lt_succ_eq_or_lt","l","i"), "exact hi", "cases hcase",
             "rewrite hcase_left at ha", "rewrite hcase_left at ha", "rewrite hcase_left at hv", "rewrite hcase_left at hv",
             "have heA : a=x", *_call("beta_at_unique","b","c","l","a","x"), "exact ha", "exact hdA_witness_witness_left",
             "have heB : v=x2", *_call("beta_at_unique","d","e","l","v","x2"), "exact hv", "exact hdB_witness_witness_left",
             "rewrite heA at hav", "rewrite heB at hav", "rewrite hdA_witness_witness_right_right", "rewrite hdB_witness_witness_right_right",
             *_call("finite_add_lt_of_le_of_lt","x1","x3","x","x2"), *_call("beta_sum_pointwise_le","b","c","d","e","l","x1","x3"),
             "exact hprefix", "exact hdA_witness_witness_right_left", "exact hdB_witness_witness_right_left", "exact hav",
             "rewrite hdA_witness_witness_right_right", "rewrite hdB_witness_witness_right_right",
             *_call("finite_add_lt_of_lt_of_le","x1","x3","x","x2"), *_call("IH","x1","x3","i","a","v"),
             "exact hprefix", "exact hdA_witness_witness_right_left", "exact hdB_witness_witness_right_left", "exact hcase_right", "exact ha", "exact hv", "exact hav", "exact hlast"),
            "A genuine strict pointwise witness makes otherwise monotone finite sums strictly ordered.",
        ),
        spec(
            "finite_bit_count_proper_subset_lt",
            f"forall b c d e l n m i. ({_count('b','c','l','n')}) -> ({_count('d','e','l','m')}) -> "
            f"({_subset('b','c','d','e','l')}) -> ({_lt('i','l')}) -> "
            f"({_at('b','c','i','0',tag='fms_proper_zero')}) -> ({_at('d','e','i','1',tag='fms_proper_one')}) -> ({_lt('n','m')})",
            ("finite_bit_subset_pointwise_le", "finite_sum_pointwise_strict_at", "le_refl"),
            ("intro b", "intro c", "intro d", "intro e", "intro l", "intro n", "intro m", "intro i", "intro hn", "intro hm", "intro hsub", "intro hi", "intro hzero", "intro hone",
             "cases hn", "cases hm", *_call("finite_sum_pointwise_strict_at","b","c","d","e","l","n","m","i","0","1"),
             *_call("finite_bit_subset_pointwise_le","b","c","d","e","l"), "exact hn_right", "exact hsub", "exact hn_left", "exact hm_left", "exact hi", "exact hzero", "exact hone", *_call("le_refl","1")),
            "A witnessed missing member makes a proper subset strictly smaller in exact cardinality.",
        ),
        spec(
            "finite_bit_count_missing_zero",
            f"forall b c l n. ({_count('b','c','l','n')}) -> ~(n=l) -> "
            f"exists i. ({_lt('i','l')}) /\\ ({_at('b','c','i','0',tag='fms_missing_zero')})",
            ("finite_contains_decidable", "beta_all_one_bit_count_exact"),
            ("intro b", "intro c", "intro l", "intro n", "intro hcount", "intro hne",
             "specialize finite_contains_decidable b", "specialize finite_contains_decidable c", "specialize finite_contains_decidable l", "specialize finite_contains_decidable 0",
             "cases finite_contains_decidable", "exact finite_contains_decidable_left", "exfalso", "apply hne",
             *_call("beta_all_one_bit_count_exact","b","c","l","n"),
             "intro i", "intro hi", "cases hcount", "specialize hcount_right i",
             f"have hentry : exists a. ({_at('b','c','i','a',tag='fms_nozero_entry')}) /\\ (a=0 \\/ a=1)", "apply hcount_right", "exact hi",
             "cases hentry", "cases hentry_witness", "cases hentry_witness_right", "exfalso", "apply finite_contains_decidable_right",
             "exists i", "split", "exact hi", "rewrite hentry_witness_right_left at hentry_witness_left", "rewrite hentry_witness_right_left at hentry_witness_left", "exact hentry_witness_left",
             "rewrite hentry_witness_right_right at hentry_witness_left", "rewrite hentry_witness_right_right at hentry_witness_left", "exact hentry_witness_left",
             "exact hcount"),
            "If a bit count is not the ambient size, finite search returns an actual zero position.",
        ),
        spec(
            "finite_bit_count_two_nonzero_member",
            f"forall b c l n. ({_count('b','c','l','n')}) -> ({_le('2','n')}) -> "
            f"exists i. ({_member('b','c','l','i')}) /\\ ~(i=0)",
            ("le_trans", "ne_zero_of_one_le", "nonzero_is_succ", "bit_count_positive_last_one", "le_of_succ_le_succ"),
            ("intro b", "intro c", "intro l", "intro n", "intro hcount", "intro hn",
             f"have hone : {_le('1','n')}", *_call("le_trans","1","2","n"), "exists 1", "simp", "exact hn",
             "have hnonzero : ~(n=0)", "intro hz", *_call("ne_zero_of_one_le","n"), "exact hone", "exact hz",
             "have hsucc : exists q. n=S q", *_call("nonzero_is_succ","n"), "exact hnonzero", "cases hsucc",
             "rewrite hsucc_witness at hcount", "rewrite hsucc_witness at hcount", "rewrite hsucc_witness at hn",
             f"have hw : exists i. ({_lt('i','l')}) /\\ (({_at('b','c','i','1',tag='fms_two_member')}) /\\ ({_le('S x','S i')}))",
             *_call("bit_count_positive_last_one","b","c","l","x"), "exact hcount", "cases hw", "cases hw_witness", "cases hw_witness_right",
             "exists x1", "split", "split", "exact hw_witness_left", "exact hw_witness_right_left", "intro hz",
             *_call("ne_zero_of_one_le","x1"), *_call("le_of_succ_le_succ","1","x1"), *_call("le_trans","2","S x","S x1"), "exact hn", "exact hw_witness_right_right", "exact hz"),
            "A characteristic set with at least two elements has a genuine nonzero canonical member.",
        ),
    )


def _make_boolean_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    balance_script = ["intro b", "intro c", "intro d", "intro e", "intro f", "intro g", "intro h", "intro t", "induction l"]
    balance_intros = ["intro n", "intro m", "intro q", "intro r", "intro hn", "intro hm", "intro hq", "intro hr", "intro hbalance"]
    balance_script.extend(balance_intros)
    for b, c, n, hypothesis in (("b","c","n","hn"),("d","e","m","hm"),("f","g","q","hq"),("h","t","r","hr")):
        balance_script.extend((f"have hzero_{n} : {n}=0", *_call("beta_sum_zero",b,c,n), f"exact {hypothesis}"))
    balance_script.extend(("rewrite hzero_n", "rewrite hzero_m", "rewrite hzero_q", "rewrite hzero_r", "refl"))
    balance_script.extend(balance_intros)
    for b,c,n,hypothesis,label in (("b","c","n","hn","hdA"),("d","e","m","hm","hdB"),("f","g","q","hq","hdC"),("h","t","r","hr","hdD")):
        balance_script.extend(_sum_decompose(b,c,"l",n,hypothesis,label))
    balance_script.extend((
        "have hprefix : x1+x3=x5+x7", *_call("IH","x1","x3","x5","x7"),
        "exact hdA_witness_witness_right_left", "exact hdB_witness_witness_right_left", "exact hdC_witness_witness_right_left", "exact hdD_witness_witness_right_left",
        "intro i", "intro a", "intro v", "intro w", "intro z", "intro hi", "intro ha", "intro hv", "intro hw", "intro hz",
        *_call("hbalance","i","a","v","w","z"), *_call("le_succ","S i","l"), "exact hi", "exact ha", "exact hv", "exact hw", "exact hz",
        "have hlast : x+x2=x4+x6", *_call("hbalance","l","x","x2","x4","x6"), *_call("le_refl","S l"),
        "exact hdA_witness_witness_left", "exact hdB_witness_witness_left", "exact hdC_witness_witness_left", "exact hdD_witness_witness_left",
        "rewrite hdA_witness_witness_right_right", "rewrite hdB_witness_witness_right_right", "rewrite hdC_witness_witness_right_right", "rewrite hdD_witness_witness_right_right",
        "trans (x1+x3)+(x+x2)", "simp [add_assoc, add_comm]", "rewrite hprefix", "rewrite hlast", "simp [add_assoc, add_comm]",
    ))
    return (
        spec(
            "finite_sum_pointwise_balance",
            f"forall b c d e f g h t l n m q r. ({_sum('b','c','l','n')}) -> ({_sum('d','e','l','m')}) -> "
            f"({_sum('f','g','l','q')}) -> ({_sum('h','t','l','r')}) -> ({_sum_balance('b','c','d','e','f','g','h','t','l')}) -> n+m=q+r",
            ("beta_sum_zero", "beta_sum_succ_decompose", "le_succ", "le_refl", "add_assoc", "add_comm"), tuple(balance_script),
            "A pointwise four-prefix balance gives the exact corresponding balance of all four finite sums.",
        ),
        spec(
            "finite_bit_product_cases",
            "forall a b. (a=0 \\/ a=1) -> (b=0 \\/ b=1) -> a*b=0 \\/ a*b=1",
            ("mul_zero_left",),
            ("intro a", "intro b", "intro ha", "intro hb", "cases ha", "left", "rewrite ha_left", "simp [mul_zero_left]",
             "cases hb", "left", "rewrite hb_left", "simp", "right", "rewrite ha_right", "rewrite hb_right", "simp"),
            "The product of two actual zero-or-one values is again zero or one.",
        ),
        spec(
            "finite_bit_intersection_from_product",
            f"forall b c d e u v l. ({_product('b','c','d','e','u','v','l')}) -> ({_binary('b','c','d','e','u','v','l',_AND)})",
            ("beta_at_exists", "mul_eq_one_components"),
            ("intro b", "intro c", "intro d", "intro e", "intro u", "intro v", "intro l", "intro hproduct", "intro i", "intro hi", "split",
             "intro hone",
             f"have ha : exists a. {_at('b','c','i','a',tag='fms_inter_a')}", *_call("beta_at_exists","b","c","i"), "cases ha",
             f"have hb : exists a. {_at('d','e','i','a',tag='fms_inter_b')}", *_call("beta_at_exists","d","e","i"), "cases hb",
             "have he : 1=x*x1", *_call("hproduct","i","x","x1","1"), "exact hi", "exact ha_witness", "exact hb_witness", "exact hone",
             "have hones : x=1 /\\ x1=1", *_call("mul_eq_one_components","x","x1"), "symm", "exact he", "cases hones", "split",
             "rewrite hones_left at ha_witness", "rewrite hones_left at ha_witness", "exact ha_witness",
             "rewrite hones_right at hb_witness", "rewrite hones_right at hb_witness", "exact hb_witness",
             "intro hboth", "cases hboth",
             f"have hw : exists a. {_at('u','v','i','a',tag='fms_inter_w')}", *_call("beta_at_exists","u","v","i"), "cases hw",
             "have he : x=1*1", *_call("hproduct","i","1","1","x"), "exact hi", "exact hboth_left", "exact hboth_right", "exact hw_witness",
             "have hone : x=1", "trans 1*1", "exact he", "simp", "rewrite hone at hw_witness", "rewrite hone at hw_witness", "exact hw_witness"),
            "An actual pointwise product code has exactly the membership of the finite-set intersection.",
        ),
        spec(
            "finite_bit_intersection_exists",
            f"forall b c d e l n m. ({_count('b','c','l','n')}) -> ({_count('d','e','l','m')}) -> "
            f"exists u v q. ({_count('u','v','l','q')}) /\\ ({_binary('b','c','d','e','u','v','l',_AND)})",
            ("beta_pointwise_mul_prefix_exists", "beta_at_exists", "finite_bit_entry_cases", "finite_bit_product_cases", "bit_count_exists", "finite_bit_intersection_from_product"),
            ("intro b", "intro c", "intro d", "intro e", "intro l", "intro n", "intro m", "intro hn", "intro hm",
             f"have hcode : exists u v. {_product('b','c','d','e','u','v','l')}", *_call("beta_pointwise_mul_prefix_exists","b","c","d","e","l"),
             "cases hcode", "cases hcode_witness", "cases hn", "cases hm",
             f"have hbits : {_bits('x','x1','l')}", "intro i", "intro hi",
             f"have ha : exists a. {_at('b','c','i','a',tag='fms_inter_exists_a')}", *_call("beta_at_exists","b","c","i"), "cases ha",
             f"have hb : exists a. {_at('d','e','i','a',tag='fms_inter_exists_b')}", *_call("beta_at_exists","d","e","i"), "cases hb",
             f"have hw : exists a. {_at('x','x1','i','a',tag='fms_inter_exists_w')}", *_call("beta_at_exists","x","x1","i"), "cases hw",
             "have he : x4=x2*x3", *_call("hcode_witness_witness","i","x2","x3","x4"), "exact hi", "exact ha_witness", "exact hb_witness", "exact hw_witness",
             "exists x4", "split", "exact hw_witness", "rewrite he", "rewrite he", *_call("finite_bit_product_cases","x2","x3"),
             *_call("finite_bit_entry_cases","b","c","l","i","x2"), "exact hn_right", "exact hi", "exact ha_witness",
             *_call("finite_bit_entry_cases","d","e","l","i","x3"), "exact hm_right", "exact hi", "exact hb_witness",
             f"have hcount : exists q. {_count('x','x1','l','q')}", *_call("bit_count_exists","x","x1","l"), "exact hbits", "cases hcount",
             "exists x", "exists x1", "exists x2", "split", "exact hcount_witness", *_call("finite_bit_intersection_from_product","b","c","d","e","x","x1","l"), "exact hcode_witness_witness"),
            "Construct an actual characteristic intersection code and its exact finite count.",
        ),
        spec(
            "finite_bit_complement_exists",
            f"forall b c l n. ({_count('b','c','l','n')}) -> exists d e m. ({_count('d','e','l','m')}) /\\ "
            f"(({_complement('b','c','d','e','l')}) /\\ n+m=l)",
            ("beta_sign_factor_prefix_exists", "beta_at_exists", "beta_at_unique", "bit_count_exists", "complementary_bit_counts_add_length"),
            ("intro b", "intro c", "intro l", "intro n", "intro hn",
             f"have hcode : exists d e. {_sign_complement('b','c','d','e','l')}", *_call("beta_sign_factor_prefix_exists","b","c","0","l","n"), "exact hn",
             "cases hcode", "cases hcode_witness",
             f"have hbits : {_bits('x','x1','l')}", "intro i", "intro hi",
             f"have ha : exists a. {_at('b','c','i','a',tag='fms_comp_source')}", *_call("beta_at_exists","b","c","i"), "cases ha",
             f"have hc : (x2=0 /\\ ({_at('x','x1','i','1',tag='fms_comp_one')})) \\/ (x2=1 /\\ ({_at('x','x1','i','0',tag='fms_comp_zero')}))",
             *_call("hcode_witness_witness","i","x2"), "exact hi", "exact ha_witness", "cases hc",
             "cases hc_left", "exists 1", "split", "exact hc_left_right", "right", "refl",
             "cases hc_right", "exists 0", "split", "exact hc_right_right", "left", "refl",
             f"have hcomp : {_complement('b','c','x','x1','l')}", "intro i", "intro a", "intro v", "intro hi", "intro ha", "intro hv",
             f"have hc : (a=0 /\\ ({_at('x','x1','i','1',tag='fms_comp_univ_one')})) \\/ (a=1 /\\ ({_at('x','x1','i','0',tag='fms_comp_univ_zero')}))",
             *_call("hcode_witness_witness","i","a"), "exact hi", "exact ha", "cases hc", "cases hc_left", "left", "split", "exact hc_left_left",
             *_call("beta_at_unique","x","x1","i","v","1"), "exact hv", "exact hc_left_right",
             "cases hc_right", "right", "split", "exact hc_right_left", *_call("beta_at_unique","x","x1","i","v","0"), "exact hv", "exact hc_right_right",
             f"have hcount : exists m. {_count('x','x1','l','m')}", *_call("bit_count_exists","x","x1","l"), "exact hbits", "cases hcount",
             "exists x", "exists x1", "exists x2", "split", "exact hcount_witness", "split", "exact hcomp",
             *_call("complementary_bit_counts_add_length","b","c","x","x1","l","n","x2"), "exact hn", "exact hcount_witness", "exact hcomp"),
            "Construct the genuine characteristic complement and prove its count adds to the ambient size.",
        ),
        spec(
            "finite_bit_complement_member_iff",
            f"forall b c d e l i. ({_complement('b','c','d','e','l')}) -> ({_lt('i','l')}) -> "
            f"({_iff(_at('d','e','i','1',tag='fms_comp_iff_t'),_not(_at('b','c','i','1',tag='fms_comp_iff_s')))})",
            ("beta_at_exists", "succ_ne_zero"),
            ("intro b", "intro c", "intro d", "intro e", "intro l", "intro i", "intro hcomp", "intro hi", "split",
             "intro ht", "intro hs", "have hc : (1=0 /\\ 1=1) \\/ (1=1 /\\ 1=0)", *_call("hcomp","i","1","1"), "exact hi", "exact hs", "exact ht",
             "cases hc", "cases hc_left", *_call("succ_ne_zero","0"), "exact hc_left_left", "cases hc_right", *_call("succ_ne_zero","0"), "exact hc_right_right",
             "intro hnot",
             f"have ha : exists a. {_at('b','c','i','a',tag='fms_comp_iff_a')}", *_call("beta_at_exists","b","c","i"), "cases ha",
             f"have hv : exists a. {_at('d','e','i','a',tag='fms_comp_iff_v')}", *_call("beta_at_exists","d","e","i"), "cases hv",
             "have hc : (x=0 /\\ x1=1) \\/ (x=1 /\\ x1=0)", *_call("hcomp","i","x","x1"), "exact hi", "exact ha_witness", "exact hv_witness",
             "cases hc", "cases hc_left", "rewrite hc_left_right at hv_witness", "rewrite hc_left_right at hv_witness", "exact hv_witness",
             "cases hc_right", "exfalso", "apply hnot", "rewrite hc_right_left at ha_witness", "rewrite hc_right_left at ha_witness", "exact ha_witness"),
            "Membership in the constructed complement is exactly constructive nonmembership in its source.",
        ),
    )


def _make_union_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    union_script = [
        "intro b", "intro c", "intro d", "intro e", "intro ab", "intro ac", "intro bb", "intro bc", "intro ib", "intro ic", "intro ub", "intro uc", "intro l",
        "intro hbitsA", "intro hbitsB", "intro hcompA", "intro hcompB", "intro hinter", "intro hcompI", "intro i", "intro hi",
    ]
    for b,c,d,e,hypothesis,label in (("b","c","ab","ac","hcompA","hA"),("d","e","bb","bc","hcompB","hB"),("ib","ic","ub","uc","hcompI","hI")):
        union_script.extend((
            f"have {label} : {_iff(_at(d,e,'i','1',tag=f'fms_{label}_target'),_not(_at(b,c,'i','1',tag=f'fms_{label}_source')))}",
            *_call("finite_bit_complement_member_iff",b,c,d,e,"l","i"), f"exact {hypothesis}", "exact hi", f"cases {label}",
        ))
    inter_ones = f"(({_at('ab','ac','i','1',tag='fms_union_CA')}) /\\ ({_at('bb','bc','i','1',tag='fms_union_CB')}))"
    union_script.extend((
        f"have hpair : {_iff(_at('ib','ic','i','1',tag='fms_union_I'),inter_ones)}", *_call("hinter","i"), "exact hi", "cases hpair", "split", "intro hu",
        f"have hnot : ~({_at('ib','ic','i','1',tag='fms_union_notI')})", "intro hx", "apply hI_left", "exact hu", "exact hx",
        f"have hdA : ({_at('b','c','i','1',tag='fms_union_decA')}) \\/ ~({_at('b','c','i','1',tag='fms_union_decA')})",
        *_call("finite_bit_membership_decidable","b","c","l","i"), "exact hbitsA", "exact hi", "cases hdA", "left", "exact hdA_left",
        f"have hdB : ({_at('d','e','i','1',tag='fms_union_decB')}) \\/ ~({_at('d','e','i','1',tag='fms_union_decB')})",
        *_call("finite_bit_membership_decidable","d","e","l","i"), "exact hbitsB", "exact hi", "cases hdB", "right", "exact hdB_left",
        "exfalso", "apply hnot", "apply hpair_right", "split", "apply hA_right", "exact hdA_right", "apply hB_right", "exact hdB_right",
        "intro hab", "apply hI_right", "intro hione", f"have hboth : {inter_ones}", "apply hpair_left", "exact hione", "cases hboth", "cases hab",
        "apply hA_left", "exact hboth_left", "exact hab_left", "apply hB_left", "exact hboth_right", "exact hab_right",
    ))
    exists_script = ["intro b", "intro c", "intro d", "intro e", "intro l", "intro n", "intro m", "intro hn", "intro hm"]
    for b,c,n,hypothesis,label in (("b","c","n","hn","hA"),("d","e","m","hm","hB")):
        exists_script.extend((
            f"have {label} : exists u v q. ({_count('u','v','l','q',tag=label)}) /\\ (({_complement(b,c,'u','v','l',tag=label)}) /\\ {n}+q=l)",
            *_call("finite_bit_complement_exists",b,c,"l",n), f"exact {hypothesis}",
            f"cases {label}", f"cases {label}_witness", f"cases {label}_witness_witness", f"cases {label}_witness_witness_witness", f"cases {label}_witness_witness_witness_right",
        ))
    exists_script.extend((
        f"have hI : exists u v q. ({_count('u','v','l','q',tag='union_inter')}) /\\ ({_binary('x','x1','x3','x4','u','v','l',_AND,tag='union_inter')})",
        *_call("finite_bit_intersection_exists","x","x1","x3","x4","l","x2","x5"), "exact hA_witness_witness_witness_left", "exact hB_witness_witness_witness_left",
        "cases hI", "cases hI_witness", "cases hI_witness_witness", "cases hI_witness_witness_witness",
        f"have hU : exists u v q. ({_count('u','v','l','q',tag='union_final')}) /\\ (({_complement('x6','x7','u','v','l',tag='union_final')}) /\\ x8+q=l)",
        *_call("finite_bit_complement_exists","x6","x7","l","x8"), "exact hI_witness_witness_witness_left",
        "cases hU", "cases hU_witness", "cases hU_witness_witness", "cases hU_witness_witness_witness", "cases hU_witness_witness_witness_right",
        "exists x9", "exists x10", "exists x11", "split", "exact hU_witness_witness_witness_left", "cases hn", "cases hm",
        *_call("finite_bit_union_of_complements","b","c","d","e","x","x1","x3","x4","x6","x7","x9","x10","l"),
        "exact hn_right", "exact hm_right", "exact hA_witness_witness_witness_right_left", "exact hB_witness_witness_witness_right_left",
        "exact hI_witness_witness_witness_right", "exact hU_witness_witness_witness_right_left",
    ))
    return (
        spec(
            "finite_bit_union_of_complements",
            f"forall b c d e ab ac bb bc ib ic ub uc l. ({_bits('b','c','l')}) -> ({_bits('d','e','l')}) -> "
            f"({_complement('b','c','ab','ac','l')}) -> ({_complement('d','e','bb','bc','l')}) -> "
            f"({_binary('ab','ac','bb','bc','ib','ic','l',_AND)}) -> ({_complement('ib','ic','ub','uc','l')}) -> "
            f"({_binary('b','c','d','e','ub','uc','l',_OR)})",
            ("finite_bit_complement_member_iff", "finite_bit_membership_decidable"), tuple(union_script),
            "Actual characteristic complements and intersection construct the exact union by decidable finite De Morgan reasoning.",
        ),
        spec(
            "finite_bit_union_exists",
            f"forall b c d e l n m. ({_count('b','c','l','n')}) -> ({_count('d','e','l','m')}) -> "
            f"exists u v q. ({_count('u','v','l','q')}) /\\ ({_binary('b','c','d','e','u','v','l',_OR)})",
            ("finite_bit_complement_exists", "finite_bit_intersection_exists", "finite_bit_union_of_complements"), tuple(exists_script),
            "Construct an actual beta characteristic union and a genuinely witnessed finite cardinality.",
        ),
    )


def _make_union_count_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    numeric_or, numeric_and = "a=1 \\/ b=1", "a=1 /\\ b=1"
    truth_script = ["intro a", "intro b", "intro u", "intro v", "intro hA", "intro hB", "intro hU", "intro hI", "intro hOr", "intro hAnd", "cases hOr", "cases hAnd"]
    def truth_branches(index: int, values: tuple[int, ...]) -> tuple[str, ...]:
        labels = ("hA", "hB", "hU", "hI")
        if index < 4:
            return (f"cases {labels[index]}", *truth_branches(index+1,values+(0,)), *truth_branches(index+1,values+(1,)))
        a,b,u,v = values
        equations = tuple(f"{label}_{'right' if value else 'left'}" for label,value in zip(labels,values))
        ea,eb,eu,ev = equations
        if u == max(a,b) and v == min(a,b):
            return (f"rewrite {eu}",f"rewrite {ev}",f"rewrite {ea}",f"rewrite {eb}","simp")
        if u == 0 and max(a,b) == 1:
            return ("have hu : u=1", "apply hOr_right", "left" if a else "right", f"exact {ea if a else eb}",
                    "exfalso", *_call("finite_bit_zero_one_conflict","u"), f"exact {eu}", "exact hu")
        if u == 1 and max(a,b) == 0:
            return ("have hab : a=1 \\/ b=1", "apply hOr_left", f"exact {eu}", "cases hab",
                    "exfalso", *_call("finite_bit_zero_one_conflict","a"), f"exact {ea}", "exact hab_left",
                    "exfalso", *_call("finite_bit_zero_one_conflict","b"), f"exact {eb}", "exact hab_right")
        if v == 0:
            return ("have hv : v=1", "apply hAnd_right", "split", f"exact {ea}", f"exact {eb}",
                    "exfalso", *_call("finite_bit_zero_one_conflict","v"), f"exact {ev}", "exact hv")
        return ("have hab : a=1 /\\ b=1", "apply hAnd_left", f"exact {ev}", "cases hab", "exfalso",
                *_call("finite_bit_zero_one_conflict","a" if not a else "b"), f"exact {ea if not a else eb}", "exact hab_left" if not a else "exact hab_right")
    truth_script.extend(truth_branches(0,()))
    count_script = [
        "intro ab", "intro ac", "intro bb", "intro bc", "intro ub", "intro uc", "intro ib", "intro ic", "intro l", "intro n", "intro m", "intro q", "intro r",
        "intro hA", "intro hB", "intro hU", "intro hI", "intro hUnion", "intro hInter", "cases hA", "cases hB", "cases hU", "cases hI",
        *_call("finite_sum_pointwise_balance","ub","uc","ib","ic","ab","ac","bb","bc","l","q","r","n","m"),
        "exact hU_left", "exact hI_left", "exact hA_left", "exact hB_left",
        "intro i", "intro u", "intro v", "intro a", "intro b", "intro hi", "intro hu", "intro hv", "intro ha", "intro hb",
    ]
    for code,scale,value,hypothesis,label in (("ab","ac","a","ha","hAe"),("bb","bc","b","hb","hBe"),("ub","uc","u","hu","hUe"),("ib","ic","v","hv","hIe")):
        count_script.extend((
            f"have {label} : {_iff(f'{value}=1',_at(code,scale,'i','1',tag=f'fms_{label}'))}",
            *_call("finite_beta_value_one_iff",code,scale,"i",value), f"exact {hypothesis}", f"cases {label}",
        ))
    union_bits = f"(({_at('ab','ac','i','1',tag='fms_balance_A')}) \\/ ({_at('bb','bc','i','1',tag='fms_balance_B')}))"
    inter_bits = f"(({_at('ab','ac','i','1',tag='fms_balance_A')}) /\\ ({_at('bb','bc','i','1',tag='fms_balance_B')}))"
    count_script.extend((
        f"have hUn : {_iff(_at('ub','uc','i','1',tag='fms_balance_U'),union_bits)}", *_call("hUnion","i"), "exact hi", "cases hUn",
        f"have hIn : {_iff(_at('ib','ic','i','1',tag='fms_balance_I'),inter_bits)}", *_call("hInter","i"), "exact hi", "cases hIn",
        *_call("finite_bit_union_intersection_values","a","b","u","v"),
    ))
    for code,scale,value,hypothesis,bits in (("ab","ac","a","ha","hA_right"),("bb","bc","b","hb","hB_right"),("ub","uc","u","hu","hU_right"),("ib","ic","v","hv","hI_right")):
        count_script.extend((*_call("finite_bit_entry_cases",code,scale,"l","i",value),f"exact {bits}","exact hi",f"exact {hypothesis}"))
    count_script.extend((
        "split", "intro hue", f"have hab : {union_bits}", "apply hUn_left", "apply hUe_left", "exact hue", "cases hab",
        "left", "apply hAe_right", "exact hab_left", "right", "apply hBe_right", "exact hab_right",
        "intro hab", "apply hUe_right", "apply hUn_right", "cases hab", "left", "apply hAe_left", "exact hab_left", "right", "apply hBe_left", "exact hab_right",
        "split", "intro hie", f"have hab : {inter_bits}", "apply hIn_left", "apply hIe_left", "exact hie", "cases hab", "split",
        "apply hAe_right", "exact hab_left", "apply hBe_right", "exact hab_right",
        "intro hab", "cases hab", "apply hIe_right", "apply hIn_right", "split", "apply hAe_left", "exact hab_left", "apply hBe_left", "exact hab_right",
    ))
    return (
        spec(
            "finite_bit_zero_one_conflict", "forall a. a=0 -> a=1 -> bot", ("succ_ne_zero",),
            ("intro a", "intro hz", "intro ho", *_call("succ_ne_zero","0"), "trans a", "symm", "exact ho", "exact hz"),
            "The two characteristic-bit values are constructively distinct.",
        ),
        spec(
            "finite_beta_value_one_iff",
            f"forall b c i a. ({_at('b','c','i','a',tag='fms_value_one')}) -> ({_iff('a=1',_at('b','c','i','1',tag='fms_value_one_result'))})",
            ("beta_at_unique",),
            ("intro b", "intro c", "intro i", "intro a", "intro ha", "split", "intro he", "rewrite he at ha", "rewrite he at ha", "exact ha",
             "intro hone", *_call("beta_at_unique","b","c","i","a","1"), "exact ha", "exact hone"),
            "For an actual decoded entry, being one is exactly characteristic membership.",
        ),
        spec(
            "finite_bit_nonmember_zero",
            f"forall b c l i. ({_bits('b','c','l')}) -> ({_lt('i','l')}) -> ~({_at('b','c','i','1',tag='fms_not_member')}) -> ({_at('b','c','i','0',tag='fms_zero_member')})",
            ("beta_at_exists", "finite_bit_entry_cases"),
            ("intro b", "intro c", "intro l", "intro i", "intro hbits", "intro hi", "intro hnot",
             "specialize beta_at_exists b", "specialize beta_at_exists c", "specialize beta_at_exists i", "cases beta_at_exists",
             "have hc : x=0 \\/ x=1", *_call("finite_bit_entry_cases","b","c","l","i","x"), "exact hbits", "exact hi", "exact beta_at_exists_witness", "cases hc",
             "rewrite hc_left at beta_at_exists_witness", "rewrite hc_left at beta_at_exists_witness", "exact beta_at_exists_witness",
             "exfalso", "apply hnot", "rewrite hc_right at beta_at_exists_witness", "rewrite hc_right at beta_at_exists_witness", "exact beta_at_exists_witness"),
            "Constructive nonmembership at a bounded index exposes its actual zero bit.",
        ),
        spec(
            "finite_bit_union_intersection_values",
            "forall a b u v. (a=0 \\/ a=1) -> (b=0 \\/ b=1) -> (u=0 \\/ u=1) -> (v=0 \\/ v=1) -> "
            f"({_iff('u=1',numeric_or)}) -> ({_iff('v=1',numeric_and)}) -> u+v=a+b",
            ("finite_bit_zero_one_conflict",), tuple(truth_script),
            "The exact finite Boolean union/intersection truth table preserves the sum of the two input bits.",
        ),
        spec(
            "finite_bit_union_intersection_count_balance",
            f"forall ab ac bb bc ub uc ib ic l n m q r. ({_count('ab','ac','l','n')}) -> ({_count('bb','bc','l','m')}) -> "
            f"({_count('ub','uc','l','q')}) -> ({_count('ib','ic','l','r')}) -> "
            f"({_binary('ab','ac','bb','bc','ub','uc','l',_OR)}) -> ({_binary('ab','ac','bb','bc','ib','ic','l',_AND)}) -> q+r=n+m",
            ("finite_sum_pointwise_balance", "finite_beta_value_one_iff", "finite_bit_entry_cases", "finite_bit_union_intersection_values"), tuple(count_script),
            "The genuinely counted union and intersection have cardinalities summing exactly to those of both inputs.",
        ),
    )


def _make_translation_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    indices_entry = (
        f"exists a q v. ({_at('x','x1','i','a',tag='fms_tindex_source')}) /\\ "
        f"(({_at('x2','x3','i','q',tag='fms_tindex_quotient')}) /\\ "
        f"(({_at('x4','x5','i','v',tag='fms_tindex_remainder')}) /\\ (a=p*q+v /\\ ({_lt('v','p')}))))"
    )
    return (
        spec(
            "finite_beta_composition_exists",
            f"forall r s b c l. exists z d. ({_compose('r','s','b','c','z','d','l')})",
            ("beta_prefix_extend", "beta_at_exists", "beta_at_unique", "finite_lt_succ_eq_or_lt", "add_eq_zero_right", "succ_ne_zero"),
            ("intro r", "intro s", "intro b", "intro c", "induction l", "exists 0", "exists 0",
             "intro i", "intro j", "intro v", "intro hi", "intro hj", "intro hv", "exfalso", "cases hi", "have hz : S i=0", *_call("add_eq_zero_right","x","S i"), "exact hi_witness", *_call("succ_ne_zero","i"), "exact hz",
             "cases IH", "cases IH_witness",
             f"have hj : exists j. {_at('r','s','l','j',tag='fms_compose_last_index')}", *_call("beta_at_exists","r","s","l"), "cases hj",
             f"have hv : exists v. {_at('b','c','x2','v',tag='fms_compose_last_value')}", *_call("beta_at_exists","b","c","x2"), "cases hv",
             "specialize beta_prefix_extend l", "specialize beta_prefix_extend x", "specialize beta_prefix_extend x1", "specialize beta_prefix_extend x3",
             "cases beta_prefix_extend", "cases beta_prefix_extend_witness", "cases beta_prefix_extend_witness_witness",
             "exists x4", "exists x5", "intro i", "intro j", "intro v", "intro hi", "intro hji", "intro hvj",
             f"have hcase : i=l \\/ ({_lt('i','l')})", *_call("finite_lt_succ_eq_or_lt","l","i"), "exact hi", "cases hcase",
             "rewrite hcase_left at hji", "rewrite hcase_left at hji", "have hjeq : j=x2", *_call("beta_at_unique","r","s","l","j","x2"), "exact hji", "exact hj_witness",
             "rewrite hjeq at hvj", "rewrite hjeq at hvj", "have hveq : v=x3", *_call("beta_at_unique","b","c","x2","v","x3"), "exact hvj", "exact hv_witness",
             "rewrite hcase_left", "rewrite hcase_left", "rewrite hveq", "rewrite hveq", "exact beta_prefix_extend_witness_witness_left",
             *_call("beta_prefix_extend_witness_witness_right","i","v"), "exact hcase_right", *_call("IH_witness_witness","i","j","v"), "exact hcase_right", "exact hji", "exact hvj"),
            "Construct an actual finite beta code for composition of two arbitrary decoded beta functions.",
        ),
        spec(
            "finite_modular_translation_indices_exists",
            f"forall p t l. ~(p=0) -> exists r s. ({_translation_indices('p','t','r','s','l')})",
            ("beta_range_exists", "beta_division_prefix_exists", "beta_at_unique", "remainder_decomposition_to_mod_eq", "add_comm", "mul_comm"),
            ("intro p", "intro t", "intro l", "intro hp",
             f"have hrange : exists b c. {range_relation('b','c','t','l',tag='fms_translation_range')}", *_call("beta_range_exists","t","l"), "cases hrange", "cases hrange_witness",
             f"have hdivision : exists qb qc rb rc. {division_prefix('p','x','x1','qb','qc','rb','rc','l',tag='fms_translation_division')}", *_call("beta_division_prefix_exists","p","x","x1","l"), "exact hp",
             "cases hdivision", "cases hdivision_witness", "cases hdivision_witness_witness", "cases hdivision_witness_witness_witness",
             "exists x4", "exists x5", "intro i", "intro hi", f"have hentry : {indices_entry}", *_call("hdivision_witness_witness_witness_witness","i"), "exact hi",
             "cases hentry", "cases hentry_witness", "cases hentry_witness_witness", "cases hentry_witness_witness_witness", "cases hentry_witness_witness_witness_right", "cases hentry_witness_witness_witness_right_right", "cases hentry_witness_witness_witness_right_right_right",
             "have he : x6=t+i", *_call("beta_at_unique","x","x1","i","x6","t+i"), "exact hentry_witness_witness_witness_left", *_call("hrange_witness_witness","i"), "exact hi",
             "exists x8", "split", "exact hentry_witness_witness_witness_right_right_left", "split", "exact hentry_witness_witness_witness_right_right_right_right",
             *_call("remainder_decomposition_to_mod_eq","p","i+t","x7","x8"), "trans t+i", *_call("add_comm","i","t"), "trans x6", "symm", "exact he",
             "trans p*x7+x8", "exact hentry_witness_witness_witness_right_right_right_left", "congr", *_call("mul_comm","p","x7"), "refl"),
            "Construct actual canonical modular-translation indices by a range code and genuine quotient/remainder recoding.",
        ),
        spec(
            "finite_modular_translation_index_entry",
            f"forall p t r s l i j. ({_translation_indices('p','t','r','s','l')}) -> ({_lt('i','l')}) -> "
            f"({_at('r','s','i','j',tag='fms_index_entry')}) -> ({_lt('j','p')}) /\\ ({_mod('p','i+t','j')})",
            ("beta_at_unique",),
            ("intro p", "intro t", "intro r", "intro s", "intro l", "intro i", "intro j", "intro hindices", "intro hi", "intro hj",
             f"have hv : exists v. ({_at('r','s','i','v',tag='fms_index_chosen')}) /\\ (({_lt('v','p')}) /\\ ({_mod('p','i+t','v')}))",
             *_call("hindices","i"), "exact hi", "cases hv", "cases hv_witness", "have he : x=j", *_call("beta_at_unique","r","s","i","x","j"), "exact hv_witness_left", "exact hj",
             "rewrite he at hv_witness_right", "rewrite he at hv_witness_right", "exact hv_witness_right"),
            "Every actual decoded modular-translation index has the canonical bound and the required congruence.",
        ),
        spec(
            "finite_modular_translation_indices_permutation",
            f"forall p t r s. ({_translation_indices('p','t','r','s','p')}) -> "
            f"({bounded_prefix('r','s','p',tag='fms_translation_bounded')}) /\\ ({injective_prefix('r','s','p',tag='fms_translation_injective')})",
            ("finite_modular_translation_index_entry", "mod_eq_bounded_unique", "mod_eq_trans", "mod_eq_symm", "mod_eq_add_cancel_right"),
            ("intro p", "intro t", "intro r", "intro s", "intro hindices", "split", "intro i", "intro hi",
             f"have hv : exists v. ({_at('r','s','i','v',tag='fms_permutation_index')}) /\\ (({_lt('v','p')}) /\\ ({_mod('p','i+t','v')}))",
             *_call("hindices","i"), "exact hi", "cases hv", "cases hv_witness", "cases hv_witness_right", "exists x", "split", "exact hv_witness_left", "exact hv_witness_right_left",
             "intro i", "intro j", "intro v", "intro hi", "intro hj", "intro hiv", "intro hjv",
             f"have hleft : ({_lt('v','p')}) /\\ ({_mod('p','i+t','v')})", *_call("finite_modular_translation_index_entry","p","t","r","s","p","i","v"), "exact hindices", "exact hi", "exact hiv", "cases hleft",
             f"have hright : ({_lt('v','p')}) /\\ ({_mod('p','j+t','v')})", *_call("finite_modular_translation_index_entry","p","t","r","s","p","j","v"), "exact hindices", "exact hj", "exact hjv", "cases hright",
             *_call("mod_eq_bounded_unique","p","i","j"), "exact hi", "exact hj", *_call("mod_eq_add_cancel_right","p","i","j","t"),
             *_call("mod_eq_trans","p","i+t","v","j+t"), "exact hleft_right", *_call("mod_eq_symm","p","j+t","v"), "exact hright_right"),
            "Canonical modular translation is a genuinely beta-coded bounded injection and hence a finite permutation.",
        ),
        spec(
            "finite_modular_composition_all_bits",
            f"forall p t r s b c z d. ({_translation_indices('p','t','r','s','p')}) -> ({_compose('r','s','b','c','z','d','p')}) -> "
            f"({_bits('b','c','p')}) -> ({_bits('z','d','p')})",
            (),
            ("intro p", "intro t", "intro r", "intro s", "intro b", "intro c", "intro z", "intro d", "intro hindices", "intro hcompose", "intro hbits", "intro i", "intro hi",
             f"have hj : exists j. ({_at('r','s','i','j',tag='fms_comp_bits_index')}) /\\ (({_lt('j','p')}) /\\ ({_mod('p','i+t','j')}))",
             *_call("hindices","i"), "exact hi", "cases hj", "cases hj_witness", "cases hj_witness_right",
             f"have hv : exists v. ({_at('b','c','x','v',tag='fms_comp_bits_source')}) /\\ (v=0 \\/ v=1)", *_call("hbits","x"), "exact hj_witness_right_left", "cases hv", "cases hv_witness",
             "exists x1", "split", *_call("hcompose","i","x","x1"), "exact hi", "exact hj_witness_left", "exact hv_witness_left", "exact hv_witness_right"),
            "The actual modular pullback of a characteristic prefix remains an actual characteristic prefix.",
        ),
        spec(
            "finite_modular_composition_pullback",
            f"forall p t r s b c z d. ({_translation_indices('p','t','r','s','p')}) -> ({_compose('r','s','b','c','z','d','p')}) -> "
            f"({_pullback('b','c','z','d','p','t')})",
            ("mod_eq_bounded_unique", "mod_eq_trans", "mod_eq_symm", "beta_at_exists", "beta_at_unique"),
            ("intro p", "intro t", "intro r", "intro s", "intro b", "intro c", "intro z", "intro d", "intro hindices", "intro hcompose",
             "intro i", "intro j", "intro hi", "intro hj", "intro hmod",
             f"have hk : exists k. ({_at('r','s','i','k',tag='fms_pullback_index')}) /\\ (({_lt('k','p')}) /\\ ({_mod('p','i+t','k')}))",
             *_call("hindices","i"), "exact hi", "cases hk", "cases hk_witness", "cases hk_witness_right",
             "have he : x=j", *_call("mod_eq_bounded_unique","p","x","j"), "exact hk_witness_right_left", "exact hj", *_call("mod_eq_trans","p","x","i+t","j"),
             *_call("mod_eq_symm","p","i+t","x"), "exact hk_witness_right_right", "exact hmod",
             "rewrite he at hk_witness_left", "rewrite he at hk_witness_left", "split", "intro ht",
             f"have ha : exists a. {_at('b','c','j','a',tag='fms_pullback_source')}", *_call("beta_at_exists","b","c","j"), "cases ha",
             f"have hv : {_at('z','d','i','x1',tag='fms_pullback_target')}", *_call("hcompose","i","j","x1"), "exact hi", "exact hk_witness_left", "exact ha_witness",
             "have hone : x1=1", *_call("beta_at_unique","z","d","i","x1","1"), "exact hv", "exact ht", "rewrite hone at ha_witness", "rewrite hone at ha_witness", "exact ha_witness",
             "intro hs", *_call("hcompose","i","j","1"), "exact hi", "exact hk_witness_left", "exact hs"),
            "The constructed value-level composition has exact two-way modular-set pullback membership.",
        ),
        spec(
            "finite_modular_set_pullback_exists",
            f"forall b c p n t. ~(p=0) -> ({_count('b','c','p','n')}) -> exists z d. ({_count('z','d','p','n')}) /\\ ({_pullback('b','c','z','d','p','t')})",
            ("finite_modular_translation_indices_exists", "finite_beta_composition_exists", "finite_modular_composition_all_bits", "bit_count_exists", "finite_modular_translation_indices_permutation", "beta_sum_permutation_invariant", "finite_modular_composition_pullback"),
            ("intro b", "intro c", "intro p", "intro n", "intro t", "intro hp", "intro hn",
             f"have hindices : exists r s. {_translation_indices('p','t','r','s','p')}", *_call("finite_modular_translation_indices_exists","p","t","p"), "exact hp", "cases hindices", "cases hindices_witness",
             f"have hcompose : exists z d. {_compose('x','x1','b','c','z','d','p')}", *_call("finite_beta_composition_exists","x","x1","b","c","p"), "cases hcompose", "cases hcompose_witness",
             f"have hbits : {_bits('x2','x3','p')}", *_call("finite_modular_composition_all_bits","p","t","x","x1","b","c","x2","x3"), "exact hindices_witness_witness", "exact hcompose_witness_witness", "cases hn", "exact hn_right",
             f"have hm : exists m. {_count('x2','x3','p','m')}", *_call("bit_count_exists","x2","x3","p"), "exact hbits", "cases hm",
             "have he : n=x4", f"have hpermutation : ({bounded_prefix('x','x1','p',tag='fms_pull_bounded')}) /\\ ({injective_prefix('x','x1','p',tag='fms_pull_injective')})",
             *_call("finite_modular_translation_indices_permutation","p","t","x","x1"), "exact hindices_witness_witness", "cases hpermutation", "cases hn", "cases hm_witness",
             *_call("beta_sum_permutation_invariant","p","x","x1","b","c","x2","x3","n","x4"), "exact hpermutation_left", "exact hpermutation_right", "exact hcompose_witness_witness", "exact hn_left", "exact hm_witness_left",
             "exists x2", "exists x3", "split", "rewrite he", "rewrite he", "exact hm_witness",
             *_call("finite_modular_composition_pullback","p","t","x","x1","b","c","x2","x3"), "exact hindices_witness_witness", "exact hcompose_witness_witness"),
            "Construct the genuine modular pullback set and prove its exact cardinality is unchanged by the finite permutation.",
        ),
    )


def _make_modular_set_transport_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    pull_witness = f"exists j. ({_member('b','c','p','j')}) /\\ ({_mod('p','i+t','j')})"
    push_witness = f"exists j. ({_member('b','c','p','j')}) /\\ ({_mod('p','j+t','i')})"
    inverse_pull_witness = f"exists j. ({_member('b','c','p','j')}) /\\ ({_mod('p','i+v','j')})"
    return (
        spec(
            "finite_bit_zero_nonmember",
            f"forall b c i. ({_at('b','c','i','0',tag='fms_zero_not_one')}) -> ~({_at('b','c','i','1',tag='fms_zero_not_one_result')})",
            ("beta_at_unique", "finite_bit_zero_one_conflict"),
            ("intro b", "intro c", "intro i", "intro hz", "intro ho", *_call("finite_bit_zero_one_conflict","0"), "refl",
             *_call("beta_at_unique","b","c","i","0","1"), "exact hz", "exact ho"),
            "A decoded zero bit excludes characteristic membership without any additional decidability assumption.",
        ),
        spec(
            "finite_modular_residue_exists",
            f"forall p a. ~(p=0) -> exists r. ({_lt('r','p')}) /\\ ({_mod('p','a','r')})",
            ("division_remainder_exists", "remainder_decomposition_to_mod_eq", "mul_comm"),
            ("intro p", "intro a", "intro hp",
             f"have hd : exists q r. a=p*q+r /\\ ({_lt('r','p')})", *_call("division_remainder_exists","p","a"), "exact hp",
             "cases hd", "cases hd_witness", "cases hd_witness_witness", "exists x1", "split", "exact hd_witness_witness_right",
             *_call("remainder_decomposition_to_mod_eq","p","a","x","x1"), "trans p*x+x1", "exact hd_witness_witness_left", "congr", *_call("mul_comm","p","x"), "refl"),
            "Every natural has an actual canonical balanced residue at every nonzero modulus.",
        ),
        spec(
            "finite_modular_additive_complement",
            f"forall p a. ({_lt('a','p')}) -> exists d. a+d=p",
            ("add_comm", "add_succ_left"),
            ("intro p", "intro a", "intro ha", "cases ha", "exists S x", "trans x+S a", "simp [add_comm, add_succ_left]", "exact ha_witness"),
            "A canonical residue has a genuine natural additive complement, including the zero boundary.",
        ),
        spec(
            "finite_modular_inverse_shift",
            f"forall p t d a b. t+d=p -> ({_mod('p','a+t','b')}) -> ({_mod('p','b+d','a')})",
            ("add_assoc", "add_comm"),
            ("intro p", "intro t", "intro d", "intro a", "intro b", "intro htd", "intro hmod", "cases hmod", "cases hmod_witness", "exists x1", "exists S x",
             "trans (b+p*x1)+d", "simp [add_assoc, add_comm]", "trans ((a+t)+p*x)+d", "congr", "symm", "exact hmod_witness_witness", "refl",
             "trans (a+(t+d))+p*x", "simp [add_assoc, add_comm]", "rewrite htd", "simp [add_assoc, add_comm]"),
            "Opposite additive shifts invert one another in balanced modular arithmetic by explicit witnesses.",
        ),
        spec(
            "finite_modular_pullback_membership_witness",
            f"forall b c z d p t i. ~(p=0) -> ({_pullback('b','c','z','d','p','t')}) -> ({_lt('i','p')}) -> "
            f"({_iff(_at('z','d','i','1',tag='fms_pull_member'),pull_witness)})",
            ("finite_modular_residue_exists",),
            ("intro b", "intro c", "intro z", "intro d", "intro p", "intro t", "intro i", "intro hp", "intro hpull", "intro hi", "split", "intro ht",
             f"have hj : exists j. ({_lt('j','p')}) /\\ ({_mod('p','i+t','j')})", *_call("finite_modular_residue_exists","p","i+t"), "exact hp", "cases hj", "cases hj_witness",
             f"have he : {_iff(_at('z','d','i','1',tag='fms_pull_t'),_at('b','c','x','1',tag='fms_pull_s'))}", *_call("hpull","i","x"), "exact hi", "exact hj_witness_left", "exact hj_witness_right", "cases he",
             "exists x", "split", "split", "exact hj_witness_left", "apply he_left", "exact ht", "exact hj_witness_right",
             "intro hw", "cases hw", "cases hw_witness", "cases hw_witness_left",
             f"have he : {_iff(_at('z','d','i','1',tag='fms_pull_back_t'),_at('b','c','x','1',tag='fms_pull_back_s'))}", *_call("hpull","i","x"), "exact hi", "exact hw_witness_left_left", "exact hw_witness_right", "cases he", "apply he_right", "exact hw_witness_left_right"),
            "Exact pullback membership constructs and reflects an actual canonical source member.",
        ),
        spec(
            "finite_modular_pushforward_membership_witness",
            f"forall b c z d p t v i. ~(p=0) -> t+v=p -> ({_pullback('b','c','z','d','p','v')}) -> ({_lt('i','p')}) -> "
            f"({_iff(_at('z','d','i','1',tag='fms_push_member'),push_witness)})",
            ("finite_modular_pullback_membership_witness", "finite_modular_inverse_shift", "add_comm"),
            ("intro b", "intro c", "intro z", "intro d", "intro p", "intro t", "intro v", "intro i", "intro hp", "intro htv", "intro hpull", "intro hi",
             f"have he : {_iff(_at('z','d','i','1',tag='fms_push_t'),inverse_pull_witness)}",
             *_call("finite_modular_pullback_membership_witness","b","c","z","d","p","v","i"), "exact hp", "exact hpull", "exact hi", "cases he", "split", "intro ht",
             f"have hw : exists j. ({_member('b','c','p','j')}) /\\ ({_mod('p','i+v','j')})", "apply he_left", "exact ht", "cases hw", "cases hw_witness",
             "exists x", "split", "exact hw_witness_left", *_call("finite_modular_inverse_shift","p","v","t","i","x"), "trans t+v", *_call("add_comm","v","t"), "exact htv", "exact hw_witness_right",
             "intro hw", "cases hw", "cases hw_witness", "apply he_right", "exists x", "split", "exact hw_witness_left", *_call("finite_modular_inverse_shift","p","t","v","x","i"), "exact htv", "exact hw_witness_right"),
            "A coded inverse pullback is exactly the forward translate, with actual source-member witnesses.",
        ),
        spec(
            "finite_modular_shifted_sum_congruence",
            f"forall p a b x y t. ({_mod('p','a+t','x')}) -> ({_mod('p','y+t','b')}) -> ({_mod('p','a+b','x+y')})",
            ("mod_eq_add", "mod_eq_refl", "mod_eq_symm", "mod_eq_trans", "add_assoc", "add_comm"),
            ("intro p", "intro a", "intro b", "intro x", "intro y", "intro t", "intro ha", "intro hb",
             *_call("mod_eq_trans","p","a+b","a+(y+t)","x+y"), *_call("mod_eq_add","p","a","a","b","y+t"), *_call("mod_eq_refl","p","a"), *_call("mod_eq_symm","p","y+t","b"), "exact hb",
             "have he : a+(y+t)=(a+t)+y", "trans a+(t+y)", "congr", "refl", *_call("add_comm","y","t"), "symm", *_call("add_assoc","a","t","y"),
             "rewrite he", *_call("mod_eq_add","p","a+t","x","y","y"), "exact ha", *_call("mod_eq_refl","p","y")),
            "Moving a common shift between two summands preserves their exact modular sum.",
        ),
    )


def _make_sumset_prefix_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "finite_beta_zero_code", f"forall i. {_at('0','0','i','0',tag='fms_zero_code')}", (),
            ("intro i", "split", "exists 0", "simp", "exists 0", "simp"),
            "The literal beta code (0,0) decodes zero at every natural index.",
        ),
        spec(
            "finite_bit_empty_count",
            f"forall p. {_count('0','0','p','0')}",
            ("finite_beta_zero_code",),
            ("intro p", "split", "exists 0", "exists 0", "split", *_call("finite_beta_zero_code","0"), "split", *_call("finite_beta_zero_code","p"),
             "intro i", "intro hi", "exists 0", "exists 0", "exists 0", "split", *_call("finite_beta_zero_code","i"), "split", *_call("finite_beta_zero_code","i"), "split", *_call("finite_beta_zero_code","S i"), "simp",
             "intro i", "intro hi", "exists 0", "split", *_call("finite_beta_zero_code","i"), "left", "refl"),
            "The literal zero code is an actual empty characteristic set with an exact zero sum trace at every ambient size.",
        ),
        spec(
            "finite_partial_sumset_empty",
            f"forall b c d e p. {_partial_sumset('b','c','d','e','0','0','p','0')}",
            ("finite_beta_zero_code", "finite_bit_zero_nonmember", "add_eq_zero_right", "succ_ne_zero"),
            ("intro b", "intro c", "intro d", "intro e", "intro p", "intro z", "intro hz", "split", "intro hmember", "exfalso",
             *_call("finite_bit_zero_nonmember","0","0","z"), *_call("finite_beta_zero_code","z"), "exact hmember",
             "intro hw", "cases hw", "cases hw_witness", "cases hw_witness_witness", "cases hw_witness_witness_right", "cases hw_witness_witness_right_right",
             "cases hw_witness_witness_right_right_left", "exfalso", "have hzero : S x1=0", *_call("add_eq_zero_right","x2","S x1"), "exact hw_witness_witness_right_right_left_witness",
             *_call("succ_ne_zero","x1"), "exact hzero"),
            "The actual empty code is exactly the sumset restricted to the empty second-coordinate prefix.",
        ),
        spec(
            "finite_partial_sumset_succ_absent",
            f"forall b c d e u v p l. ({_partial_sumset('b','c','d','e','u','v','p','l')}) -> "
            f"~({_at('d','e','l','1',tag='fms_absent')}) -> ({_partial_sumset('b','c','d','e','u','v','p','S l')})",
            ("finite_lt_succ_eq_or_lt", "le_succ"),
            ("intro b", "intro c", "intro d", "intro e", "intro u", "intro v", "intro p", "intro l", "intro hprefix", "intro habsent", "intro z", "intro hz",
             f"have he : {_iff(_at('u','v','z','1',tag='fms_absent_old'),_partial_sums('b','c','d','e','p','l','z'))}", *_call("hprefix","z"), "exact hz", "cases he", "split", "intro hs",
             f"have hw : {_partial_sums('b','c','d','e','p','l','z')}", "apply he_left", "exact hs",
             "cases hw", "cases hw_witness", "cases hw_witness_witness", "cases hw_witness_witness_right", "cases hw_witness_witness_right_right",
             "exists x", "exists x1", "split", "exact hw_witness_witness_left", "split", "exact hw_witness_witness_right_left", "split", *_call("le_succ","S x1","l"), "exact hw_witness_witness_right_right_left", "exact hw_witness_witness_right_right_right",
             "intro hw", "cases hw", "cases hw_witness", "cases hw_witness_witness", "cases hw_witness_witness_right", "cases hw_witness_witness_right_right",
             f"have hcase : x1=l \\/ ({_lt('x1','l')})", *_call("finite_lt_succ_eq_or_lt","l","x1"), "exact hw_witness_witness_right_right_left", "cases hcase",
             "cases hw_witness_witness_right_left", "exfalso", "apply habsent", "rewrite hcase_left at hw_witness_witness_right_left_right", "rewrite hcase_left at hw_witness_witness_right_left_right", "exact hw_witness_witness_right_left_right",
             "apply he_right", "exists x", "exists x1", "split", "exact hw_witness_witness_left", "split", "exact hw_witness_witness_right_left", "split", "exact hcase_right", "exact hw_witness_witness_right_right_right"),
            "Skipping an actually absent second-coordinate bit preserves the exact partial sumset.",
        ),
    )


def _make_sumset_existence_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    translated_member = f"exists a. ({_member('b','c','p','a')}) /\\ ({_mod('p','a+l','z')})"
    union_member = f"({_at('ub','uc','z','1',tag='fms_present_old')}) \\/ ({_at('tb','tc','z','1',tag='fms_present_translate')})"
    full_witness = f"exists a v. ({_member('b','c','p','a')}) /\\ (({_member('d','e','p','v')}) /\\ ({_mod('p','a+v','z')}))"
    return (
        spec(
            "finite_partial_sumset_succ_present",
            f"forall b c d e ub uc tb tc zb zc p l v. ~(p=0) -> ({_lt('l','p')}) -> l+v=p -> "
            f"({_at('d','e','l','1',tag='fms_present_bit')}) -> ({_partial_sumset('b','c','d','e','ub','uc','p','l')}) -> "
            f"({_pullback('b','c','tb','tc','p','v')}) -> ({_binary('ub','uc','tb','tc','zb','zc','p',_OR)}) -> "
            f"({_partial_sumset('b','c','d','e','zb','zc','p','S l')})",
            ("finite_modular_pushforward_membership_witness", "finite_lt_succ_eq_or_lt", "le_succ", "le_refl"),
            ("intro b", "intro c", "intro d", "intro e", "intro ub", "intro uc", "intro tb", "intro tc", "intro zb", "intro zc", "intro p", "intro l", "intro v",
             "intro hp", "intro hl", "intro hlv", "intro hB", "intro hprefix", "intro hpull", "intro hunion", "intro z", "intro hz",
             f"have hpre : {_iff(_at('ub','uc','z','1',tag='fms_present_old_iff'),_partial_sums('b','c','d','e','p','l','z'))}", *_call("hprefix","z"), "exact hz", "cases hpre",
             f"have hshift : {_iff(_at('tb','tc','z','1',tag='fms_present_shift_iff'),translated_member)}", *_call("finite_modular_pushforward_membership_witness","b","c","tb","tc","p","l","v","z"), "exact hp", "exact hlv", "exact hpull", "exact hz", "cases hshift",
             f"have hun : {_iff(_at('zb','zc','z','1',tag='fms_present_new_iff'),union_member)}", *_call("hunion","z"), "exact hz", "cases hun", "split", "intro hnew",
             f"have hc : {union_member}", "apply hun_left", "exact hnew", "cases hc",
             f"have hw : {_partial_sums('b','c','d','e','p','l','z')}", "apply hpre_left", "exact hc_left", "cases hw", "cases hw_witness", "cases hw_witness_witness", "cases hw_witness_witness_right", "cases hw_witness_witness_right_right",
             "exists x", "exists x1", "split", "exact hw_witness_witness_left", "split", "exact hw_witness_witness_right_left", "split", *_call("le_succ","S x1","l"), "exact hw_witness_witness_right_right_left", "exact hw_witness_witness_right_right_right",
             f"have hw : {translated_member}", "apply hshift_left", "exact hc_right", "cases hw", "cases hw_witness", "exists x", "exists l", "split", "exact hw_witness_left", "split", "split", "exact hl", "exact hB", "split", *_call("le_refl","S l"), "exact hw_witness_right",
             "intro hw", "cases hw", "cases hw_witness", "cases hw_witness_witness", "cases hw_witness_witness_right", "cases hw_witness_witness_right_right",
             f"have hcase : x1=l \\/ ({_lt('x1','l')})", *_call("finite_lt_succ_eq_or_lt","l","x1"), "exact hw_witness_witness_right_right_left", "cases hcase",
             "apply hun_right", "right", "apply hshift_right", "exists x", "split", "exact hw_witness_witness_left", "rewrite hcase_left at hw_witness_witness_right_right_right", "exact hw_witness_witness_right_right_right",
             "apply hun_right", "left", "apply hpre_right", "exists x", "exists x1", "split", "exact hw_witness_witness_left", "split", "exact hw_witness_witness_right_left", "split", "exact hcase_right", "exact hw_witness_witness_right_right_right"),
            "Adjoining the actual translated first set at a present second-coordinate bit gives the exact next partial sumset.",
        ),
        spec(
            "finite_modular_sumset_prefix_exists",
            f"forall b c d e p n l. ~(p=0) -> ({_count('b','c','p','n')}) -> ({_bits('d','e','p')}) -> ({_le('l','p')}) -> "
            f"exists u v m. ({_count('u','v','p','m')}) /\\ ({_partial_sumset('b','c','d','e','u','v','p','l')})",
            ("finite_bit_empty_count", "finite_partial_sumset_empty", "le_trans", "le_succ_self", "finite_bit_membership_decidable", "finite_modular_additive_complement", "finite_modular_set_pullback_exists", "finite_bit_union_exists", "finite_partial_sumset_succ_present", "finite_partial_sumset_succ_absent"),
            ("intro b", "intro c", "intro d", "intro e", "intro p", "intro n", "induction l",
             "intro hp", "intro hA", "intro hbitsB", "intro hl", "exists 0", "exists 0", "exists 0", "split", *_call("finite_bit_empty_count","p"), *_call("finite_partial_sumset_empty","b","c","d","e","p"),
             "intro hp", "intro hA", "intro hbitsB", "intro hbound",
             f"have hprefix : exists u v m. ({_count('u','v','p','m')}) /\\ ({_partial_sumset('b','c','d','e','u','v','p','l')})",
             "apply IH", "exact hp", "exact hA", "exact hbitsB", *_call("le_trans","l","S l","p"), *_call("le_succ_self","l"), "exact hbound",
             "cases hprefix", "cases hprefix_witness", "cases hprefix_witness_witness", "cases hprefix_witness_witness_witness",
             f"have hdec : ({_at('d','e','l','1',tag='fms_sumset_last')}) \\/ ~({_at('d','e','l','1',tag='fms_sumset_last')})",
             *_call("finite_bit_membership_decidable","d","e","p","l"), "exact hbitsB", "exact hbound", "cases hdec",
             "have hd : exists v. l+v=p", *_call("finite_modular_additive_complement","p","l"), "exact hbound", "cases hd",
             f"have htranslate : exists u v. ({_count('u','v','p','n')}) /\\ ({_pullback('b','c','u','v','p','x3')})",
             *_call("finite_modular_set_pullback_exists","b","c","p","n","x3"), "exact hp", "exact hA", "cases htranslate", "cases htranslate_witness", "cases htranslate_witness_witness",
             f"have hunion : exists u v m. ({_count('u','v','p','m')}) /\\ ({_binary('x','x1','x4','x5','u','v','p',_OR)})",
             *_call("finite_bit_union_exists","x","x1","x4","x5","p","x2","n"), "exact hprefix_witness_witness_witness_left", "exact htranslate_witness_witness_left",
             "cases hunion", "cases hunion_witness", "cases hunion_witness_witness", "cases hunion_witness_witness_witness",
             "exists x6", "exists x7", "exists x8", "split", "exact hunion_witness_witness_witness_left",
             *_call("finite_partial_sumset_succ_present","b","c","d","e","x","x1","x4","x5","x6","x7","p","l","x3"),
             "exact hp", "exact hbound", "exact hd_witness", "exact hdec_left", "exact hprefix_witness_witness_witness_right", "exact htranslate_witness_witness_right", "exact hunion_witness_witness_witness_right",
             "exists x", "exists x1", "exists x2", "split", "exact hprefix_witness_witness_witness_left", *_call("finite_partial_sumset_succ_absent","b","c","d","e","x","x1","p","l"), "exact hprefix_witness_witness_witness_right", "exact hdec_right"),
            "Genuine finite induction constructs every bounded prefix of the exact modular sumset, including all beta codes and cardinality traces.",
        ),
        spec(
            "finite_modular_sumset_exists",
            f"forall b c d e p n m. ~(p=0) -> ({_count('b','c','p','n')}) -> ({_count('d','e','p','m')}) -> "
            f"exists u v q. ({_count('u','v','p','q')}) /\\ ({_sumset('b','c','d','e','u','v','p')})",
            ("finite_modular_sumset_prefix_exists", "le_refl"),
            ("intro b", "intro c", "intro d", "intro e", "intro p", "intro n", "intro m", "intro hp", "intro hA", "intro hB",
             f"have hprefix : exists u v q. ({_count('u','v','p','q')}) /\\ ({_partial_sumset('b','c','d','e','u','v','p','p')})",
             *_call("finite_modular_sumset_prefix_exists","b","c","d","e","p","n","p"), "exact hp", "exact hA", "cases hB", "exact hB_right", *_call("le_refl","p"),
             "cases hprefix", "cases hprefix_witness", "cases hprefix_witness_witness", "cases hprefix_witness_witness_witness",
             "exists x", "exists x1", "exists x2", "split", "exact hprefix_witness_witness_witness_left", "intro z", "intro hz",
             f"have he : {_iff(_at('x','x1','z','1',tag='fms_sumset_final'),_partial_sums('b','c','d','e','p','p','z'))}", *_call("hprefix_witness_witness_witness_right","z"), "exact hz", "cases he", "split", "intro hs",
             f"have hw : {_partial_sums('b','c','d','e','p','p','z')}", "apply he_left", "exact hs", "cases hw", "cases hw_witness", "cases hw_witness_witness", "cases hw_witness_witness_right", "cases hw_witness_witness_right_right",
             "exists x3", "exists x4", "split", "exact hw_witness_witness_left", "split", "exact hw_witness_witness_right_left", "exact hw_witness_witness_right_right_right",
             "intro hw", "cases hw", "cases hw_witness", "cases hw_witness_witness", "cases hw_witness_witness_right", "apply he_right", "exists x3", "exists x4", "split", "exact hw_witness_witness_left", "split", "exact hw_witness_witness_right_left", "split",
             "cases hw_witness_witness_right_left", "exact hw_witness_witness_right_left_left", "exact hw_witness_witness_right_right"),
            "Every pair of actual finite modular sets has an actual canonical sumset code with a witnessed exact cardinality.",
        ),
        spec(
            "finite_modular_sumset_cover",
            f"forall b c d e u v p. ({_sumset('b','c','d','e','u','v','p')}) -> ({_cover('b','c','d','e','u','v','p')})",
            (),
            ("intro b", "intro c", "intro d", "intro e", "intro u", "intro v", "intro p", "intro hsum", "intro a", "intro w", "intro z", "intro ha", "intro hw", "intro hz", "intro hA", "intro hB", "intro hmod",
             f"have he : {_iff(_at('u','v','z','1',tag='fms_sumset_cover'),full_witness)}", *_call("hsum","z"), "exact hz", "cases he", "apply he_right",
             "exists a", "exists w", "split", "split", "exact ha", "exact hA", "split", "split", "exact hw", "exact hB", "exact hmod"),
            "An exact actual sumset contains each witnessed canonical sum of input members.",
        ),
    )


__all__ = [
    "FiniteModularSetError", "finite_modular_set_relation", "modular_set_member_relation",
    "modular_set_subset_relation", "modular_set_union_relation", "modular_set_intersection_relation",
    "modular_set_pullback_relation", "modular_set_sum_cover_relation", "modular_set_sum_relation",
    "make_finite_modular_set_candidate_theorems",
]
