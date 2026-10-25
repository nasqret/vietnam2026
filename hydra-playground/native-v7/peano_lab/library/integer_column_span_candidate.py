"""Constructive integer column spans with actual coded coefficient witnesses.

Signed integers are natural pairs, compared by balanced equality rather than
by their chosen components. Matrix-vector multiplication is the existing
fully coded signed matrix product at output width one, not an opaque solver.
No independence, basis, rank, normal-form, or lattice-index claim is made here.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .finite_fold_surface import _identifier
from .finite_sum_theorems import _at as _beta
from .matrix_coded_product_candidate import (
    _pointwise_add_terms, _product_cell_terms, _product_prefix_terms,
    _signed_matrix_product_terms,
)
from .matrix_dot_product_candidate import dot_product_relation


def _arguments(*values: str) -> tuple[str, ...]:
    result = tuple(_identifier(value, "integer-column-span argument") for value in values)
    if len(set(result)) != len(result):
        raise ValueError("integer-column-span arguments must be distinct")
    if any(value.startswith(("ics_", "ff_", "fs_", "mcp_", "dot_", "fpmp_")) for value in result):
        raise ValueError("generated integer-column-span binder captures an argument")
    return result


def _safe(tag: str) -> str:
    return _identifier(tag, "integer-column-span binder tag")


def _names(tag: str, *roles: str) -> tuple[str, ...]:
    return tuple(f"ics_{role}_{_safe(tag)}" for role in roles)


def _and(*parts: str) -> str:
    return parts[0] if len(parts) == 1 else f"(({parts[0]}) /\\ ({_and(*parts[1:])}))"


def _lt(a: str, b: str, tag: str) -> str:
    (gap,) = _names(tag, "gap")
    return f"exists {gap}. {gap} + S ({a}) = ({b})"


def _at(b: str, c: str, i: str, a: str, tag: str) -> str:
    return _beta(b, c, i, a, tag=f"ics_{_safe(tag)}")


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _call(name: str, *terms: str) -> tuple[str, ...]:
    return (*(f"specialize {name} ({term})" for term in terms), f"apply {name}")


def _cases(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_witness" * i for i in range(count))


def _parts(name: str, count: int) -> tuple[str, ...]:
    return tuple("cases " + name + "_right" * i for i in range(count - 1))


def _part(name: str, count: int, index: int) -> str:
    return name + "_right" * index + ("_left" if index < count - 1 else "")


def _exists(*terms: str) -> tuple[str, ...]:
    return tuple(f"exists {term}" for term in terms)


def _rewrites(equation: str, variable: str, formula: str, *, at: str | None = None) -> tuple[str, ...]:
    count = len(re.findall(rf"(?<![A-Za-z0-9_']){re.escape(variable)}(?![A-Za-z0-9_'])", formula))
    return (f"rewrite {equation}" + (f" at {at}" if at else ""),) * count


def _choose_at(name: str, b: str, c: str, i: str, tag: str) -> tuple[str, ...]:
    return (f"have {name} : exists value. ({_at(b,c,i,'value',tag)})",) + _call("beta_at_exists", b, c, i) + (f"cases {name}",)


def _natural_add(b: str, c: str, d: str, e: str, f: str, g: str, l: str, tag: str) -> str:
    return _pointwise_add_terms(b, c, d, e, f, g, l, tag=f"ics_{tag}")


def _dot(b: str, c: str, d: str, e: str, l: str, n: str, tag: str) -> str:
    return dot_product_relation(b, c, d, e, l, n, tag=f"ics_{tag}")


def _cell(b: str, c: str, d: str, e: str, w: str, i: str, n: str, tag: str) -> str:
    return _product_cell_terms(b, c, d, e, w, "1", i, "0", n, tag=f"ics_{tag}")


def _natural_product(b: str, c: str, d: str, e: str, w: str, f: str, g: str, l: str, tag: str) -> str:
    return _product_prefix_terms(b, c, d, e, w, "1", f, g, l, tag=f"ics_{tag}")


def _raw_product(ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str, w: str, r: str, pb: str, pc: str, nb: str, nc: str, tag: str) -> str:
    return _signed_matrix_product_terms(ab, ac, db, dc, eb, ec, fb, fc, w, "1", r, pb, pc, nb, nc, tag=f"ics_{tag}")


def _pointwise(codes: tuple[str, ...], length: str, equation: Callable[..., str], tag: str) -> str:
    names = _names(tag, "index", *(f"value{k}" for k in range(len(codes) // 2)))
    i, *values = names
    conditions = [_lt(i, length, tag + "_bound")]
    conditions.extend(_at(codes[2*k], codes[2*k+1], i, value, f"{tag}_at{k}") for k, value in enumerate(values))
    return f"forall {' '.join(names)}. " + "".join(f"({condition}) -> " for condition in conditions) + equation(*values)


def _equal(ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str, l: str, tag: str) -> str:
    return _pointwise((ab,ac,db,dc,eb,ec,fb,fc), l, lambda a,b,c,d: f"{a} + {d} = {c} + {b}", tag)


def _zero(ab: str, ac: str, db: str, dc: str, l: str, tag: str) -> str:
    return _pointwise((ab,ac,db,dc), l, lambda a,b: f"{a} = {b}", tag)


def _add(ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str, pb: str, pc: str, nb: str, nc: str, l: str, tag: str) -> str:
    return _pointwise((ab,ac,db,dc,eb,ec,fb,fc,pb,pc,nb,nc), l, lambda a,b,c,d,e,f: f"{e} + ({b} + {d}) = ({a} + {c}) + {f}", tag)


def _matrix_vector(ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str, w: str, r: str, pb: str, pc: str, nb: str, nc: str, tag: str) -> str:
    P,C,N,D = _names(tag, "raw_positive", "raw_positive_scale", "raw_negative", "raw_negative_scale")
    return f"exists {P} {C} {N} {D}. ({_and(_raw_product(ab,ac,db,dc,eb,ec,fb,fc,w,r,P,C,N,D,tag+'_raw'),_equal(P,C,N,D,pb,pc,nb,nc,r,tag+'_equal'))})"


def _span(ab: str, ac: str, db: str, dc: str, w: str, r: str, pb: str, pc: str, nb: str, nc: str, tag: str) -> str:
    E,C,F,D = _names(tag, "coefficient_positive", "coefficient_positive_scale", "coefficient_negative", "coefficient_negative_scale")
    return f"exists {E} {C} {F} {D}. ({_matrix_vector(ab,ac,db,dc,E,C,F,D,w,r,pb,pc,nb,nc,tag+'_image')})"


def integer_vector_equal(ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str, l: str, *, tag: str) -> str:
    """Equality of represented integers at every actual vector coordinate."""
    return _equal(*_arguments(ab,ac,db,dc,eb,ec,fb,fc,l), _safe(tag))


def integer_vector_zero(ab: str, ac: str, db: str, dc: str, l: str, *, tag: str) -> str:
    """Zero integer entries, allowing arbitrary equal positive/negative parts."""
    return _zero(*_arguments(ab,ac,db,dc,l), _safe(tag))


def integer_vector_add(ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str, pb: str, pc: str, nb: str, nc: str, l: str, *, tag: str) -> str:
    """Actual coordinatewise integer addition, independent of pair encoding."""
    return _add(*_arguments(ab,ac,db,dc,eb,ec,fb,fc,pb,pc,nb,nc,l), _safe(tag))


def integer_vector_negate(ab: str, ac: str, db: str, dc: str, pb: str, pc: str, nb: str, nc: str, l: str, *, tag: str) -> str:
    """The target represents the negative vector, not necessarily swapped codes."""
    ab,ac,db,dc,pb,pc,nb,nc,l = _arguments(ab,ac,db,dc,pb,pc,nb,nc,l)
    return _equal(db,dc,ab,ac,pb,pc,nb,nc,l,_safe(tag))


def integer_matrix_vector_product(ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str, w: str, r: str, pb: str, pc: str, nb: str, nc: str, *, tag: str) -> str:
    """An actual signed coded product, modulo integer-pair output equality."""
    return _matrix_vector(*_arguments(ab,ac,db,dc,eb,ec,fb,fc,w,r,pb,pc,nb,nc), _safe(tag))


def integer_column_span(ab: str, ac: str, db: str, dc: str, w: str, r: str, pb: str, pc: str, nb: str, nc: str, *, tag: str) -> str:
    """Generated integer column span with explicit finite coefficient codes."""
    return _span(*_arguments(ab,ac,db,dc,w,r,pb,pc,nb,nc), _safe(tag))


def make_integer_column_span_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Return additive ordinary-kernel authoring rows, without admission."""
    six_codes = ("ab","ac","bb","bc","cb","cc","db","dc","eb","ec","fb","fc")
    alignment = _pointwise(six_codes, "l", lambda a,b,c,d,e,f:f"{e} * {f} = {a} * {b} + {c} * {d}", "dot_alignment")
    first = "hf_witness_witness"
    second = "hg_witness_witness"
    third = "hh_witness_witness"
    cell1,cell2,cell3 = ("hfirst"+"_witness"*4,"hsecond"+"_witness"*4,"hthird"+"_witness"*4)
    entrycell = _product_cell_terms("ab","ac","bb","bc","w","1","x","x1","x2",tag="ics_entry_actual")
    entrycell_zero = _cell("ab","ac","bb","bc","w","x","x2","entry_column_zero")
    entrycell_row = _cell("ab","ac","bb","bc","w","i","x2","entry_row_aligned")
    interchange_codes = ("ab","ac","bb","bc","cb","cc","db","dc","eb","ec","fb","fc","pb","pc","qb","qc","rb","rc")
    matrix = ("ab","ac","db","dc")
    coefficient = ("eb","ec","fb","fc")
    output = ("pb","pc","nb","nc")
    raw_h = "hproduct" + "_witness"*8
    coefficient2 = ("gb","gc","hb","hc")
    coefficient3 = ("ib","ic","jb","jc")
    output2 = ("qb","qc","mb","mc")
    output3 = ("rb","rc","sb","sc")
    signed_add_arguments = (*matrix,*coefficient,*coefficient2,*coefficient3,"w","r",*output,*output2,*output3)
    raw_sources = tuple(name+"_witness"*8 for name in ("hfirst","hsecond","hthird"))
    xnames = tuple(f"x{k}" if k else "x" for k in range(24))
    raw_products = (
        (("ab","ac"),("eb","ec"),("gb","gc"),("ib","ic"),"haddp"),
        (("db","dc"),("fb","fc"),("hb","hc"),("jb","jc"),"haddn"),
        (("ab","ac"),("fb","fc"),("hb","hc"),("jb","jc"),"haddn"),
        (("db","dc"),("eb","ec"),("gb","gc"),("ib","ic"),"haddp"),
    )
    raw_sum_args = (*matrix,*coefficient,*coefficient2,*coefficient3,"w","r",*output,*output2,*output3)
    linear_add_args = (*matrix,*coefficient,*coefficient2,"w","r",*output,*output2,*output3)
    add_constructed = _and(
        _natural_add(*coefficient[:2],*coefficient2[:2],*coefficient3[:2],"w","linear_constructed_p"),
        _natural_add(*coefficient[2:],*coefficient2[2:],*coefficient3[2:],"w","linear_constructed_n"),
        _matrix_vector(*matrix,*coefficient3,"w","r",*output3,"linear_constructed_image"),
    )

    return (
        spec(
            "integer_span_dot_product_pointwise_add",
            f"forall {' '.join(six_codes)} l L M N. ({_dot('ab','ac','bb','bc','l','L','dot_first')}) -> "
            f"({_dot('cb','cc','db','dc','l','M','dot_second')}) -> ({_dot('eb','ec','fb','fc','l','N','dot_third')}) -> ({alignment}) -> L + M = N",
            ("beta_sum_pointwise_add", "beta_at_exists"),
            _intro(*six_codes,"l","L","M","N","hf","hg","hh","hpoint")
            +_cases("hf",2)+(f"cases {first}",)+_cases("hg",2)+(f"cases {second}",)+_cases("hh",2)+(f"cases {third}",)
            +_call("beta_sum_pointwise_add","x","x1","x2","x3","x4","x5","l","L","M","N")
            +(f"exact {first}_right",f"exact {second}_right",f"exact {third}_right")
            +_intro("i","v","w","z","hi","hv","hw","hz")
            +tuple(command for k in range(6) for command in _choose_at(f"ha{k}",six_codes[2*k],six_codes[2*k+1],"i",f"dot_value{k}"))
            +("have heq : x10 * x11 = x6 * x7 + x8 * x9",)
            +_call("hpoint","i","x6","x7","x8","x9","x10","x11")
            +("exact hi",)+tuple(f"exact ha{k}_witness" for k in range(6))
            +("trans x10 * x11",)+_call(f"{third}_left","i","x10","x11","z")+("exact hi","exact ha4_witness","exact ha5_witness","exact hz")
            +("trans x6 * x7 + x8 * x9","exact heq","congr","symm")
            +_call(f"{first}_left","i","x6","x7","v")+("exact hi","exact ha0_witness","exact ha1_witness","exact hv","symm")
            +_call(f"{second}_left","i","x8","x9","w")+("exact hi","exact ha2_witness","exact ha3_witness","exact hw"),
            "Actual finite dot products add whenever their decoded multiplicands satisfy the displayed pointwise distributive equation; checked finite-sum additivity supplies the full arbitrary-length result.",
        ),
        spec(
            "integer_span_natural_cell_add_right",
            "forall ab ac bb bc cb cc db dc w row L M N. "
            f"({_natural_add('bb','bc','cb','cc','db','dc','w','cell_coeff_add')}) -> "
            f"({_cell('ab','ac','bb','bc','w','row','L','cell_first')}) -> "
            f"({_cell('ab','ac','cb','cc','w','row','M','cell_second')}) -> "
            f"({_cell('ab','ac','db','dc','w','row','N','cell_third')}) -> L + M = N",
            ("integer_span_dot_product_pointwise_add", "beta_at_exists", "mul_add", "one_mul", "zero_add"),
            _intro("ab","ac","bb","bc","cb","cc","db","dc","w","row","L","M","N","hadd","hfirst","hsecond","hthird")
            +_cases("hfirst",4)+_parts(cell1,3)+_cases("hsecond",4)+_parts(cell2,3)+_cases("hthird",4)+_parts(cell3,3)
            +_call("integer_span_dot_product_pointwise_add",*(f"x{k}" if k else "x" for k in range(12)),"w","L","M","N")
            +(f"exact {_part(cell1,3,2)}",f"exact {_part(cell2,3,2)}",f"exact {_part(cell3,3,2)}")
            +_intro("i","a","b","c","d","e","f","hi","ha","hb","hc","hd","he","hf")
            +_choose_at("hmatrix","ab","ac","row * w + 1 * i","cell_matrix_source")
            +_choose_at("hleft","bb","bc","i","cell_coeff_left")
            +_choose_at("hright","cb","cc","i","cell_coeff_right")
            +_choose_at("htotal","db","dc","i","cell_coeff_total")
            +("have haeq : a = x12",)+_call(_part(cell1,3,0),"i","x12","a")+("exact hi","exact hmatrix_witness","exact ha")
            +("have hceq : c = x12",)+_call(_part(cell2,3,0),"i","x12","c")+("exact hi","exact hmatrix_witness","exact hc")
            +("have heeq : e = x12",)+_call(_part(cell3,3,0),"i","x12","e")+("exact hi","exact hmatrix_witness","exact he")
            +("have hindex : 0 + 1 * i = i","simp [one_mul, zero_add]")
            +tuple(command for value,body,hypothesis,target,source in (
                ("x13",cell1,"hleft_witness","b","hb"),
                ("x14",cell2,"hright_witness","d","hd"),
                ("x15",cell3,"htotal_witness","f","hf"),
            ) for command in (
                f"have h{target}eq : {target} = {value}",
                *_call(_part(body,3,1),"i",value,target),"exact hi",
                "rewrite hindex","rewrite hindex",f"exact {hypothesis}",f"exact {source}",
            ))
            +("have hcoeff : x15 = x13 + x14",)+_call("hadd","i","x13","x14","x15")
            +("exact hi","exact hleft_witness","exact hright_witness","exact htotal_witness")
            +("rewrite haeq","rewrite hbeq","rewrite hceq","rewrite hdeq","rewrite heeq","rewrite hfeq","rewrite hcoeff","apply mul_add"),
            "Each genuine row-by-column multiplication cell distributes over an actual coded sum of coefficient vectors; the old affine row and column slices are aligned at every coordinate.",
        ),
        spec(
            "integer_span_natural_product_entry",
            "forall ab ac bb bc w pb pc l i z. "
            f"({_natural_product('ab','ac','bb','bc','w','pb','pc','l','entry_product')}) -> "
            f"({_lt('i','l','entry_bound')}) -> ({_at('pb','pc','i','z','entry_decoded')}) -> "
            f"({_cell('ab','ac','bb','bc','w','i','z','entry_result')})",
            ("le_zero", "le_of_succ_le_succ", "one_mul", "beta_at_unique"),
            _intro("ab","ac","bb","bc","w","pb","pc","l","i","z","hproduct","hi","hz")
            +(f"have hentry : exists row column value. {_and('i = 1 * row + column',_lt('column','1','entry_column'),_product_cell_terms('ab','ac','bb','bc','w','1','row','column','value',tag='ics_entry_cell'),_at('pb','pc','i','value','entry_value'))}",)
            +_call("hproduct","i")+("exact hi",)+_cases("hentry",3)+_parts("hentry_witness_witness_witness",4)
            +("have hcol : x1 = 0",)+_call("le_zero","x1")+_call("le_of_succ_le_succ","x1","0")+("exact hentry_witness_witness_witness_right_left",)
            +("have hrow : x = i","symm","trans 1 * x + x1","exact hentry_witness_witness_witness_left","rewrite hcol","simp [one_mul]")
            +(f"have hc : {entrycell}","exact hentry_witness_witness_witness_right_right_left")
            +_rewrites("hcol","x1",entrycell,at="hc")+_rewrites("hrow","x",entrycell_zero,at="hc")
            +("have hvalue : x2 = z",)+_call("beta_at_unique","pb","pc","i","x2","z")
            +("exact hentry_witness_witness_witness_right_right_right","exact hz")
            +_rewrites("hvalue","x2",entrycell_row,at="hc")+("exact hc",),
            "Every actual entry of a one-column coded matrix product is the genuine cell at that same row, by bounded column-zero and beta uniqueness, not an arbitrary output witness.",
        ),
        spec(
            "integer_span_natural_product_add_right",
            "forall ab ac bb bc cb cc db dc w pb pc qb qc rb rc l. "
            f"({_natural_add('bb','bc','cb','cc','db','dc','w','product_coeff_add')}) -> "
            f"({_natural_product('ab','ac','bb','bc','w','pb','pc','l','product_first')}) -> "
            f"({_natural_product('ab','ac','cb','cc','w','qb','qc','l','product_second')}) -> "
            f"({_natural_product('ab','ac','db','dc','w','rb','rc','l','product_third')}) -> "
            f"({_natural_add('pb','pc','qb','qc','rb','rc','l','product_output_add')})",
            ("integer_span_natural_cell_add_right", "integer_span_natural_product_entry", "eq_symm"),
            _intro("ab","ac","bb","bc","cb","cc","db","dc","w","pb","pc","qb","qc","rb","rc","l","hadd","hfirst","hsecond","hthird","i","L","M","N","hi","hL","hM","hN")
            +_call("eq_symm","L + M","N")+_call("integer_span_natural_cell_add_right","ab","ac","bb","bc","cb","cc","db","dc","w","i","L","M","N")+("exact hadd",)
            +tuple(command for coeff,out,hyp,value,entry in (
                (("bb","bc"),("pb","pc"),"hfirst","L","hL"),
                (("cb","cc"),("qb","qc"),"hsecond","M","hM"),
                (("db","dc"),("rb","rc"),"hthird","N","hN"),
            ) for command in (
                *_call("integer_span_natural_product_entry","ab","ac",*coeff,"w",*out,"l","i",value),f"exact {hyp}","exact hi",f"exact {entry}",
            )),
            "Arbitrary finite one-column matrix multiplication is genuinely additive in the coded right coefficient vector, at every output row.",
        ),
        spec(
            "integer_span_pointwise_add_interchange",
            f"forall {' '.join(interchange_codes)} l. "
            +"".join(f"({_natural_add(*args,'l',tag)}) -> " for args,tag in (
                (("ab","ac","bb","bc","pb","pc"),"interchange_first"),
                (("cb","cc","db","dc","qb","qc"),"interchange_second"),
                (("eb","ec","fb","fc","rb","rc"),"interchange_total"),
                (("ab","ac","cb","cc","eb","ec"),"interchange_vertical_first"),
                (("bb","bc","db","dc","fb","fc"),"interchange_vertical_second"),
            ))+f"({_natural_add('pb','pc','qb','qc','rb','rc','l','interchange_result')})",
            ("beta_at_exists", "add_shuffle_middle"),
            _intro(*interchange_codes,"l","hfirst","hsecond","htotal","hleft","hright","i","v","w","z","hi","hv","hw","hz")
            +tuple(command for k in range(6) for command in _choose_at(f"ha{k}",interchange_codes[2*k],interchange_codes[2*k+1],"i",f"interchange_value{k}"))
            +("have heqv : v = x + x1",)+_call("hfirst","i","x","x1","v")+("exact hi","exact ha0_witness","exact ha1_witness","exact hv")
            +("have heqw : w = x2 + x3",)+_call("hsecond","i","x2","x3","w")+("exact hi","exact ha2_witness","exact ha3_witness","exact hw")
            +("have heqz : z = x4 + x5",)+_call("htotal","i","x4","x5","z")+("exact hi","exact ha4_witness","exact ha5_witness","exact hz")
            +("have heqleft : x4 = x + x2",)+_call("hleft","i","x","x2","x4")+("exact hi","exact ha0_witness","exact ha2_witness","exact ha4_witness")
            +("have heqright : x5 = x1 + x3",)+_call("hright","i","x1","x3","x5")+("exact hi","exact ha1_witness","exact ha3_witness","exact ha5_witness")
            +("trans x4 + x5","exact heqz","trans (x + x2) + (x1 + x3)","congr","exact heqleft","exact heqright",
              "trans (x + x1) + (x2 + x3)","apply add_shuffle_middle","congr","symm","exact heqv","symm","exact heqw"),
            "Five actual pointwise sum relations imply the regrouped sixth relation at every coordinate, with no assumption about canonical beta encodings.",
        ),
        spec(
            "integer_span_signed_product_negate",
            f"forall {' '.join((*matrix,*coefficient,'w','r',*output))}. ({_raw_product(*matrix,*coefficient,'w','r',*output,'negate_source')}) -> "
            f"({_raw_product(*matrix,'fb','fc','eb','ec','w','r','nb','nc','pb','pc','negate_result')})",
            (),
            _intro(*matrix,*coefficient,"w","r",*output,"hproduct")+_cases("hproduct",8)+_parts(raw_h,6)
            +_exists("x4","x5","x6","x7","x","x1","x2","x3")
            +tuple(command for k in (2,3,0,1,5,4) for command in (("split",f"exact {_part(raw_h,6,k)}") if k != 4 else (f"exact {_part(raw_h,6,k)}",))),
            "Swapping the actual coefficient vector's positive and negative codes swaps the exact signed product's output components, by the four original coded natural products.",
        ),
        spec(
            "integer_span_signed_product_equal_coefficients",
            f"forall {' '.join((*matrix,'b','c','w','r'))}. exists pb pc. ({_raw_product(*matrix,'b','c','b','c','w','r','pb','pc','pb','pc','equal_coefficients')})",
            ("beta_matrix_product_exists", "beta_pointwise_add_prefix_exists"),
            _intro(*matrix,"b","c","w","r")
            +(f"have hfirst : exists pb pc. ({_natural_product('ab','ac','b','c','w','pb','pc','r * 1','zero_first_product')})",)
            +_call("beta_matrix_product_exists","ab","ac","b","c","w","1","r")+_cases("hfirst",2)
            +(f"have hsecond : exists nb nc. ({_natural_product('db','dc','b','c','w','nb','nc','r * 1','zero_second_product')})",)
            +_call("beta_matrix_product_exists","db","dc","b","c","w","1","r")+_cases("hsecond",2)
            +(f"have hsum : exists pb pc. ({_natural_add('x','x1','x2','x3','pb','pc','r * 1','zero_output_sum')})",)
            +_call("beta_pointwise_add_prefix_exists","x","x1","x2","x3","r * 1")+_cases("hsum",2)
            +_exists("x4","x5","x","x1","x2","x3","x","x1","x2","x3")
            +("split","exact hfirst_witness_witness","split","exact hsecond_witness_witness","split","exact hfirst_witness_witness","split","exact hsecond_witness_witness","split","exact hsum_witness_witness","exact hsum_witness_witness"),
            "Equal positive and negative coefficient streams construct a genuine coded matrix product with equal output streams, hence integer zero in every row.",
        ),
        spec(
            "integer_span_signed_product_add_right",
            f"forall {' '.join(signed_add_arguments)}. "
            f"({_natural_add(*coefficient[:2],*coefficient2[:2],*coefficient3[:2],'w','sp_cofp')}) -> "
            f"({_natural_add(*coefficient[2:],*coefficient2[2:],*coefficient3[2:],'w','sp_cofn')}) -> "
            +"".join(f"({_raw_product(*matrix,*cof,'w','r',*out,f'sp{k}')}) -> " for k,(cof,out) in enumerate(((coefficient,output),(coefficient2,output2),(coefficient3,output3))))
            +_and(_natural_add(*output[:2],*output2[:2],*output3[:2],'r * 1','sp_output_p'),_natural_add(*output[2:],*output2[2:],*output3[2:],'r * 1','sp_output_n')),
            ("integer_span_natural_product_add_right", "integer_span_pointwise_add_interchange"),
            _intro(*signed_add_arguments,"haddp","haddn","hfirst","hsecond","hthird")
            +tuple(command for h,body in zip(("hfirst","hsecond","hthird"),raw_sources) for command in (*_cases(h,8),*_parts(body,6)))
            +tuple(command for k,(mat,cof1,cof2,cof3,hadd) in enumerate(raw_products) for command in (
                f"have hnew{k} : {_natural_add(*xnames[2*k:2*k+2],*xnames[8+2*k:10+2*k],*xnames[16+2*k:18+2*k],'r * 1',f'sp_new{k}')}",
                *_call("integer_span_natural_product_add_right",*mat,*cof1,*cof2,*cof3,"w",*xnames[2*k:2*k+2],*xnames[8+2*k:10+2*k],*xnames[16+2*k:18+2*k],"r * 1"),
                f"exact {hadd}",*(f"exact {_part(body,6,k)}" for body in raw_sources),
            ))
            +("split",)
            +tuple(command for k,offset,outs in ((4,0,(output[:2],output2[:2],output3[:2])),(5,4,(output[2:],output2[2:],output3[2:]))) for command in (
                *_call("integer_span_pointwise_add_interchange",*xnames[offset:offset+4],*xnames[8+offset:12+offset],*xnames[16+offset:20+offset],*(v for out in outs for v in out),"r * 1"),
                *(f"exact {_part(body,6,k)}" for body in raw_sources),f"exact hnew{offset//2}",f"exact hnew{offset//2+1}",
            )),
            "The actual signed coded matrix product is componentwise additive in actual componentwise coefficient sums, by all four proved natural matrix-vector products and exact pointwise regrouping.",
        ),
        spec(
            "integer_span_pair_equal_transitive",
            "forall a b c d e f. a + d = c + b -> c + f = e + d -> a + f = e + b",
            ("add_right_cancel", "four_square_euler_add_swap_last"),
            _intro("a","b","c","d","e","f","hfirst","hsecond")
            +_call("add_right_cancel","a + f","e + b","d")
            +("trans (a + d) + f","apply four_square_euler_add_swap_last","trans (c + b) + f","congr","exact hfirst","refl",
              "trans (c + f) + b","apply four_square_euler_add_swap_last","trans (e + d) + b","congr","exact hsecond","refl","apply four_square_euler_add_swap_last"),
            "Equality of signed natural pairs is transitive by genuine cancellative arithmetic, not equality of the chosen positive and negative components.",
        ),
        spec(
            "integer_span_pair_add_congruence",
            "forall p n q m a b c d. p + b = a + n -> q + d = c + m -> (p + q) + (b + d) = (a + c) + (n + m)",
            ("add_shuffle_middle",),
            _intro("p","n","q","m","a","b","c","d","hfirst","hsecond")
            +("trans (p + b) + (q + d)","apply add_shuffle_middle","trans (a + n) + (c + m)","congr","exact hfirst","exact hsecond","apply add_shuffle_middle"),
            "Component addition represents the sum of integer pairs even when either input has a different noncanonical positive/negative encoding.",
        ),
        spec(
            "integer_vector_equal_reflexive",
            f"forall {' '.join((*matrix,'l'))}. ({_equal(*matrix,*matrix,'l','equal_refl')})",
            ("beta_at_unique",),
            _intro(*matrix,"l","i","a","b","c","d","hi","ha","hb","hc","hd")
            +("have hpositive : a = c",)+_call("beta_at_unique","ab","ac","i","a","c")+("exact ha","exact hc")
            +("have hnegative : d = b",)+_call("beta_at_unique","db","dc","i","d","b")+("exact hd","exact hb")
            +("congr","exact hpositive","exact hnegative"),
            "Any signed coded vector equals itself as an integer vector, using functionality of the actual positive and negative decoded entries.",
        ),
        spec(
            "integer_vector_equal_transitive",
            f"forall {' '.join((*matrix,*coefficient,*output,'l'))}. ({_equal(*matrix,*coefficient,'l','equal_trans_first')}) -> "
            f"({_equal(*coefficient,*output,'l','equal_trans_second')}) -> ({_equal(*matrix,*output,'l','equal_trans_result')})",
            ("beta_at_exists", "integer_span_pair_equal_transitive"),
            _intro(*matrix,*coefficient,*output,"l","hfirst","hsecond","i","a","b","e","f","hi","ha","hb","he","hf")
            +_choose_at("hmiddlep","eb","ec","i","equal_middle_p")+_choose_at("hmiddlen","fb","fc","i","equal_middle_n")
            +_call("integer_span_pair_equal_transitive","a","b","x","x1","e","f")
            +_call("hfirst","i","a","b","x","x1")+("exact hi","exact ha","exact hb","exact hmiddlep_witness","exact hmiddlen_witness")
            +_call("hsecond","i","x","x1","e","f")+("exact hi","exact hmiddlep_witness","exact hmiddlen_witness","exact he","exact hf"),
            "Integer-vector equality is genuinely transitive across independently coded, noncanonical intermediate signed entries.",
        ),
        spec(
            "integer_vector_equal_negated",
            f"forall {' '.join((*matrix,*coefficient,'l'))}. ({_equal(*matrix,*coefficient,'l','equal_neg_source')}) -> "
            f"({_equal(*matrix[2:],*matrix[:2],*coefficient[2:],*coefficient[:2],'l','equal_neg_result')})",
            ("add_comm", "eq_symm"),
            _intro(*matrix,*coefficient,"l","hequal","i","a","b","c","d","hi","ha","hb","hc","hd")
            +("have hsource : b + c = d + a",)+_call("hequal","i","b","a","d","c")+("exact hi","exact hb","exact ha","exact hd","exact hc")
            +("trans d + a","apply add_comm","trans b + c")+_call("eq_symm","b + c","d + a")
            +("exact hsource","apply add_comm"),
            "Swapping positive and negative components preserves actual integer-vector equality, independently of the chosen pair representatives.",
        ),
        spec(
            "integer_vector_equal_components_zero",
            f"forall b c l. ({_zero('b','c','b','c','l','zero_same')})",
            ("beta_at_unique",),
            _intro("b","c","l","i","a","d","hi","ha","hd")
            +_call("beta_at_unique","b","c","i","a","d")+("exact ha","exact hd"),
            "Equal positive and negative beta streams represent the zero vector at every finite dimension.",
        ),
        spec(
            "integer_vector_equal_zero_from_same_components",
            f"forall b c {' '.join((*output,'l'))}. ({_zero(*output,'l','zero_target')}) -> ({_equal('b','c','b','c',*output,'l','zero_same_target')})",
            ("beta_at_unique", "add_comm"),
            _intro("b","c",*output,"l","hzero","i","u","v","p","n","hi","hu","hv","hp","hn")
            +("have hsame : u = v",)+_call("beta_at_unique","b","c","i","u","v")+("exact hu","exact hv")
            +("have hz : p = n",)+_call("hzero","i","p","n")+("exact hi","exact hp","exact hn")
            +("rewrite hsame","rewrite hz","apply add_comm"),
            "An equal-component product represents every actual zero vector, including all noncanonical zero pair encodings.",
        ),
        spec(
            "integer_vector_add_from_component_sums",
            f"forall {' '.join((*matrix,*coefficient,*output,'l'))}. "
            f"({_natural_add(*matrix[:2],*coefficient[:2],*output[:2],'l','add_components_p')}) -> "
            f"({_natural_add(*matrix[2:],*coefficient[2:],*output[2:],'l','add_components_n')}) -> ({_add(*matrix,*coefficient,*output,'l','add_components_result')})",
            (),
            _intro(*matrix,*coefficient,*output,"l","hpositive","hnegative","i","a","b","c","d","e","f","hi","ha","hb","hc","hd","he","hf")
            +("have hp : e = a + c",)+_call("hpositive","i","a","c","e")+("exact hi","exact ha","exact hc","exact he")
            +("have hn : f = b + d",)+_call("hnegative","i","b","d","f")+("exact hi","exact hb","exact hd","exact hf")
            +("rewrite hp","rewrite hn","refl"),
            "Actual coded component sums yield integer-vector addition without requiring canonical representatives.",
        ),
        spec(
            "integer_vector_add_exists",
            f"forall {' '.join((*matrix,*coefficient,'l'))}. exists {' '.join(output)}. ({_add(*matrix,*coefficient,*output,'l','vector_add_exists')})",
            ("beta_pointwise_add_prefix_exists", "integer_vector_add_from_component_sums"),
            _intro(*matrix,*coefficient,"l")
            +(f"have hp : exists b c. ({_natural_add(*matrix[:2],*coefficient[:2],'b','c','l','vector_add_exists_p')})",)
            +_call("beta_pointwise_add_prefix_exists",*matrix[:2],*coefficient[:2],"l")+_cases("hp",2)
            +(f"have hn : exists b c. ({_natural_add(*matrix[2:],*coefficient[2:],'b','c','l','vector_add_exists_n')})",)
            +_call("beta_pointwise_add_prefix_exists",*matrix[2:],*coefficient[2:],"l")+_cases("hn",2)
            +_exists("x","x1","x2","x3")+_call("integer_vector_add_from_component_sums",*matrix,*coefficient,"x","x1","x2","x3","l")
            +("exact hp_witness_witness","exact hn_witness_witness"),
            "Every two finite signed vectors have a constructively produced coded integer sum, including the empty vector.",
        ),
        spec(
            "integer_vector_add_transport_inputs",
            f"forall {' '.join((*matrix,*coefficient,*output,*output2,*output3,'l'))}. "
            f"({_equal(*matrix,*output,'l','add_transport_first')}) -> ({_equal(*coefficient,*output2,'l','add_transport_second')}) -> "
            f"({_add(*matrix,*coefficient,*output3,'l','add_transport_source')}) -> ({_add(*output,*output2,*output3,'l','add_transport_result')})",
            ("beta_at_exists", "integer_span_pair_equal_transitive", "integer_span_pair_add_congruence"),
            _intro(*matrix,*coefficient,*output,*output2,*output3,"l","hfirst","hsecond","hadd","i","a","b","c","d","e","f","hi","ha","hb","hc","hd","he","hf")
            +tuple(command for k,codes in enumerate((matrix[:2],matrix[2:],coefficient[:2],coefficient[2:])) for command in _choose_at(f"hraw{k}",*codes,"i",f"add_transport_raw{k}"))
            +_call("integer_span_pair_equal_transitive","e","f","x + x2","x1 + x3","a + c","b + d")
            +_call("hadd","i","x","x1","x2","x3","e","f")
            +("exact hi","exact hraw0_witness","exact hraw1_witness","exact hraw2_witness","exact hraw3_witness","exact he","exact hf")
            +_call("integer_span_pair_add_congruence","x","x1","x2","x3","a","b","c","d")
            +_call("hfirst","i","x","x1","a","b")+("exact hi","exact hraw0_witness","exact hraw1_witness","exact ha","exact hb")
            +_call("hsecond","i","x2","x3","c","d")+("exact hi","exact hraw2_witness","exact hraw3_witness","exact hc","exact hd"),
            "Integer-vector addition respects genuine signed-difference equality of both inputs, not merely recoding of equal natural components.",
        ),
        spec(
            "integer_vector_add_functional",
            f"forall {' '.join((*matrix,*coefficient,*output,*output2,'l'))}. "
            f"({_add(*matrix,*coefficient,*output,'l','add_functional_first')}) -> ({_add(*matrix,*coefficient,*output2,'l','add_functional_second')}) -> "
            f"({_equal(*output,*output2,'l','add_functional_result')})",
            ("beta_at_exists", "integer_span_pair_equal_transitive", "eq_symm"),
            _intro(*matrix,*coefficient,*output,*output2,"l","hfirst","hsecond","i","a","b","c","d","hi","ha","hb","hc","hd")
            +tuple(command for k,codes in enumerate((matrix[:2],matrix[2:],coefficient[:2],coefficient[2:])) for command in _choose_at(f"hinput{k}",*codes,"i",f"add_functional_input{k}"))
            +_call("integer_span_pair_equal_transitive","a","b","x + x2","x1 + x3","c","d")
            +_call("hfirst","i","x","x1","x2","x3","a","b")
            +("exact hi","exact hinput0_witness","exact hinput1_witness","exact hinput2_witness","exact hinput3_witness","exact ha","exact hb")
            +_call("eq_symm","c + (x1 + x3)","(x + x2) + d")
            +_call("hsecond","i","x","x1","x2","x3","c","d")
            +("exact hi","exact hinput0_witness","exact hinput1_witness","exact hinput2_witness","exact hinput3_witness","exact hc","exact hd"),
            "Two actual sums of the same signed vectors are equal as integer vectors, without claiming equality of their beta codes or separate components.",
        ),
        spec(
            "integer_matrix_vector_product_exists",
            f"forall {' '.join((*matrix,*coefficient,'w','r'))}. exists {' '.join(output)}. ({_matrix_vector(*matrix,*coefficient,'w','r',*output,'linear_exists')})",
            ("beta_signed_matrix_product_exists", "integer_vector_equal_reflexive"),
            _intro(*matrix,*coefficient,"w","r")
            +(f"have hraw : exists {' '.join(output)}. ({_raw_product(*matrix,*coefficient,'w','r',*output,'linear_exists_raw')})",)
            +_call("beta_signed_matrix_product_exists",*matrix,*coefficient,"w","1","r")+_cases("hraw",4)
            +_exists("x","x1","x2","x3","x","x1","x2","x3")+("split","exact "+"hraw"+"_witness"*4)
            +_call("integer_vector_equal_reflexive","x","x1","x2","x3","r"),
            "Every finite signed coefficient vector has a fully constructed matrix-vector image as represented integers; the output is an actual coded signed product.",
        ),
        spec(
            "integer_matrix_vector_product_transport",
            f"forall {' '.join((*matrix,*coefficient,'w','r',*output,*output2))}. ({_matrix_vector(*matrix,*coefficient,'w','r',*output,'linear_transport_source')}) -> "
            f"({_equal(*output,*output2,'r','linear_transport_equal')}) -> ({_matrix_vector(*matrix,*coefficient,'w','r',*output2,'linear_transport_result')})",
            ("integer_vector_equal_transitive",),
            _intro(*matrix,*coefficient,"w","r",*output,*output2,"himage","hequal")+_cases("himage",4)+("cases "+"himage"+"_witness"*4,)
            +_exists("x","x1","x2","x3")+("split","exact "+"himage"+"_witness"*4+"_left")
            +_call("integer_vector_equal_transitive","x","x1","x2","x3",*output,*output2,"r")
            +("exact "+"himage"+"_witness"*4+"_right","exact hequal"),
            "A coefficient witness represents every integer-equal output vector, even when its two component streams differ.",
        ),
        spec(
            "integer_matrix_vector_product_zero",
            f"forall {' '.join((*matrix,'w','r',*output))}. ({_zero(*output,'r','linear_zero_source')}) -> "
            f"({_matrix_vector(*matrix,'0','0','0','0','w','r',*output,'linear_zero_result')})",
            ("integer_span_signed_product_equal_coefficients", "integer_vector_equal_zero_from_same_components"),
            _intro(*matrix,"w","r",*output,"hzero")
            +(f"have hraw : exists b c. ({_raw_product(*matrix,'0','0','0','0','w','r','b','c','b','c','linear_zero_raw')})",)
            +_call("integer_span_signed_product_equal_coefficients",*matrix,"0","0","w","r")+_cases("hraw",2)
            +_exists("x","x1","x","x1")+("split","exact hraw_witness_witness")
            +_call("integer_vector_equal_zero_from_same_components","x","x1",*output,"r")+("exact hzero",),
            "The actual zero coefficient vector represents every zero integer vector through a genuine coded signed matrix product, for arbitrary matrix dimensions.",
        ),
        spec(
            "integer_matrix_vector_product_negated",
            f"forall {' '.join((*matrix,*coefficient,'w','r',*output))}. ({_matrix_vector(*matrix,*coefficient,'w','r',*output,'linear_neg_source')}) -> "
            f"({_matrix_vector(*matrix,*coefficient[2:],*coefficient[:2],'w','r',*output[2:],*output[:2],'linear_neg_result')})",
            ("integer_span_signed_product_negate", "integer_vector_equal_negated"),
            _intro(*matrix,*coefficient,"w","r",*output,"himage")+_cases("himage",4)+("cases "+"himage"+"_witness"*4,)
            +_exists("x2","x3","x","x1")+("split",)
            +_call("integer_span_signed_product_negate",*matrix,*coefficient,"w","r","x","x1","x2","x3")
            +("exact "+"himage"+"_witness"*4+"_left",)
            +_call("integer_vector_equal_negated","x","x1","x2","x3",*output,"r")
            +("exact "+"himage"+"_witness"*4+"_right",),
            "Swapping the constructed coefficient streams witnesses the negative image, and the image remains correct for arbitrary signed-pair output representations.",
        ),
        spec(
            "integer_matrix_vector_add_coefficients",
            f"forall {' '.join(raw_sum_args)}. "
            f"({_matrix_vector(*matrix,*coefficient,'w','r',*output,'linear_sum_first')}) -> "
            f"({_matrix_vector(*matrix,*coefficient2,'w','r',*output2,'linear_sum_second')}) -> "
            f"({_natural_add(*coefficient[:2],*coefficient2[:2],*coefficient3[:2],'w','linear_sum_p')}) -> "
            f"({_natural_add(*coefficient[2:],*coefficient2[2:],*coefficient3[2:],'w','linear_sum_n')}) -> "
            f"({_raw_product(*matrix,*coefficient3,'w','r',*output3,'linear_sum_raw')}) -> ({_add(*output,*output2,*output3,'r','linear_sum_result')})",
            ("integer_span_signed_product_add_right", "integer_vector_add_from_component_sums", "integer_vector_add_transport_inputs", "mul_one"),
            _intro(*raw_sum_args,"hfirst","hsecond","haddp","haddn","hraw")
            +_cases("hfirst",4)+("cases "+"hfirst"+"_witness"*4,)+_cases("hsecond",4)+("cases "+"hsecond"+"_witness"*4,)
            +(f"have hsum : {_and(_natural_add('x','x1','x4','x5',*output3[:2],'r * 1','linear_raw_sum_p'),_natural_add('x2','x3','x6','x7',*output3[2:],'r * 1','linear_raw_sum_n'))}",)
            +_call("integer_span_signed_product_add_right",*matrix,*coefficient,*coefficient2,*coefficient3,"w","r","x","x1","x2","x3","x4","x5","x6","x7",*output3)
            +("exact haddp","exact haddn","exact "+"hfirst"+"_witness"*4+"_left","exact "+"hsecond"+"_witness"*4+"_left","exact hraw")
            +("have hlength : r * 1 = r","apply mul_one","rewrite hlength at hsum","rewrite hlength at hsum","cases hsum")
            +_call("integer_vector_add_transport_inputs","x","x1","x2","x3","x4","x5","x6","x7",*output,*output2,*output3,"r")
            +("exact "+"hfirst"+"_witness"*4+"_right","exact "+"hsecond"+"_witness"*4+"_right")
            +_call("integer_vector_add_from_component_sums","x","x1","x2","x3","x4","x5","x6","x7",*output3,"r")
            +("exact hsum_left","exact hsum_right"),
            "Actual componentwise coefficient addition produces the integer sum of both represented matrix images, after explicit signed-equality transport and width-one row-length normalization.",
        ),
        spec(
            "integer_matrix_vector_add_constructive",
            f"forall {' '.join(linear_add_args)}. "
            f"({_matrix_vector(*matrix,*coefficient,'w','r',*output,'linear_construct_first')}) -> "
            f"({_matrix_vector(*matrix,*coefficient2,'w','r',*output2,'linear_construct_second')}) -> "
            f"({_add(*output,*output2,*output3,'r','linear_construct_sum')}) -> exists {' '.join(coefficient3)}. ({add_constructed})",
            ("beta_pointwise_add_prefix_exists", "beta_signed_matrix_product_exists", "integer_matrix_vector_add_coefficients", "integer_vector_add_functional"),
            _intro(*linear_add_args,"hfirst","hsecond","hadd")
            +(f"have hp : exists b c. ({_natural_add(*coefficient[:2],*coefficient2[:2],'b','c','w','construct_coeff_p')})",)
            +_call("beta_pointwise_add_prefix_exists",*coefficient[:2],*coefficient2[:2],"w")+_cases("hp",2)
            +(f"have hn : exists b c. ({_natural_add(*coefficient[2:],*coefficient2[2:],'b','c','w','construct_coeff_n')})",)
            +_call("beta_pointwise_add_prefix_exists",*coefficient[2:],*coefficient2[2:],"w")+_cases("hn",2)
            +(f"have hraw : exists P C N D. ({_raw_product(*matrix,'x','x1','x2','x3','w','r','P','C','N','D','construct_raw')})",)
            +_call("beta_signed_matrix_product_exists",*matrix,"x","x1","x2","x3","w","1","r")+_cases("hraw",4)
            +(f"have hrawsum : {_add(*output,*output2,'x4','x5','x6','x7','r','construct_raw_sum')}",)
            +_call("integer_matrix_vector_add_coefficients",*matrix,*coefficient,*coefficient2,"x","x1","x2","x3","w","r",*output,*output2,"x4","x5","x6","x7")
            +("exact hfirst","exact hsecond","exact hp_witness_witness","exact hn_witness_witness","exact "+"hraw"+"_witness"*4)
            +_exists("x","x1","x2","x3")+("split","exact hp_witness_witness","split","exact hn_witness_witness")
            +_exists("x4","x5","x6","x7")+("split","exact "+"hraw"+"_witness"*4)
            +_call("integer_vector_add_functional",*output,*output2,"x4","x5","x6","x7",*output3,"r")
            +("exact hrawsum","exact hadd"),
            "The sum of two represented images has constructively generated coefficient codes whose positive and negative streams are the actual sums of the original coefficient streams; those same codes represent the given integer-sum output.",
        ),
        spec(
            "integer_column_span_transport",
            f"forall {' '.join((*matrix,'w','r',*output,*output2))}. ({_span(*matrix,'w','r',*output,'span_transport_source')}) -> "
            f"({_equal(*output,*output2,'r','span_transport_equal')}) -> ({_span(*matrix,'w','r',*output2,'span_transport_result')})",
            ("integer_matrix_vector_product_transport",),
            _intro(*matrix,"w","r",*output,*output2,"hspan","hequal")+_cases("hspan",4)+_exists("x","x1","x2","x3")
            +_call("integer_matrix_vector_product_transport",*matrix,"x","x1","x2","x3","w","r",*output,*output2)
            +("exact "+"hspan"+"_witness"*4,"exact hequal"),
            "Column-span membership depends on the represented integer vector, not on its beta codes or its separate positive and negative components.",
        ),
        spec(
            "integer_column_span_zero",
            f"forall {' '.join((*matrix,'w','r',*output))}. ({_zero(*output,'r','span_zero_source')}) -> ({_span(*matrix,'w','r',*output,'span_zero_result')})",
            ("integer_matrix_vector_product_zero",),
            _intro(*matrix,"w","r",*output,"hzero")+_exists("0","0","0","0")
            +_call("integer_matrix_vector_product_zero",*matrix,"w","r",*output)+("exact hzero",),
            "Every actual zero integer vector belongs to the arbitrary finite integer column span, with the explicit all-zero coefficient code.",
        ),
        spec(
            "integer_column_span_contains_zero",
            f"forall {' '.join((*matrix,'w','r'))}. ({_span(*matrix,'w','r','0','0','0','0','span_literal_zero')})",
            ("integer_column_span_zero", "integer_vector_equal_components_zero"),
            _intro(*matrix,"w","r")+_call("integer_column_span_zero",*matrix,"w","r","0","0","0","0")
            +_call("integer_vector_equal_components_zero","0","0","r"),
            "Every finite generating matrix has the literal zero vector in its integer column span, without nonemptiness or independence assumptions.",
        ),
        spec(
            "integer_column_span_negated",
            f"forall {' '.join((*matrix,'w','r',*output))}. ({_span(*matrix,'w','r',*output,'span_neg_source')}) -> "
            f"({_span(*matrix,'w','r',*output[2:],*output[:2],'span_neg_result')})",
            ("integer_matrix_vector_product_negated",),
            _intro(*matrix,"w","r",*output,"hspan")+_cases("hspan",4)+_exists("x2","x3","x","x1")
            +_call("integer_matrix_vector_product_negated",*matrix,"x","x1","x2","x3","w","r",*output)
            +("exact "+"hspan"+"_witness"*4,),
            "The negative of every column-span vector belongs to the same span, witnessed by swapping its actual positive and negative coefficient streams.",
        ),
        spec(
            "integer_column_span_negate_closed",
            f"forall {' '.join((*matrix,'w','r',*output,*output2))}. ({_span(*matrix,'w','r',*output,'span_negative_source')}) -> "
            f"({_equal(*output[2:],*output[:2],*output2,'r','span_negative_relation')}) -> ({_span(*matrix,'w','r',*output2,'span_negative_result')})",
            ("integer_column_span_transport", "integer_column_span_negated"),
            _intro(*matrix,"w","r",*output,*output2,"hspan","hnegative")
            +_call("integer_column_span_transport",*matrix,"w","r",*output[2:],*output[:2],*output2)
            +_call("integer_column_span_negated",*matrix,"w","r",*output)+("exact hspan","exact hnegative"),
            "Column spans are closed under every actual integer-negative output, not only under literal swapping of one chosen output code.",
        ),
        spec(
            "integer_column_span_add_closed",
            f"forall {' '.join((*matrix,'w','r',*output,*output2,*output3))}. "
            f"({_span(*matrix,'w','r',*output,'span_add_first')}) -> ({_span(*matrix,'w','r',*output2,'span_add_second')}) -> "
            f"({_add(*output,*output2,*output3,'r','span_add_sum')}) -> ({_span(*matrix,'w','r',*output3,'span_add_result')})",
            ("integer_matrix_vector_add_constructive",),
            _intro(*matrix,"w","r",*output,*output2,*output3,"hfirst","hsecond","hadd")+_cases("hfirst",4)+_cases("hsecond",4)
            +(f"have hcoeff : exists ib ic jb jc. ({_and(_natural_add('x','x1','x4','x5','ib','ic','w','span_new_coeffp'),_natural_add('x2','x3','x6','x7','jb','jc','w','span_new_coeffn'),_matrix_vector(*matrix,'ib','ic','jb','jc','w','r',*output3,'span_new_image'))})",)
            +_call("integer_matrix_vector_add_constructive",*matrix,"x","x1","x2","x3","x4","x5","x6","x7","w","r",*output,*output2,*output3)
            +("exact "+"hfirst"+"_witness"*4,"exact "+"hsecond"+"_witness"*4,"exact hadd")
            +_cases("hcoeff",4)+_parts("hcoeff"+"_witness"*4,3)+_exists("x8","x9","x10","x11")
            +("exact "+"hcoeff"+"_witness"*4+"_right_right",),
            "Every actual integer sum of two arbitrary column-span vectors lies in the same span, with the constructed finite sums of their actual coefficient streams as witnesses.",
        ),
        spec(
            "integer_column_span_add_exists",
            f"forall {' '.join((*matrix,'w','r',*output,*output2))}. ({_span(*matrix,'w','r',*output,'span_add_exists_first')}) -> "
            f"({_span(*matrix,'w','r',*output2,'span_add_exists_second')}) -> exists {' '.join(output3)}. "
            f"({_and(_add(*output,*output2,*output3,'r','span_add_exists_sum'),_span(*matrix,'w','r',*output3,'span_add_exists_result'))})",
            ("integer_vector_add_exists", "integer_column_span_add_closed"),
            _intro(*matrix,"w","r",*output,*output2,"hfirst","hsecond")
            +(f"have hsum : exists rb rc sb sc. ({_add(*output,*output2,'rb','rc','sb','sc','r','span_constructed_sum')})",)
            +_call("integer_vector_add_exists",*output,*output2,"r")+_cases("hsum",4)+_exists("x","x1","x2","x3")
            +("split","exact "+"hsum"+"_witness"*4)
            +_call("integer_column_span_add_closed",*matrix,"w","r",*output,*output2,"x","x1","x2","x3")
            +("exact hfirst","exact hsecond","exact "+"hsum"+"_witness"*4),
            "Both the sum vector and its span-membership coefficient witnesses are constructively available for every two integer column-span vectors.",
        ),
        spec(
            "integer_column_span_negate_exists",
            f"forall {' '.join((*matrix,'w','r',*output))}. ({_span(*matrix,'w','r',*output,'span_neg_exists_source')}) -> exists {' '.join(output2)}. "
            f"({_and(_equal(*output[2:],*output[:2],*output2,'r','span_neg_exists_relation'),_span(*matrix,'w','r',*output2,'span_neg_exists_result'))})",
            ("integer_vector_equal_reflexive", "integer_column_span_negated"),
            _intro(*matrix,"w","r",*output,"hspan")+_exists(*output[2:],*output[:2])+("split",)
            +_call("integer_vector_equal_reflexive",*output[2:],*output[:2],"r")
            +_call("integer_column_span_negated",*matrix,"w","r",*output)+("exact hspan",),
            "Every integer column-span vector has a constructively coded negative in the same span, together with actual negated coefficient witnesses.",
        ),
    )


__all__ = [
    "integer_vector_equal", "integer_vector_zero", "integer_vector_add", "integer_vector_negate",
    "integer_matrix_vector_product", "integer_column_span", "make_integer_column_span_candidate_theorems",
]
