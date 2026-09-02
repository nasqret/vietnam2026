"""Actual finite beta-coded tables for canonical prime-field arithmetic.

Binary tables use the explicit row-major index a*p+b and all p*p entries;
unary tables use all p entries.  The inverse table records zero at zero as a
convention, never as a multiplicative inverse.  Pointwise choice is proved by
ordinary finite induction and actual beta-prefix extension before it is
instantiated with the proved operation constructors.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .finite_fold_surface import _beta_at_term
from .prime_field_arithmetic_candidate import (
    _add, _and, _call, _intro, _inv, _lt, _mul, _neg, _part, _parts,
    _prime, _public,
)


KINDS = ("add", "multiply", "negate", "inverse")


def _at(b: str, c: str, i: str, value: str, tag: str) -> str:
    return _beta_at_term(b, c, i, value, tag="pft_" + tag, avoid=())


def _zero_inverse(p: str, a: str, b: str, tag: str) -> str:
    return _and(_lt(a, p, tag + "input"), _lt(b, p, tag + "output"),
                f"(({a}) = 0 /\\ ({b}) = 0) \\/ ({_inv(p,a,b,tag+'nonzero')})")


def _grid_value(kind: str, p: str, i: str, value: str, tag: str) -> str:
    a, b = f"pft_row_{tag}", f"pft_column_{tag}"
    graph = _add if kind == "add" else _mul
    return f"exists {a} {b}. " + _and(f"({i}) = {a} * ({p}) + {b}", graph(p, a, b, value, tag + "operation"))


def _value(kind: str, p: str, i: str, value: str, tag: str) -> str:
    if kind in ("add", "multiply"):
        return _grid_value(kind, p, i, value, tag)
    if kind == "negate":
        return _neg(p, i, value, tag)
    if kind == "inverse":
        return _zero_inverse(p, i, value, tag)
    raise ValueError("unknown prime-field table kind")


def _entry(kind: str, p: str, b: str, c: str, i: str, value: str, tag: str) -> str:
    return _and(_at(b, c, i, value, tag + "entry"), _value(kind, p, i, value, tag + "value"))


def _prefix(kind: str, p: str, b: str, c: str, length: str, tag: str) -> str:
    i, value = f"pft_index_{tag}", f"pft_value_{tag}"
    return f"forall {i}. ({_lt(i,length,tag+'prefix')}) -> exists {value}. ({_entry(kind,p,b,c,i,value,tag+'point')})"


def _length(kind: str, p: str) -> str:
    return f"({p}) * ({p})" if kind in ("add", "multiply") else p


def _table(kind: str, p: str, b: str, c: str, tag: str) -> str:
    return _prefix(kind, p, b, c, _length(kind, p), tag)


def _tables(p: str, ab: str, ac: str, mb: str, mc: str, nb: str, nc: str, ib: str, ic: str, tag: str) -> str:
    return _and(_table("add", p, ab, ac, tag + "add"), _table("multiply", p, mb, mc, tag + "multiply"),
                _table("negate", p, nb, nc, tag + "negate"), _table("inverse", p, ib, ic, tag + "inverse"))


def prime_field_zero_extended_inverse_relation(p: str, a: str, b: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Inverse on nonzero elements; the explicit table convention 0 maps to 0."""
    return _public(_zero_inverse, (p, a, b), tag=tag, variables=variables)


def prime_field_add_grid_value_relation(p: str, i: str, value: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(lambda p,i,value,tag: _grid_value("add",p,i,value,tag), (p,i,value), tag=tag, variables=variables)


def prime_field_multiply_grid_value_relation(p: str, i: str, value: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(lambda p,i,value,tag: _grid_value("multiply",p,i,value,tag), (p,i,value), tag=tag, variables=variables)


def prime_field_add_prefix_relation(p: str, b: str, c: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(lambda p,b,c,length,tag: _prefix("add",p,b,c,length,tag), (p,b,c,length), tag=tag, variables=variables)


def prime_field_multiply_prefix_relation(p: str, b: str, c: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(lambda p,b,c,length,tag: _prefix("multiply",p,b,c,length,tag), (p,b,c,length), tag=tag, variables=variables)


def prime_field_negate_prefix_relation(p: str, b: str, c: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(lambda p,b,c,length,tag: _prefix("negate",p,b,c,length,tag), (p,b,c,length), tag=tag, variables=variables)


def prime_field_inverse_prefix_relation(p: str, b: str, c: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(lambda p,b,c,length,tag: _prefix("inverse",p,b,c,length,tag), (p,b,c,length), tag=tag, variables=variables)


def prime_field_operation_tables_relation(p: str, ab: str, ac: str, mb: str, mc: str, nb: str, nc: str, ib: str, ic: str,
                                         *, tag: str, variables: tuple[str, ...]) -> str:
    """Four actual beta codes, with p*p binary entries and p unary entries."""
    return _public(_tables, (p,ab,ac,mb,mc,nb,nc,ib,ic), tag=tag, variables=variables)


def _rewrite_all(equality: str, formula: str, variable: str, at: str | None = None) -> tuple[str, ...]:
    return (f"rewrite {equality}" + (f" at {at}" if at else ""),) * len(re.findall(r"\b" + re.escape(variable) + r"\b", formula))


def _grid_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    result = []
    for kind, graph in (("add", _add), ("multiply", _mul)):
        body = _intro("p", "i", "hp", "hi")
        body += (f"have hd : exists a b. i = p * a + b /\\ ({_lt('b','p',kind+'grid_division')})",)
        body += _call("division_remainder_exists", "p", "i") + ("intro hz",)
        body += _call("prime_nonzero", "p") + ("exact hp", "exact hz", "cases hd", "cases hd_witness", "cases hd_witness_witness")
        body += (f"have hx : {_lt('x','p',kind+'grid_row')}",)
        body += _call("matrix_recursive_quotient_row_bound", "p", "i", "x", "x1")
        body += ("exact hd_witness_witness_left", "exact hi")
        body += (f"have hv : exists v. ({graph('p','x','x1','v',kind+'grid_operation')})",)
        body += _call("prime_field_" + kind + "_exists", "p", "x", "x1")
        body += ("exact hp", "exact hx", "exact hd_witness_witness_right", "cases hv", "exists x2", "exists x", "exists x1", "split",
                 "specialize mul_comm p", "specialize mul_comm x", "rewrite mul_comm at hd_witness_witness_left", "exact hd_witness_witness_left", "exact hv_witness")
        result.append(spec(
            "prime_field_" + kind + "_grid_value_exists",
            f"forall p i. ({_prime('p',kind+'grid_domain')}) -> ({_lt('i','p*p',kind+'grid_bound')}) -> exists v. ({_grid_value(kind,'p','i','v',kind+'grid_result')})",
            ("division_remainder_exists", "prime_nonzero", "matrix_recursive_quotient_row_bound", "prime_field_" + kind + "_exists", "mul_comm"),
            body, f"Construct the actual bounded {kind} value at every one of the p*p row-major indices.",
        ))
    result.append(spec(
        "prime_field_zero_extended_inverse_exists",
        f"forall p a. ({_prime('p','zero_extended_domain')}) -> ({_lt('a','p','zero_extended_bound')}) -> exists b. ({_zero_inverse('p','a','b','zero_extended_result')})",
        ("eq_decidable", "prime_field_zero_below_prime", "prime_field_inverse_exists"),
        _intro("p", "a", "hp", "ha") + ("have hcases : a = 0 \\/ ~(a = 0)",)
        + _call("eq_decidable", "a", "0") + ("cases hcases", "exists 0", "split", "exact ha", "split")
        + _call("prime_field_zero_below_prime", "p") + ("exact hp", "left", "split", "exact hcases_left", "refl")
        + (f"have hi : exists b. ({_inv('p','a','b','zero_extended_inverse')})",)
        + _call("prime_field_inverse_exists", "p", "a") + ("exact hp", "exact ha", "exact hcases_right", "cases hi", "exists x", "split", "exact ha", "split")
        + _parts("hi_witness", 4) + ("exact hi_witness_right_right_left", "right", "exact hi_witness"),
        "Totalize only the inverse table by recording zero at zero; the nonzero branch constructs a genuine inverse.",
    ))
    result.append(spec(
        "prime_field_zero_extended_inverse_functional",
        f"forall p a b c. ({_zero_inverse('p','a','b','zero_inverse_first')}) -> ({_zero_inverse('p','a','c','zero_inverse_second')}) -> b = c",
        ("prime_field_inverse_functional",),
        _intro("p", "a", "b", "c", "hb", "hc") + _parts("hb", 3) + _parts("hc", 3)
        + ("cases hb_right_right", "cases hb_right_right_left", "cases hc_right_right", "cases hc_right_right_left",
           "trans 0", "exact hb_right_right_left_right", "symm", "exact hc_right_right_left_right",
           "exfalso", "cases hc_right_right_right", "apply hc_right_right_right_left", "exact hb_right_right_left_left",
           "cases hc_right_right", "cases hc_right_right_left", "exfalso", "cases hb_right_right_right", "apply hb_right_right_right_left", "exact hc_right_right_left_left")
        + _call("prime_field_inverse_functional", "p", "a", "b", "c") + ("exact hb_right_right_right", "exact hc_right_right_right"),
        "The explicit zero convention and genuine nonzero inverses together define a functional total table operation.",
    ))
    return tuple(result)


def _choice_row(spec: Callable[..., Any], kind: str) -> Any:
    total = f"forall i. ({_lt('i','l',kind+'choice_domain')}) -> exists v. ({_value(kind,'p','i','v',kind+'choice_value')})"
    goal = f"exists b c. ({_prefix(kind,'p','b','c','l',kind+'choice_result')})"
    body = _intro("p", "l") + ("induction l", "intro htotal", "exists 0", "exists 0")
    body += _intro("i", "hi") + ("exfalso",) + _call("lt_not_le", "i", "0") + ("exact hi",) + _call("zero_le", "i")
    body += ("intro htotal", f"have hprev : exists b c. ({_prefix(kind,'p','b','c','l',kind+'choice_previous')})", "apply IH")
    body += _intro("i", "hi") + _call("htotal", "i") + _call("le_succ", "S i", "l") + ("exact hi", "cases hprev", "cases hprev_witness")
    body += (f"have hv : exists v. ({_value(kind,'p','l','v',kind+'choice_last_value')})",)
    body += _call("htotal", "l") + ("exists 0", "apply zero_add", "cases hv")
    preserve = (f"forall i v. ({_lt('i','l',kind+'choice_preserve_bound')}) -> "
                f"({_at('x','x1','i','v',kind+'choice_old')}) -> ({_at('b','c','i','v',kind+'choice_new')})")
    body += (f"have hext : exists b c. ({_at('b','c','l','x2',kind+'choice_last_entry')}) /\\ ({preserve})",)
    body += _call("beta_prefix_extend", "l", "x", "x1", "x2")
    body += ("cases hext", "cases hext_witness", "cases hext_witness_witness", "exists x3", "exists x4")
    body += _intro("i", "hi")
    body += (f"have hcases : i = l \\/ ({_lt('i','l',kind+'choice_cases')})",)
    body += _call("finite_lt_succ_eq_or_lt", "l", "i") + ("exact hi", "cases hcases")
    body += _rewrite_all("hcases_left", _entry(kind,"p","x3","x4","i","v",kind+'count'), "i")
    body += ("exists x2", "split", "exact hext_witness_witness_left", "exact hv_witness")
    body += (f"have hold : exists v. ({_entry(kind,'p','x','x1','i','v',kind+'choice_old_entry')})",)
    body += _call("hprev_witness_witness", "i") + ("exact hcases_right", "cases hold", "cases hold_witness", "exists x5", "split")
    body += _call("hext_witness_witness_right", "i", "x5") + ("exact hcases_right", "exact hold_witness_left", "exact hold_witness_right")
    return spec(
        "prime_field_" + kind + "_prefix_choice",
        f"forall p l. ({total}) -> ({goal})",
        ("lt_not_le", "zero_le", "le_succ", "zero_add", "beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
        body,
        f"Ordinary finite induction codes actual pointwise {kind} witnesses; no choice axiom or unproved field law is introduced.",
    )


def _table_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    result = []
    for kind in KINDS:
        constructor = ("prime_field_" + kind + "_grid_value_exists" if kind in ("add", "multiply")
                       else "prime_field_negate_exists" if kind == "negate" else "prime_field_zero_extended_inverse_exists")
        body = _intro("p", "hp") + _call("prime_field_" + kind + "_prefix_choice", "p", _length(kind,"p"))
        body += _intro("i", "hi") + _call(constructor, "p", "i") + ("exact hp", "exact hi")
        result.append(spec(
            "prime_field_" + kind + "_table_exists",
            f"forall p. ({_prime('p',kind+'table_domain')}) -> exists b c. ({_table(kind,'p','b','c',kind+'table_result')})",
            ("prime_field_" + kind + "_prefix_choice", constructor), body,
            f"Construct every entry of the finite {kind} table from primality alone.",
        ))
    body = _intro("p", "hp")
    for kind in KINDS:
        body += (f"have h{kind} : exists b c. ({_table(kind,'p','b','c',kind+'all_tables')})",)
        body += _call("prime_field_" + kind + "_table_exists", "p") + ("exact hp", f"cases h{kind}", f"cases h{kind}_witness")
    body += tuple(f"exists x{i}" if i else "exists x" for i in range(8))
    for index, kind in enumerate(KINDS):
        if index < 3:
            body += ("split",)
        body += (f"exact h{kind}_witness_witness",)
    result.append(spec(
        "prime_field_operation_tables_exists",
        f"forall p. ({_prime('p','all_tables_domain')}) -> exists ab ac mb mc nb nc ib ic. ({_tables('p','ab','ac','mb','mc','nb','nc','ib','ic','all_tables')})",
        tuple("prime_field_" + kind + "_table_exists" for kind in KINDS), body,
        "Every prime has four actual finite beta-coded arithmetic tables; zero is only a totalized inverse-table convention.",
    ))
    return tuple(result)


def _lookup_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    result = []
    for kind, graph in (("add", _add), ("multiply", _mul)):
        body = _intro("p", "a", "b", "v", "hb", "hg")
        body += ("cases hg", "cases hg_witness", "cases hg_witness_witness")
        body += _parts("hg_witness_witness_right", 4)
        body += ("have heq : x = a /\\ x1 = b",)
        body += _call("division_remainder_unique", "p", "a * p + b", "x", "x1", "a", "b")
        body += ("specialize mul_comm x", "specialize mul_comm p", "rewrite mul_comm at hg_witness_witness_left", "exact hg_witness_witness_left",
                 "exact hg_witness_witness_right_right_left", "specialize mul_comm a", "specialize mul_comm p", "rewrite mul_comm", "refl", "exact hb", "cases heq")
        body += _rewrite_all("heq_left", graph("p","x","x1","v",kind+'rowtransport'), "x", "hg_witness_witness_right")
        body += _rewrite_all("heq_right", graph("p","a","x1","v",kind+'columntransport'), "x1", "hg_witness_witness_right")
        body += ("exact hg_witness_witness_right",)
        result.append(spec(
            "prime_field_" + kind + "_grid_value_lookup",
            f"forall p a b v. ({_lt('b','p',kind+'lookup_column')}) -> ({_grid_value(kind,'p','a*p+b','v',kind+'lookup_grid')}) -> ({graph('p','a','b','v',kind+'lookup_result')})",
            ("division_remainder_unique", "mul_comm"), body,
            f"Actual quotient/remainder uniqueness identifies both row-major coordinates of a {kind} table entry.",
        ))
        body = _intro("p", "B", "C", "a", "b", "v", "htable", "ha", "hb", "hat")
        body += (f"have hpoint : exists w. ({_entry(kind,'p','B','C','a*p+b','w',kind+'lookup_point')})",)
        body += _call("htable", "a*p+b") + _call("matrix_recursive_flattened_index_bound", "p", "a", "b")
        body += ("exact ha", "exact hb", "cases hpoint", "cases hpoint_witness", "have heq : x = v")
        body += _call("beta_at_unique", "B", "C", "a*p+b", "x", "v") + ("exact hpoint_witness_left", "exact hat")
        body += _rewrite_all("heq", _grid_value(kind,"p","a*p+b","x",kind+'value_transport'), "x", "hpoint_witness_right")
        body += _call("prime_field_" + kind + "_grid_value_lookup", "p", "a", "b", "v")
        body += ("exact hb", "exact hpoint_witness_right")
        result.append(spec(
            "prime_field_" + kind + "_table_lookup",
            f"forall p B C a b v. ({_table(kind,'p','B','C',kind+'lookup_table')}) -> ({_lt('a','p',kind+'lookup_a')}) -> ({_lt('b','p',kind+'lookup_b')}) -> ({_at('B','C','a*p+b','v',kind+'lookup_at')}) -> ({graph('p','a','b','v',kind+'lookup_graph')})",
            ("matrix_recursive_flattened_index_bound", "beta_at_unique", "prime_field_" + kind + "_grid_value_lookup"),
            body, f"Every decoded {kind} table lookup has exactly the proved canonical arithmetic meaning.",
        ))
        body = _intro("p", "B", "C", "a", "b", "v", "htable", "hop")
        body += _parts("hop", 3)
        body += (f"have hat : exists w. ({_at('B','C','a*p+b','w',kind+'reflect_exists')})",)
        body += _call("beta_at_exists", "B", "C", "a*p+b") + ("cases hat",)
        body += (f"have hout : {graph('p','a','b','x',kind+'reflect_lookup')}",)
        body += _call("prime_field_" + kind + "_table_lookup", "p", "B", "C", "a", "b", "x")
        body += ("exact htable", "exact hop_left", "exact hop_right_left", "exact hat_witness", "have heq : x = v")
        body += _call("prime_field_" + kind + "_functional", "p", "a", "b", "x", "v") + ("exact hout", "exact hop")
        body += _rewrite_all("heq", _at("B","C","a*p+b","x",kind+'reflect_transport'), "x", "hat_witness")
        body += ("exact hat_witness",)
        result.append(spec(
            "prime_field_" + kind + "_table_reflect",
            f"forall p B C a b v. ({_table(kind,'p','B','C',kind+'reflect_table')}) -> ({graph('p','a','b','v',kind+'reflect_graph')}) -> ({_at('B','C','a*p+b','v',kind+'reflect_at')})",
            ("beta_at_exists", "prime_field_" + kind + "_table_lookup", "prime_field_" + kind + "_functional"), body,
            f"Every genuine canonical {kind} result occurs at its actual finite table index.",
        ))
    for kind, graph in (("negate", _neg), ("inverse", _zero_inverse)):
        body = _intro("p", "B", "C", "a", "v", "htable", "ha", "hat")
        body += (f"have hpoint : exists w. ({_entry(kind,'p','B','C','a','w',kind+'unary_lookup_point')})",)
        body += _call("htable", "a") + ("exact ha", "cases hpoint", "cases hpoint_witness", "have heq : x = v")
        body += _call("beta_at_unique", "B", "C", "a", "x", "v") + ("exact hpoint_witness_left", "exact hat")
        body += _rewrite_all("heq", graph("p","a","x",kind+'unary_value_transport'), "x", "hpoint_witness_right")
        body += ("exact hpoint_witness_right",)
        result.append(spec(
            "prime_field_" + kind + "_table_lookup",
            f"forall p B C a v. ({_table(kind,'p','B','C',kind+'unary_lookup_table')}) -> ({_lt('a','p',kind+'unary_lookup_bound')}) -> ({_at('B','C','a','v',kind+'unary_lookup_at')}) -> ({graph('p','a','v',kind+'unary_lookup_graph')})",
            ("beta_at_unique",), body,
            f"Every decoded {kind} table lookup has its exact unary meaning, including the inverse-at-zero convention.",
        ))
        functional = "prime_field_negate_functional" if kind == "negate" else "prime_field_zero_extended_inverse_functional"
        body = _intro("p", "B", "C", "a", "v", "htable", "hop") + ("cases hop",)
        body += (f"have hat : exists w. ({_at('B','C','a','w',kind+'unary_reflect_exists')})",)
        body += _call("beta_at_exists", "B", "C", "a") + ("cases hat",)
        body += (f"have hout : {graph('p','a','x',kind+'unary_reflect_lookup')}",)
        body += _call("prime_field_" + kind + "_table_lookup", "p", "B", "C", "a", "x")
        body += ("exact htable", "exact hop_left", "exact hat_witness", "have heq : x = v")
        body += _call(functional, "p", "a", "x", "v") + ("exact hout", "exact hop")
        body += _rewrite_all("heq", _at("B","C","a","x",kind+'unary_reflect_transport'), "x", "hat_witness")
        body += ("exact hat_witness",)
        result.append(spec(
            "prime_field_" + kind + "_table_reflect",
            f"forall p B C a v. ({_table(kind,'p','B','C',kind+'unary_reflect_table')}) -> ({graph('p','a','v',kind+'unary_reflect_graph')}) -> ({_at('B','C','a','v',kind+'unary_reflect_at')})",
            ("beta_at_exists", "prime_field_" + kind + "_table_lookup", functional), body,
            f"Every genuine {kind} value is stored at its actual unary table index.",
        ))
    return tuple(result)


def _table_law_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    result = []
    for kind, graph in (("add", _add), ("multiply", _mul)):
        result.append(spec(
            "prime_field_" + kind + "_table_commutative",
            f"forall p B C a b v. ({_table(kind,'p','B','C',kind+'comm_table')}) -> ({_lt('a','p',kind+'comm_a')}) -> ({_lt('b','p',kind+'comm_b')}) -> ({_at('B','C','a*p+b','v',kind+'comm_source')}) -> ({_at('B','C','b*p+a','v',kind+'comm_target')})",
            ("prime_field_"+kind+"_table_reflect", "prime_field_"+kind+"_commutative", "prime_field_"+kind+"_table_lookup"),
            _intro("p","B","C","a","b","v","htable","ha","hb","hat")
            + _call("prime_field_"+kind+"_table_reflect","p","B","C","b","a","v") + ("exact htable",)
            + _call("prime_field_"+kind+"_commutative","p","a","b","v")
            + _call("prime_field_"+kind+"_table_lookup","p","B","C","a","b","v")
            + ("exact htable","exact ha","exact hb","exact hat"),
            f"The actual finite {kind} table is symmetric under exchanging row and column.",
        ))
        relations = tuple(_at('B','C',i,v,kind+'table_assoc'+str(j)) for j,(i,v) in enumerate((('a*p+b','x'),('x*p+c','u'),('b*p+c','y'),('a*p+y','v'))))
        body = _intro("p","B","C","a","b","c","x","y","u","v","htable","ha","hb","hc","hatfirst","hatleft","hatsecond","hatright")
        for label,aa,bb,rr,ba,bbound,hat in (("hfirst","a","b","x","ha","hb","hatfirst"),
                                             ("hsecond","b","c","y","hb","hc","hatsecond")):
            body += (f"have {label} : {graph('p',aa,bb,rr,kind+label)}",)
            body += _call("prime_field_"+kind+"_table_lookup","p","B","C",aa,bb,rr)
            body += ("exact htable",f"exact {ba}",f"exact {bbound}",f"exact {hat}") + _parts(label,4)
        body += _call("prime_field_"+kind+"_associative","p","a","b","c","x","y","u","v")
        body += ("exact hfirst",)
        body += _call("prime_field_"+kind+"_table_lookup","p","B","C","x","c","u")
        body += ("exact htable","exact hfirst_right_right_left","exact hc","exact hatleft","exact hsecond")
        body += _call("prime_field_"+kind+"_table_lookup","p","B","C","a","y","v")
        body += ("exact htable","exact ha","exact hsecond_right_right_left","exact hatright")
        result.append(spec(
            "prime_field_"+kind+"_table_associative",
            f"forall p B C a b c x y u v. ({_table(kind,'p','B','C',kind+'assoc_table')}) -> ({_lt('a','p',kind+'assoc_a')}) -> ({_lt('b','p',kind+'assoc_b')}) -> ({_lt('c','p',kind+'assoc_c')}) -> " + " -> ".join(f"({r})" for r in relations) + " -> u = v",
            ("prime_field_"+kind+"_table_lookup","prime_field_"+kind+"_associative"), body,
            f"Both parenthesizations of three actual {kind} table lookups agree, with intermediate bounds proved.",
        ))
    result.append(spec(
        "prime_field_inverse_table_zero",
        f"forall p B C. ({_prime('p','inverse_zero_domain')}) -> ({_table('inverse','p','B','C','inverse_zero_table')}) -> ({_at('B','C','0','0','inverse_zero_entry')})",
        ("prime_field_inverse_table_reflect","prime_field_zero_below_prime"),
        _intro("p","B","C","hp","htable") + _call("prime_field_inverse_table_reflect","p","B","C","0","0")
        + ("exact htable",f"have hz : {_lt('0','p','inverse_zero_bound')}")
        + _call("prime_field_zero_below_prime","p") + ("exact hp","split","exact hz","split","exact hz","left","split","refl","refl"),
        "The totalized inverse table really stores zero at zero, without claiming zero has an inverse.",
    ))
    result.append(spec(
        "prime_field_inverse_table_nonzero",
        f"forall p B C a v. ({_table('inverse','p','B','C','inverse_nonzero_table')}) -> ({_lt('a','p','inverse_nonzero_bound')}) -> ~(a = 0) -> ({_at('B','C','a','v','inverse_nonzero_entry')}) -> ({_mul('p','a','v','1','inverse_nonzero_product')})",
        ("prime_field_inverse_table_lookup",),
        _intro("p","B","C","a","v","htable","ha","hn","hat")
        + (f"have hi : {_zero_inverse('p','a','v','inverse_nonzero_value')}",)
        + _call("prime_field_inverse_table_lookup","p","B","C","a","v")
        + ("exact htable","exact ha","exact hat") + _parts("hi",3)
        + ("cases hi_right_right","cases hi_right_right_left","exfalso","apply hn","exact hi_right_right_left_left",
           "cases hi_right_right_right","exact hi_right_right_right_right"),
        "Every nonzero inverse-table entry multiplies its input to the actual one representative.",
    ))
    return tuple(result)


def _table_distributive_row(spec: Callable[...,Any], side: str) -> Any:
    factors = (("a","s"),("a","b"),("a","c")) if side == "left" else (("s","a"),("b","a"),("c","a"))
    entries = (_at('A','D','b*p+c','s',side+'table_distributive_sum'),
               _at('M','E',f'{factors[0][0]}*p+{factors[0][1]}','u',side+'table_distributive_left'),
               _at('M','E',f'{factors[1][0]}*p+{factors[1][1]}','x',side+'table_distributive_first'),
               _at('M','E',f'{factors[2][0]}*p+{factors[2][1]}','y',side+'table_distributive_second'),
               _at('A','D','x*p+y','v',side+'table_distributive_right'))
    body = _intro('p','A','D','M','E','a','b','c','s','x','y','u','v','haddtable','hmultable','ha','hb','hc','hatsum','hatleft','hatfirst','hatsecond','hatright')
    body += (f"have hsum : {_add('p','b','c','s',side+'table_sum_graph')}",)
    body += _call('prime_field_add_table_lookup','p','A','D','b','c','s') + ('exact haddtable','exact hb','exact hc','exact hatsum') + _parts('hsum',4)
    for label,(aa,bb),rr,hat in (('hfirst',factors[1],'x','hatfirst'),('hsecond',factors[2],'y','hatsecond')):
        body += (f"have {label} : {_mul('p',aa,bb,rr,side+label+'graph')}",)
        body += _call('prime_field_multiply_table_lookup','p','M','E',aa,bb,rr)
        body += ('exact hmultable',f'exact h{aa}',f'exact h{bb}',f'exact {hat}') + _parts(label,4)
    body += _call('prime_field_'+side+'_distributive','p','a','b','c','s','x','y','u','v') + ('exact hsum',)
    body += _call('prime_field_multiply_table_lookup','p','M','E',*factors[0],'u') + ('exact hmultable',)
    body += (('exact ha','exact hsum_right_right_left') if side=='left' else ('exact hsum_right_right_left','exact ha'))
    body += ('exact hatleft','exact hfirst','exact hsecond')
    body += _call('prime_field_add_table_lookup','p','A','D','x','y','v')
    body += ('exact haddtable','exact hfirst_right_right_left','exact hsecond_right_right_left','exact hatright')
    return spec(
        'prime_field_'+side+'_table_distributive',
        f"forall p A D M E a b c s x y u v. ({_table('add','p','A','D',side+'table_distributive_add')}) -> ({_table('multiply','p','M','E',side+'table_distributive_mul')}) -> ({_lt('a','p',side+'table_distributive_a')}) -> ({_lt('b','p',side+'table_distributive_b')}) -> ({_lt('c','p',side+'table_distributive_c')}) -> " + ' -> '.join(f'({e})' for e in entries) + ' -> u = v',
        ('prime_field_add_table_lookup','prime_field_multiply_table_lookup','prime_field_'+side+'_distributive'),
        body, f'Actual finite addition and multiplication table entries satisfy {side} distributivity, with all intermediate bounds derived.',
    )


def make_prime_field_tables_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_grid_rows(spec) + tuple(_choice_row(spec, kind) for kind in KINDS) + _table_rows(spec)
            + _lookup_rows(spec) + _table_law_rows(spec)
            + tuple(_table_distributive_row(spec,side) for side in ('left','right')))


__all__ = [
    "prime_field_zero_extended_inverse_relation", "prime_field_add_grid_value_relation",
    "prime_field_multiply_grid_value_relation", "prime_field_add_prefix_relation",
    "prime_field_multiply_prefix_relation", "prime_field_negate_prefix_relation",
    "prime_field_inverse_prefix_relation", "prime_field_operation_tables_relation",
    "make_prime_field_tables_candidate_theorems",
]
