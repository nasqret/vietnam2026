"""Constructive Eisenstein arithmetic and Euclidean division in strict HA.

Coordinates are genuine integer differences of pairs of naturals.  Norms and
all ring equalities are subtraction-free equations, not new kernel symbols.
The Euclidean construction uses the fundamental parallelogram: for residues
0 <= s,t < M the Eisenstein norm is at most max(s,t)^2, strictly below M^2.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_generalized_crt_congruence_candidate import _checked_term
from .finite_fold_surface import _identifier
from .ha_signed_balance_candidate import signed_balance
from .ha_signed_decode_candidate import signed_decode
from .signed_integer_division_candidate import _context, _call, _intro
from .gaussian_euclidean_candidate import (
    _square, _commutative_expansion_identity,
    _complex_equal, _complex_add, _complex_difference, _scale, _and, _parts,
    _ordered_expansion_identity, _rep, _gaussian, _code_add, _part,
    _complex_product as _gaussian_product,
)


_ADD = ("add_assoc","add_comm","four_square_add_swap_right_tail")
_POLY = ("add_mul","mul_add","mul_assoc","add_assoc","add_comm","mul_comm","four_square_add_swap_right_tail","natural_mul_swap_right_tail")


def _simp(names: tuple[str, ...]) -> str:
    return "simp [" + ", ".join(names) + "]"


def _add(a: str, b: str) -> str:
    return f"(({a}) + ({b}))"


def _mul(a: str, b: str) -> str:
    return f"(({a}) * ({b}))"


def _pair_mul(a: tuple[str,str], b: tuple[str,str]) -> tuple[str,str]:
    p,n = a
    q,t = b
    return _add(_mul(p,q),_mul(n,t)),_add(_mul(p,t),_mul(n,q))


def _pair_add(a: tuple[str,str], b: tuple[str,str]) -> tuple[str,str]:
    return _add(a[0],b[0]),_add(a[1],b[1])


def _pair_equal(a: tuple[str,str], b: tuple[str,str]) -> str:
    return f"{_add(a[0],b[1])} = {_add(b[0],a[1])}"


def _norm_parts(ap: str, an: str, bp: str, bn: str) -> tuple[str,str]:
    a,b = (ap,an),(bp,bn)
    return _pair_add(_pair_add(_pair_mul(a,a),_pair_mul(b,b)),_pair_mul(a,b)[::-1])


def _norm(ap: str, an: str, bp: str, bn: str, n: str) -> str:
    positive,negative = _norm_parts(ap,an,bp,bn)
    return f"{positive} = {_add(negative,n)}"


def eisenstein_coordinate_norm_relation(ap: str, an: str, bp: str, bn: str, n: str, *, tag: str, variables: tuple[str,...]) -> str:
    """The exact integer norm (ap-an)^2-(ap-an)(bp-bn)+(bp-bn)^2."""
    _identifier(tag,"Eisenstein norm tag")
    context = _context(variables)
    return _norm(*(_checked_term(value,context) for value in (ap,an,bp,bn,n)))


def _natural_norm(a: str, b: str, n: str) -> str:
    return f"({_mul(a,a)} + {_mul(b,b)}) = ({_mul(a,b)} + ({n}))"


def _lt(a: str, b: str, tag: str = "lt") -> str:
    return f"exists ee_gap_{tag}. ee_gap_{tag} + S ({a}) = ({b})"


def _le(a: str, b: str, tag: str = "le") -> str:
    return f"exists ee_bound_{tag}. ee_bound_{tag} + ({a}) = ({b})"


def _weighted(ap: str, an: str, bp: str, bn: str, n: str, tag: str) -> str:
    s,t = f"ee_real_square_{tag}",f"ee_imag_square_{tag}"
    return f"exists {s} {t}. ({_square(ap,an,s)}) /\\ (({_square(bp,bn,t)}) /\\ ({n}) = {s} + 3 * {t})"


def _transform(ap: str, an: str, bp: str, bn: str) -> tuple[str,str,str,str]:
    return _add(_mul("2",ap),bn),_add(_mul("2",an),bp),bp,bn


def _weighted_product(first: tuple[str,...], second: tuple[str,...]) -> tuple[str,...]:
    a,b,c,d = first[:2],first[2:],second[:2],second[2:]
    ac,bd,ad,bc = _pair_mul(a,c),_pair_mul(b,d),_pair_mul(a,d),_pair_mul(b,c)
    return _add(ac[0],_mul("3",bd[1])),_add(ac[1],_mul("3",bd[0])),*_pair_add(ad,bc)


def _eisenstein_product(first: tuple[str,...], second: tuple[str,...]) -> tuple[str,...]:
    a,b,c,d = first[:2],first[2:],second[:2],second[2:]
    ac,bd,ad,bc = _pair_mul(a,c),_pair_mul(b,d),_pair_mul(a,d),_pair_mul(b,c)
    return *_pair_add(ac,bd[::-1]),*_pair_add(_pair_add(ad,bc),bd[::-1])


def _conjugate(value: tuple[str,...]) -> tuple[str,...]:
    """a+bω ↦ (a-b)-bω, as exact signed-coordinate contributions."""
    ap,an,bp,bn=value
    return _add(ap,bn),_add(an,bp),bn,bp


def _omega(value: tuple[str,...]) -> tuple[str,...]:
    """Multiplication by ω: (a,b)↦(-b,a-b)."""
    ap,an,bp,bn=value
    return bn,bp,_add(ap,bn),_add(an,bp)


def eisenstein_coordinate_product_relation(
    ap: str, an: str, bp: str, bn: str, cp: str, cn: str, dp: str, dn: str,
    rp: str, rn: str, sp: str, sn: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """The actual product (a+bω)(c+dω), with ω²+ω+1=0."""
    _identifier(tag,"Eisenstein product tag")
    context = _context(variables)
    terms = tuple(_checked_term(value,context) for value in (ap,an,bp,bn,cp,cn,dp,dn,rp,rn,sp,sn))
    product = _eisenstein_product(terms[:4],terms[4:8])
    return f"({_pair_equal(product[:2],terms[8:10])}) /\\ ({_pair_equal(product[2:],terms[10:])})"


def _names(tag: str, *stems: str) -> tuple[str,...]:
    return tuple("ee_"+stem+"_"+tag for stem in stems)


def _public_arguments(values: tuple[str,...], tag: str, variables: tuple[str,...]) -> tuple[str,...]:
    _identifier(tag,"Eisenstein binder tag")
    context=_context(variables)
    if any(value.startswith(("ee_","ge_","sd_","sb_","sif_")) for value in context):
        raise ValueError("Eisenstein argument context captures a generated binder")
    return tuple(_checked_term(value,context) for value in values)


def eisenstein_integer_relation(code: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Exactly the shared ZPairValid carrier, with no second integer encoding."""
    return _gaussian(*_public_arguments((code,),tag,variables),tag)


def eisenstein_add_relation(first: str, second: str, output: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Exactly the neutral ZPairAdd graph shared with Gaussian coordinates."""
    return _code_add(*_public_arguments((first,second,output),tag,variables),tag)


def _code_norm(code: str, value: str, tag: str) -> str:
    coords=_names(tag,"norm_rp","norm_rn","norm_ip","norm_in")
    return f"exists {' '.join(coords)}. "+_and(_rep(code,*coords,tag+"representation"),_norm(*coords,value))


def eisenstein_norm_relation(code: str, value: str, *, tag: str, variables: tuple[str,...]) -> str:
    """The actual norm a²-ab+b² of a canonical signed-coordinate code."""
    return _code_norm(*_public_arguments((code,value),tag,variables),tag)


def _code_mul(first: str, second: str, output: str, tag: str) -> str:
    A=_names(tag,"first_rp","first_rn","first_ip","first_in")
    B=_names(tag,"second_rp","second_rn","second_ip","second_in")
    return f"exists {' '.join((*A,*B))}. "+_and(_rep(first,*A,tag+"first"),_rep(second,*B,tag+"second"),_rep(output,*_eisenstein_product(A,B),tag+"output"))


def eisenstein_multiply_relation(first: str, second: str, output: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Actual (a+bω)(c+dω)=(ac-bd)+(ad+bc-bd)ω on the shared ZPair carrier."""
    return _code_mul(*_public_arguments((first,second,output),tag,variables),tag)


def _code_divrem(dividend: str, divisor: str, quotient: str, remainder: str, tag: str) -> str:
    product,=_names(tag,"division_product")
    return f"exists {product}. "+_and(_code_mul(divisor,quotient,product,tag+"product"),_code_add(product,remainder,dividend,tag+"sum"))


def eisenstein_division_remainder_relation(dividend: str, divisor: str, quotient: str, remainder: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Exact canonical Eisenstein equation a=bq+r using the real operation graphs."""
    return _code_divrem(*_public_arguments((dividend,divisor,quotient,remainder),tag,variables),tag)


def _code_euclidean(dividend: str, divisor: str, quotient: str, remainder: str, U: str, V: str, tag: str) -> str:
    return _and(_code_divrem(dividend,divisor,quotient,remainder,tag+"equation"),_code_norm(remainder,U,tag+"smallnorm"),_code_norm(divisor,V,tag+"largenorm"),_lt(U,V,tag+"strict"))


def eisenstein_euclidean_division_relation(dividend: str, divisor: str, quotient: str, remainder: str, remainder_norm: str, divisor_norm: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Actual canonical equation and witnessed strict decrease of the actual norms."""
    return _code_euclidean(*_public_arguments((dividend,divisor,quotient,remainder,remainder_norm,divisor_norm),tag,variables),tag)


def _cases(name: str, count: int) -> tuple[str,...]:
    return tuple("cases "+name+"_witness"*i for i in range(count))


def _coordinate_chain(points: tuple[tuple[str,...],...], steps: tuple[tuple[str,...],...], tag: str) -> tuple[str,...]:
    """Emit small ordinary cuts, preserving unspecialized equality laws."""
    if len(points)!=len(steps)+1 or not steps:
        raise ValueError("an equality chain must have one proof per consecutive pair")
    result=()
    previous=""
    for i,step in enumerate(steps):
        current=f"ee_chain_step_{tag}_{i}"
        result+=(f"have {current} : {_complex_equal(points[i],points[i+1])}",)+step
        if i:
            path=f"ee_chain_path_{tag}_{i}"
            result+=(f"have {path} : {_complex_equal(points[0],points[i+1])}",)+_call("gaussian_equal_transitive",*points[0],*points[i],*points[i+1])+(f"exact {previous}",f"exact {current}",)
            previous=path
        else:
            previous=current
    return result+(f"exact {previous}",)


def _natural_zero_branch(a: str, b: str, order: str, source: str, *, reverse: bool) -> tuple[str,...]:
    body = (
        f"cases {order}",f"have hlarge : {b} = {a} + x",f"trans x + {a}","symm",f"exact {order}_witness","apply add_comm",
        f"have hvalue : 0 = {a} * {a} + {a} * x + x * x",
    )+_call("eisenstein_natural_norm_gap_value",a,"x","0")
    body += ("rewrite <- hlarge",)*3+(f"exact {source}",)
    body += (f"have hfirst : {a} * {a} + {a} * x = 0",)+_call("add_eq_zero_left",f"({a} * {a} + {a} * x)","(x * x)")+("symm","exact hvalue",)
    body += (f"have hsmallzero : {a} = 0",)+_call("square_zero_root",a)+_call("add_eq_zero_left",f"({a} * {a})",f"({a} * x)")+("exact hfirst",)
    body += ("have hgapzero : x = 0",)+_call("square_zero_root","x")+_call("add_eq_zero_right",f"({a} * {a} + {a} * x)","(x * x)")+("symm","exact hvalue",)
    body += (f"have hlargezero : {b} = 0",f"trans {a} + x","exact hlarge","simp [hsmallzero, hgapzero, zero_add]","split",)
    return body+(("exact hlargezero","exact hsmallzero") if reverse else ("exact hsmallzero","exact hlargezero"))


def make_eisenstein_euclidean_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B,C,D = ("ap","an"),("bp","bn"),("cp","cn"),("dp","dn")
    aa,bb,ab = _pair_mul(A,A),_pair_mul(B,B),_pair_mul(A,B)
    cc,dd,cd = _pair_mul(C,C),_pair_mul(D,D),_pair_mul(C,D)
    oldsq,newsq = _pair_add(aa,bb),_pair_add(cc,dd)
    oldnorm,newnorm = _norm_parts(*A,*B),_norm_parts(*C,*D)

    def normal_exists(a: str,b: str,left_zero: str,right_zero: str,same: bool) -> tuple[str,...]:
        if same:
            return (
                f"have hnatural : exists n. {_natural_norm(a,b,'n')}",
                *_call("eisenstein_natural_norm_exists",a,b),"cases hnatural","exists x",
                f"simp [{left_zero}, {right_zero}, mul_zero_left, zero_add]",
            )
        return (f"exists {a} * {a} + {b} * {b} + {a} * {b}",f"simp [{left_zero}, {right_zero}, mul_zero_left, zero_add]",)

    return (
        spec(
            "eisenstein_natural_norm_symmetric",
            f"forall a b n. ({_natural_norm('a','b','n')}) -> ({_natural_norm('b','a','n')})",
            ("add_comm","mul_comm"),
            _intro("a","b","n","hnorm")+("trans a * a + b * b","apply add_comm","trans a * b + n","exact hnorm","congr","apply mul_comm","refl"),
            "The natural-coordinate Eisenstein norm is symmetric in its two coordinates.",
        ),
        spec(
            "eisenstein_natural_norm_gap_value",
            f"forall a d n. ({_natural_norm('a','a + d','n')}) -> n = a * a + a * d + d * d",
            ("add_left_cancel",*_POLY),
            _intro("a","d","n","hnorm")+_call("add_left_cancel","(a * (a + d))","n","(a * a + a * d + d * d)")
            +("trans a * a + (a + d) * (a + d)","symm","exact hnorm",_simp(_POLY)),
            "Ordering the coordinates gives the explicit subtraction-free norm a²+ad+d².",
        ),
        spec(
            "eisenstein_natural_norm_exists",
            f"forall a b. exists n. ({_natural_norm('a','b','n')})",
            ("le_total",*_POLY),
            _intro("a","b")+("specialize le_total a","specialize le_total b","cases le_total","cases le_total_left","exists a * a + a * x + x * x",)
            +("rewrite <- le_total_left_witness",)*3+(_simp(_POLY),"cases le_total_right","exists b * b + b * x + x * x",)
            +("rewrite <- le_total_right_witness",)*3+(_simp(_POLY),),
            "Every pair of natural coordinates has an actual natural Eisenstein norm, constructed by a decidable order comparison.",
        ),
        spec(
            "eisenstein_natural_norm_zero",
            f"forall a b. ({_natural_norm('a','b','0')}) -> a = 0 /\\ b = 0",
            ("le_total","eisenstein_natural_norm_gap_value","eisenstein_natural_norm_symmetric","add_comm","zero_add","add_eq_zero_left","add_eq_zero_right","square_zero_root"),
            _intro("a","b","hnorm")+("specialize le_total a","specialize le_total b","cases le_total",)
            +_natural_zero_branch("a","b","le_total_left","hnorm",reverse=False)
            +(f"have hreverse : {_natural_norm('b','a','0')}",)+_call("eisenstein_natural_norm_symmetric","a","b","0")+("exact hnorm",)
            +_natural_zero_branch("b","a","le_total_right","hreverse",reverse=True),
            "A zero Eisenstein norm forces both natural coordinates to vanish, including the diagonal boundary.",
        ),
        spec(
            "eisenstein_natural_norm_le_larger_square",
            f"forall a b n. ({_le('a','b')}) -> ({_natural_norm('a','b','n')}) -> ({_le('n','b * b')})",
            ("mul_le_mul_left","add_left_cancel",*_ADD),
            _intro("a","b","n","hle","hnorm")+("have hproduct : exists k. k + a * a = a * b",)
            +_call("mul_le_mul_left","a","b","a")+("exact hle","cases hproduct","exists x",)
            +_call("add_left_cancel","(a * a)","(x + n)","(b * b)")
            +("trans (x + a * a) + n",_simp(_ADD),"rewrite hproduct_witness","symm","exact hnorm"),
            "If a≤b then a²−ab+b²≤b², with an actual natural gap witness.",
        ),
        spec(
            "eisenstein_parallelogram_norm_strict",
            f"forall a b m n. ({_lt('a','m')}) -> ({_lt('b','m')}) -> ({_natural_norm('a','b','n')}) -> ({_lt('n','m * m')})",
            ("le_total","eisenstein_natural_norm_symmetric","eisenstein_natural_norm_le_larger_square","square_lt_strict","lt_of_le_of_lt"),
            _intro("a","b","m","n","ha","hb","hnorm")+("specialize le_total a","specialize le_total b","cases le_total",)
            +_call("lt_of_le_of_lt","n","(b * b)","(m * m)")
            +_call("eisenstein_natural_norm_le_larger_square","a","b","n")+("exact le_total_left","exact hnorm",)
            +_call("square_lt_strict","b","m")+("exact hb",)
            +_call("lt_of_le_of_lt","n","(a * a)","(m * m)")
            +_call("eisenstein_natural_norm_le_larger_square","b","a","n")+("exact le_total_right",)
            +_call("eisenstein_natural_norm_symmetric","a","b","n")+("exact hnorm",)
            +_call("square_lt_strict","a","m")+("exact ha",),
            "Every lattice residue pair 0≤a,b<m has norm strictly below m², including zero and a=b=m−1.",
        ),
        spec(
            "eisenstein_coordinate_norm_functional",
            f"forall ap an bp bn n m. ({_norm(*A,*B,'n')}) -> ({_norm(*A,*B,'m')}) -> n = m",
            ("add_left_cancel",),
            _intro(*A,*B,"n","m","hn","hm")+_call("add_left_cancel",oldnorm[1],"n","m")
            +(f"trans {oldnorm[0]}","symm","exact hn","exact hm"),
            "The subtraction-free signed-coordinate norm has a unique natural value.",
        ),
        spec(
            "eisenstein_coordinate_norm_negation",
            f"forall ap an bp bn n. ({_norm(*A,*B,'n')}) -> ({_norm(*A[::-1],*B[::-1],'n')})",
            (*_ADD,"mul_comm"),
            _intro(*A,*B,"n","hnorm")+(f"trans {oldnorm[0]}",_simp((*_ADD,"mul_comm")),f"trans {oldnorm[1]} + n","exact hnorm",_simp((*_ADD,"mul_comm"))),
            "Negating both genuine signed coordinates leaves the Eisenstein norm unchanged.",
        ),
        spec(
            "eisenstein_normal_coordinate_norm_exists",
            f"forall ap an bp bn. (ap = 0 \\/ an = 0) -> (bp = 0 \\/ bn = 0) -> exists n. ({_norm(*A,*B,'n')})",
            ("eisenstein_natural_norm_exists","mul_zero_left","zero_add"),
            _intro(*A,*B,"ha","hb")+("cases ha","cases hb",)
            +normal_exists("an","bn","ha_left","hb_left",True)
            +normal_exists("an","bp","ha_left","hb_right",False)
            +("cases hb",)
            +normal_exists("ap","bn","ha_right","hb_left",False)
            +normal_exists("ap","bp","ha_right","hb_right",True),
            "Every normalized signed-coordinate pair has an actual natural norm, in all four sign quadrants.",
        ),
        spec(
            "eisenstein_pair_natural_value_transport",
            "forall p n P N v. p = n + v -> p + N = P + n -> P = N + v",
            ("add_right_cancel",*_ADD),
            _intro("p","n","P","N","v","hvalue","hcross")+_call("add_right_cancel","P","(N + v)","n")
            +("trans p + N","symm","exact hcross","rewrite hvalue",_simp(_ADD)),
            "An equal signed-pair representative preserves the same natural value.",
        ),
        spec(
            "eisenstein_coordinate_norm_transport",
            f"forall ap an bp bn cp cn dp dn n. ({_pair_equal(A,C)}) -> ({_pair_equal(B,D)}) -> ({_norm(*A,*B,'n')}) -> ({_norm(*C,*D,'n')})",
            ("matrix_integer_pair_product_balance","matrix_integer_pair_negation_balance","integer_span_pair_add_congruence","eisenstein_pair_natural_value_transport"),
            _intro(*A,*B,*C,*D,"n","ha","hb","hnorm")
            +(f"have haa : {_pair_equal(aa,cc)}",)+_call("matrix_integer_pair_product_balance",*A,*C,*A,*C)+("exact ha","exact ha",)
            +(f"have hbb : {_pair_equal(bb,dd)}",)+_call("matrix_integer_pair_product_balance",*B,*D,*B,*D)+("exact hb","exact hb",)
            +(f"have hab : {_pair_equal(ab,cd)}",)+_call("matrix_integer_pair_product_balance",*A,*C,*B,*D)+("exact ha","exact hb",)
            +(f"have hsquares : {_pair_equal(oldsq,newsq)}",)+_call("integer_span_pair_add_congruence",*aa,*bb,*cc,*dd)+("exact haa","exact hbb",)
            +(f"have hnegative : {_pair_equal(ab[::-1],cd[::-1])}",)+_call("matrix_integer_pair_negation_balance",*ab,*cd)+("exact hab",)
            +(f"have hnormpair : {_pair_equal(oldnorm,newnorm)}",)+_call("integer_span_pair_add_congruence",*oldsq,*ab[::-1],*newsq,*cd[::-1])+("exact hsquares","exact hnegative",)
            +_call("eisenstein_pair_natural_value_transport",*oldnorm,*newnorm,"n")+("exact hnorm","exact hnormpair"),
            "The norm depends only on the represented integers, not on a chosen positive/negative decomposition of either coordinate.",
        ),
        spec(
            "eisenstein_coordinate_norm_exists",
            f"forall ap an bp bn. exists n. ({_norm(*A,*B,'n')})",
            ("signed_balance_total","signed_decode_normal","eisenstein_normal_coordinate_norm_exists","eisenstein_coordinate_norm_transport","add_comm"),
            _intro(*A,*B)
            +(f"have hfirst : exists code. ({signed_balance('code','ap','an',tag='ee_first')})",)+_call("signed_balance_total",*A)
            +("cases hfirst","cases hfirst_witness","cases hfirst_witness_witness","cases hfirst_witness_witness_witness",)
            +(f"have hsecond : exists code. ({signed_balance('code','bp','bn',tag='ee_second')})",)+_call("signed_balance_total",*B)
            +("cases hsecond","cases hsecond_witness","cases hsecond_witness_witness","cases hsecond_witness_witness_witness",)
            +("have hnorm : exists n. "+_norm("x1","x2","x4","x5","n"),)
            +_call("eisenstein_normal_coordinate_norm_exists","x1","x2","x4","x5")
            +_call("signed_decode_normal","x","x1","x2")+("exact hfirst_witness_witness_witness_left",)
            +_call("signed_decode_normal","x3","x4","x5")+("exact hsecond_witness_witness_witness_left","cases hnorm","exists x6",)
            +_call("eisenstein_coordinate_norm_transport","x1","x2","x4","x5",*A,*B,"x6")
            +("trans an + x1","apply add_comm","symm","exact hfirst_witness_witness_witness_right",)
            +("trans bn + x4","apply add_comm","symm","exact hsecond_witness_witness_witness_right","exact hnorm_witness"),
            "Every arbitrary signed-coordinate representation has a natural Eisenstein norm, by actual signed normalization and checked representative invariance.",
        ),
    ) + _weighted_rows(spec) + _coordinate_ring_rows(spec) + _multiplicative_norm_rows(spec) + _division_rows(spec) + _coded_rows(spec)


def _weighted_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B,C,D = ("ap","an"),("bp","bn"),("cp","cn"),("dp","dn")
    aa,bb,ab = _pair_mul(A,A),_pair_mul(B,B),_pair_mul(A,B)
    normparts = _norm_parts(*A,*B)
    doubleA = _mul("2",A[0]),_mul("2",A[1])
    cross2 = _pair_mul(doubleA,B)
    transformed = _transform(*A,*B)
    comp = "sh + (2 * P + 2 * P) = ((2 * 2) * sa + sb) + (2 * Q + 2 * Q)"
    compensation=_intro("sa","sb","P","Q","sh","N","hnorm","hdifference")
    compensation+=_call("add_right_cancel","(sh + 3 * sb)","(4 * N)","(4 * P)")+("trans (sh + (2 * P + 2 * P)) + 3 * sb",)
    compensation+=_commutative_expansion_identity("(sh + 3 * sb) + 4 * P","(sh + (2 * P + 2 * P)) + 3 * sb")
    compensation+=("rewrite hdifference","trans 4 * ((sa + sb) + Q)",)
    compensation+=_commutative_expansion_identity("(((2 * 2) * sa + sb) + (2 * Q + 2 * Q)) + 3 * sb","4 * ((sa + sb) + Q)")
    compensation+=("trans 4 * (P + N)","congr","refl","exact hnorm",)
    compensation+=_commutative_expansion_identity("4 * (P + N)","4 * N + 4 * P")
    return (
        spec(
            "eisenstein_norm_square_balance",
            f"forall ap an bp bn sa sb N. ({_square(*A,'sa')}) -> ({_square(*B,'sb')}) -> ({_norm(*A,*B,'N')}) -> (sa + sb) + ({ab[1]}) = ({ab[0]}) + N",
            ("add_right_cancel",*_ADD),
            _intro(*A,*B,"sa","sb","N","ha","hb","hnorm")
            +_call("add_right_cancel",f"((sa + sb) + ({ab[1]}))",f"(({ab[0]}) + N)",_add(aa[1],bb[1]))
            +(f"trans {normparts[0]}",_simp(("ha","hb",*_ADD)),f"trans {normparts[1]} + N","exact hnorm",_simp(_ADD)),
            "Actual natural coordinate squares give the exact signed cross-term balance sa+sb=ENorm+ab.",
        ),
        spec(
            "eisenstein_weighted_embedding_compensation",
            f"forall sa sb P Q sh N. (sa + sb) + Q = P + N -> ({comp}) -> sh + 3 * sb = 4 * N",
            ("add_right_cancel","add_mul","mul_add","mul_assoc",*_ADD,"mul_succ_left","mul_zero_left","zero_add","one_mul","mul_one"),
            compensation,
            "The elementary compensation proves 4N=(2a-b)²+3b² without integer subtraction or an inequality assumption.",
        ),
        spec(
            "eisenstein_norm_weighted_square_identity",
            f"forall ap an bp bn sa sb sh N. ({_square(*A,'sa')}) -> ({_square(*B,'sb')}) -> ({_square(*transformed[:2],'sh')}) -> ({_norm(*A,*B,'N')}) -> sh + 3 * sb = 4 * N",
            ("gaussian_signed_square_scaled","gaussian_signed_square_difference_compensation","eisenstein_norm_square_balance","eisenstein_weighted_embedding_compensation","mul_assoc","mul_add"),
            _intro(*A,*B,"sa","sb","sh","N","ha","hb","htransformed","hnorm")
            +(f"have hdouble : {_square(*doubleA,'(2 * 2) * sa')}",)+_call("gaussian_signed_square_scaled",*A,"sa","2")+("exact ha",)
            +(f"have hdifference : sh + ({_add(*((cross2[0],)*2))}) = ((2 * 2) * sa + sb) + ({_add(*((cross2[1],)*2))})",)
            +_call("gaussian_signed_square_difference_compensation",*doubleA,*B,"((2 * 2) * sa)","sb","sh")+("exact hdouble","exact hb","exact htransformed",)
            +(f"have hp : {cross2[0]} = 2 * ({ab[0]})",_simp(("mul_assoc","mul_add")),)
            +(f"have hn : {cross2[1]} = 2 * ({ab[1]})",_simp(("mul_assoc","mul_add")),)
            +("rewrite hp at hdifference","rewrite hp at hdifference","rewrite hn at hdifference","rewrite hn at hdifference",)
            +_call("eisenstein_weighted_embedding_compensation","sa","sb",ab[0],ab[1],"sh","N")
            +_call("eisenstein_norm_square_balance",*A,*B,"sa","sb","N")+("exact ha","exact hb","exact hnorm","exact hdifference"),
            "The actual signed square identity 4ENorm(a,b)=(2a-b)²+3b² holds for every signed representative.",
        ),
        spec(
            "eisenstein_weighted_norm_exists",
            f"forall ap an bp bn. exists N. ({_weighted(*A,*B,'N','total')})",
            ("gaussian_signed_square_exists",),
            _intro(*A,*B)+(f"have ha : exists sa. {_square(*A,'sa')}",)+_call("gaussian_signed_square_exists",*A)+("cases ha",)
            +(f"have hb : exists sb. {_square(*B,'sb')}",)+_call("gaussian_signed_square_exists",*B)+("cases hb","exists x + 3 * x1","exists x","exists x1","split","exact ha_witness","split","exact hb_witness","refl"),
            "Every genuine signed coordinate pair has a constructed positive-definite weight-three squared norm.",
        ),
        spec(
            "eisenstein_weighted_norm_functional",
            f"forall ap an bp bn N M. ({_weighted(*A,*B,'N','first')}) -> ({_weighted(*A,*B,'M','second')}) -> N = M",
            ("gaussian_signed_square_functional",),
            _intro(*A,*B,"N","M","hfirst","hsecond")+_cases("hfirst",2)+("cases hfirst_witness_witness","cases hfirst_witness_witness_right",)
            +_cases("hsecond",2)+("cases hsecond_witness_witness","cases hsecond_witness_witness_right",)
            +("have heq : x = x2",)+_call("gaussian_signed_square_functional",*A,"x","x2")+("exact hfirst_witness_witness_left","exact hsecond_witness_witness_left",)
            +("have heq2 : x1 = x3",)+_call("gaussian_signed_square_functional",*B,"x1","x3")+("exact hfirst_witness_witness_right_left","exact hsecond_witness_witness_right_left",)
            +("trans x + 3 * x1","exact hfirst_witness_witness_right_right","rewrite heq","rewrite heq2","symm","exact hsecond_witness_witness_right_right"),
            "The weighted norm is a genuine functional arithmetic relation, independent of chosen square witnesses.",
        ),
        spec(
            "eisenstein_norm_to_weighted_norm",
            f"forall ap an bp bn N. ({_norm(*A,*B,'N')}) -> ({_weighted(*transformed,'4 * N','image')})",
            ("gaussian_signed_square_exists","eisenstein_norm_weighted_square_identity"),
            _intro(*A,*B,"N","hnorm")
            +(f"have ha : exists sa. {_square(*A,'sa')}",)+_call("gaussian_signed_square_exists",*A)+("cases ha",)
            +(f"have hb : exists sb. {_square(*B,'sb')}",)+_call("gaussian_signed_square_exists",*B)+("cases hb",)
            +(f"have ht : exists sh. {_square(*transformed[:2],'sh')}",)+_call("gaussian_signed_square_exists",*transformed[:2])+("cases ht","exists x2","exists x1","split","exact ht_witness","split","exact hb_witness","symm",)
            +_call("eisenstein_norm_weighted_square_identity",*A,*B,"x","x1","x2","N")+("exact ha_witness","exact hb_witness","exact ht_witness","exact hnorm"),
            "The exact linear embedding (a,b)↦(2a-b,b) has actual weight-three norm four times the Eisenstein norm.",
        ),
        spec(
            "eisenstein_weighted_norm_transport",
            f"forall ap an bp bn cp cn dp dn N. ({_pair_equal(A,C)}) -> ({_pair_equal(B,D)}) -> ({_weighted(*A,*B,'N','source')}) -> ({_weighted(*C,*D,'N','target')})",
            ("gaussian_signed_square_integer_transport",),
            _intro(*A,*B,*C,*D,"N","ha","hb","hnorm")+_cases("hnorm",2)+("cases hnorm_witness_witness","cases hnorm_witness_witness_right","exists x","exists x1","split",)
            +_call("gaussian_signed_square_integer_transport",*A,*C,"x")+("exact ha","exact hnorm_witness_witness_left","split",)
            +_call("gaussian_signed_square_integer_transport",*B,*D,"x1")+("exact hb","exact hnorm_witness_witness_right_left","exact hnorm_witness_witness_right_right"),
            "The positive-definite weighted norm respects actual equality of both integer coordinates.",
        ),
        spec(
            "eisenstein_weighted_norm_scaled",
            f"forall ap an bp bn N k. ({_weighted(*A,*B,'N','scaled_source')}) -> ({_weighted(*(_mul('k',value) for value in (*A,*B)),'(k * k) * N','scaled_target')})",
            ("gaussian_signed_square_scaled","mul_add","mul_assoc","mul_comm","natural_mul_swap_right_tail"),
            _intro(*A,*B,"N","k","hnorm")+_cases("hnorm",2)+("cases hnorm_witness_witness","cases hnorm_witness_witness_right","exists (k * k) * x","exists (k * k) * x1","split",)
            +_call("gaussian_signed_square_scaled",*A,"x","k")+("exact hnorm_witness_witness_left","split",)
            +_call("gaussian_signed_square_scaled",*B,"x1","k")+("exact hnorm_witness_witness_right_left","rewrite hnorm_witness_witness_right_right",_simp(("mul_add","mul_assoc","mul_comm","natural_mul_swap_right_tail"))),
            "Scaling both actual integer coordinates multiplies the weighted norm by the exact natural square of the scale.",
        ),
    ) + _weighted_product_rows(spec)


def _coordinate_ring_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    names=tuple("abcdefghijklmnop")
    A,B,C,D=names[:4],names[4:8],names[8:12],names[12:]
    product=_eisenstein_product
    left_assoc,right_assoc=product(product(A,B),C),product(A,product(B,C))
    left_difference=product(A,_complex_difference(B,C))
    right_difference=_complex_difference(product(A,B),product(A,C))
    result=[]
    assoc_names=("eisenstein_product_associate_real","eisenstein_product_associate_imaginary")
    gaussian_left=_gaussian_product(_gaussian_product(A,B),C)
    gaussian_right=_gaussian_product(A,_gaussian_product(B,C))
    tail_left=_pair_mul(_pair_mul(A[2:],B[2:]),C[2:])
    tail_right=_pair_mul(A[2:],_pair_mul(B[2:],C[2:]))
    real_component_names=[]
    for label,actual,gaussian,tail in (("left",left_assoc,gaussian_left,tail_left),("right",right_assoc,gaussian_right,tail_right)):
        for i,sign in enumerate(("positive","negative")):
            name=f"eisenstein_real_associate_{label}_{sign}"
            real_component_names.append(name)
            target=_add(gaussian[i],tail[i])
            result.append(spec(name,f"forall {' '.join(names[:12])}. {actual[i]} = {target}",
                               ("add_mul","mul_add","mul_assoc",*(dep for dep in _ADD if label=="left" or dep!="add_comm")),_intro(*names[:12])+_ordered_expansion_identity(actual[i],target),
                               "The "+label+" associated Eisenstein real "+sign+" contribution is the checked Gaussian contribution plus the actual triple-imaginary contribution."))
    real_script=_intro(*names[:12])+(f"have htail : ({tail_left[0]} = {tail_right[0]}) /\\ ({tail_left[1]} = {tail_right[1]})",)
    real_script+=_call("signed_pair_mul_components_associate",*A[2:],*B[2:],*C[2:])+("cases htail","congr",)
    for i,sign in enumerate(("positive","negative")):
        if i:
            real_script+=("symm",)
        real_script+=(f"trans {_add(gaussian_left[i],tail_left[i])}",f"apply eisenstein_real_associate_left_{sign}",f"trans {_add(gaussian_right[i],tail_right[i])}","congr",f"apply gaussian_product_associate_real_{sign}",f"exact htail_{'left' if i==0 else 'right'}","symm",f"apply eisenstein_real_associate_right_{sign}",)
    result.append(spec(assoc_names[0],f"forall {' '.join(names[:12])}. {_pair_equal(left_assoc[:2],right_assoc[:2])}",
                       (*real_component_names,"signed_pair_mul_components_associate","gaussian_product_associate_real_positive","gaussian_product_associate_real_negative"),real_script,
                       "Real Eisenstein associativity follows from checked Gaussian real associativity and associative scalar triple products, with all natural contribution equations explicit."))
    labels=("real_positive","real_negative","imaginary_positive","imaginary_negative")
    diff_names=tuple("eisenstein_product_difference_"+label for label in labels)
    for i,name in enumerate(diff_names):
        result.append(spec(name,f"forall {' '.join(names[:12])}. {left_difference[i]} = {right_difference[i]}",
                           ("add_mul","mul_add","mul_assoc","add_assoc","four_square_add_swap_right_tail"),_intro(*names[:12])+_ordered_expansion_identity(left_difference[i],right_difference[i]),
                           "Exact "+labels[i].replace("_"," ")+" contribution of Eisenstein multiplication distributes over an actual signed difference."))
    result.append(spec("eisenstein_product_difference",f"forall {' '.join(names[:12])}. ({_complex_equal(left_difference,right_difference)})",
                       diff_names,_intro(*names[:12])+("split","congr",f"apply {diff_names[0]}","symm",f"apply {diff_names[1]}","congr",f"apply {diff_names[2]}","symm",f"apply {diff_names[3]}"),
                       "Actual Eisenstein multiplication distributes over signed subtraction in the second argument."))

    congruence=_intro(*names,"hfirst","hsecond")+("cases hfirst","cases hsecond","split",)
    AC,BD,AD,BC=(_pair_mul(A[:2],C[:2]),_pair_mul(A[2:],C[2:]),_pair_mul(A[:2],C[2:]),_pair_mul(A[2:],C[:2]))
    newAC,newBD,newAD,newBC=(_pair_mul(B[:2],D[:2]),_pair_mul(B[2:],D[2:]),_pair_mul(B[:2],D[2:]),_pair_mul(B[2:],D[:2]))
    congruence+=_call("integer_span_pair_add_congruence",*AC,*BD[::-1],*newAC,*newBD[::-1])
    congruence+=_call("matrix_integer_pair_product_balance",*A[:2],*B[:2],*C[:2],*D[:2])+("exact hfirst_left","exact hsecond_left",)
    congruence+=_call("matrix_integer_pair_negation_balance",*BD,*newBD)+_call("matrix_integer_pair_product_balance",*A[2:],*B[2:],*C[2:],*D[2:])+("exact hfirst_right","exact hsecond_right",)
    congruence+=(f"have himaginary_sum : {_pair_equal(_pair_add(AD,BC),_pair_add(newAD,newBC))}",)
    congruence+=_call("integer_span_pair_add_congruence",*AD,*BC,*newAD,*newBC)
    congruence+=_call("matrix_integer_pair_product_balance",*A[:2],*B[:2],*C[2:],*D[2:])+("exact hfirst_left","exact hsecond_right",)
    congruence+=_call("matrix_integer_pair_product_balance",*A[2:],*B[2:],*C[:2],*D[:2])+("exact hfirst_right","exact hsecond_left",)
    congruence+=_call("integer_span_pair_add_congruence",*_pair_add(AD,BC),*BD[::-1],*_pair_add(newAD,newBC),*newBD[::-1])+("exact himaginary_sum",)
    congruence+=_call("matrix_integer_pair_negation_balance",*BD,*newBD)+_call("matrix_integer_pair_product_balance",*A[2:],*B[2:],*C[2:],*D[2:])+("exact hfirst_right","exact hsecond_right",)

    rotated_product=product(_omega(A),B)
    product_rotated=_omega(product(A,B))
    covariance=_intro(*A,*B)+("split",)
    for i in (0,2):
        covariance+=_commutative_expansion_identity(_add(rotated_product[i],product_rotated[i+1]),_add(product_rotated[i],rotated_product[i+1]))
    rotated_left=product(_omega(product(A,B)),C)
    associated_rotated_left=product(product(_omega(A),B),C)
    associated_rotated_right=product(_omega(A),product(B,C))
    imaginary=_intro(*names[:12])
    imaginary+=(f"have hfirst : {_complex_equal(associated_rotated_left,rotated_left)}",)
    imaginary+=_call("eisenstein_product_integer_congruence",*product(_omega(A),B),*_omega(product(A,B)),*C,*C)+_call("eisenstein_omega_product_covariance",*A,*B)+_call("gaussian_equal_reflexive",*C)
    imaginary+=(f"have hrotation : {_complex_equal(rotated_left,_omega(left_assoc))}",)+_call("eisenstein_omega_product_covariance",*product(A,B),*C)
    imaginary+=(f"have hlast : {_complex_equal(associated_rotated_right,_omega(right_assoc))}",)+_call("eisenstein_omega_product_covariance",*A,*product(B,C))
    imaginary+=("cases hfirst","cases hrotation","cases hlast",f"have hnegative : {_pair_equal(left_assoc[2:][::-1],right_assoc[2:][::-1])}",)
    imaginary+=(f"have hleft : {_pair_equal(associated_rotated_left[:2],left_assoc[2:][::-1])}",)+_call("integer_span_pair_equal_transitive",*associated_rotated_left[:2],*rotated_left[:2],*left_assoc[2:][::-1])+("exact hfirst_left","exact hrotation_left",)
    imaginary+=(f"have hright : {_pair_equal(associated_rotated_left[:2],right_assoc[2:][::-1])}",)+_call("integer_span_pair_equal_transitive",*associated_rotated_left[:2],*associated_rotated_right[:2],*right_assoc[2:][::-1])
    imaginary+=_call("eisenstein_product_associate_real",*_omega(A),*B,*C)+("exact hlast_left",)
    imaginary+=_call("integer_span_pair_equal_transitive",*left_assoc[2:][::-1],*associated_rotated_left[:2],*right_assoc[2:][::-1])+("symm","exact hleft","exact hright",)
    imaginary+=_call("matrix_integer_pair_negation_balance",*left_assoc[2:][::-1],*right_assoc[2:][::-1])+("exact hnegative",)

    normparts=_norm_parts(*A)
    conjA=_conjugate(A)
    conjparts=_norm_parts(*conjA)
    conjugate_norm=_intro(*A,"N","hnorm")+_call("eisenstein_pair_natural_value_transport",*normparts,*conjparts,"N")+("exact hnorm",)
    conjugate_norm+=_commutative_expansion_identity(_add(normparts[0],conjparts[1]),_add(conjparts[0],normparts[1]))
    self_product=product(conjA,A)
    conjugate_product=_intro(*A,"N","hnorm")+(f"have hreal : {self_product[0]} = {_add(self_product[1],'N')}",)
    conjugate_product+=_call("eisenstein_pair_natural_value_transport",*normparts,*self_product[:2],"N")+("exact hnorm",)
    conjugate_product+=_commutative_expansion_identity(_add(normparts[0],self_product[1]),_add(self_product[0],normparts[1]))
    conjugate_product+=("split",f"trans {self_product[0]}","apply PA3",f"trans {_add(self_product[1],'N')}","exact hreal","apply add_comm",f"trans {self_product[2]}","apply PA3",f"trans {self_product[3]}",)
    conjugate_product+=_commutative_expansion_identity(self_product[2],self_product[3])+("symm","apply zero_add",)
    scalar_product=product(("N","0","0","0"),B)
    scaled=_scale("N",B)
    adjoint=product(conjA,product(A,B))
    associated=product(self_product,B)
    adjoint_script=_intro(*A,*B,"N","hnorm")+(f"have hassociation : {_complex_equal(adjoint,associated)}",)
    adjoint_script+=_call("gaussian_equal_symmetric",*associated,*adjoint)+_call("eisenstein_product_associate",*conjA,*A,*B)
    adjoint_script+=(f"have hscaling : {_complex_equal(associated,scaled)}",)+_call("gaussian_equal_transitive",*associated,*scalar_product,*scaled)
    adjoint_script+=_call("eisenstein_product_integer_congruence",*self_product,"N","0","0","0",*B,*B)
    adjoint_script+=_call("eisenstein_conjugate_product_is_norm",*A,"N")+("exact hnorm",)+_call("gaussian_equal_reflexive",*B)
    adjoint_script+=_call("eisenstein_natural_scalar_product","N",*B)
    adjoint_script+=_call("gaussian_equal_transitive",*adjoint,*associated,*scaled)+("exact hassociation","exact hscaling",)
    residual=_complex_difference(A,product(B,C))
    numerator=product(_conjugate(B),A)
    residual_product=product(_conjugate(B),residual)
    expanded_residual=_complex_difference(numerator,product(_conjugate(B),product(B,C)))
    actual_error=_complex_difference(numerator,_scale("N",C))
    residual_script=_intro(*names[:12],"N","hnorm")+_call("gaussian_equal_transitive",*residual_product,*expanded_residual,*actual_error)
    residual_script+=_call("eisenstein_product_difference",*_conjugate(B),*A,*product(B,C))
    residual_script+=_call("gaussian_difference_integer_congruence",*numerator,*numerator,*product(_conjugate(B),product(B,C)),*_scale("N",C))
    residual_script+=_call("gaussian_equal_reflexive",*numerator)+_call("eisenstein_adjoint_product_is_norm_scale",*B,*C,"N")+("exact hnorm",)

    result.extend((
        spec("eisenstein_product_integer_congruence",f"forall {' '.join(names)}. ({_complex_equal(A,B)}) -> ({_complex_equal(C,D)}) -> ({_complex_equal(product(A,C),product(B,D))})",
             ("integer_span_pair_add_congruence","matrix_integer_pair_product_balance","matrix_integer_pair_negation_balance"),congruence,
             "Eisenstein multiplication respects the represented integers in both inputs; overlapping natural representatives cause no ambiguity."),
        spec("eisenstein_omega_product_covariance",f"forall {' '.join((*A,*B))}. ({_complex_equal(rotated_product,product_rotated)})",
             ("add_mul","mul_add","mul_assoc",*_ADD),covariance,"The genuine coordinate rotation for multiplication by ω commutes with right multiplication; this small bilinear identity recovers imaginary associativity from real associativity."),
        spec("eisenstein_product_associate_imaginary",f"forall {' '.join(names[:12])}. {_pair_equal(left_assoc[2:],right_assoc[2:])}",
             ("eisenstein_product_integer_congruence","eisenstein_omega_product_covariance","gaussian_equal_reflexive","integer_span_pair_equal_transitive","eisenstein_product_associate_real","matrix_integer_pair_negation_balance"),imaginary,
             "Imaginary Eisenstein associativity follows constructively from real associativity under the exact ω rotation, avoiding an oversized polynomial expansion."),
        spec("eisenstein_product_associate",f"forall {' '.join(names[:12])}. ({_complex_equal(left_assoc,right_assoc)})",
             assoc_names,_intro(*names[:12])+("split",)+_call(assoc_names[0],*names[:12])+_call(assoc_names[1],*names[:12]),
             "Actual Eisenstein multiplication is associative on represented integer coordinates."),
        spec("eisenstein_coordinate_norm_conjugate",f"forall {' '.join(A)} N. ({_norm(*A,'N')}) -> ({_norm(*conjA,'N')})",
             ("eisenstein_pair_natural_value_transport",*_POLY[:-1]),conjugate_norm,
             "The actual Eisenstein conjugate (a-b)-bω has the same norm as a+bω for all signed representatives."),
        spec("eisenstein_conjugate_product_is_norm",f"forall {' '.join(A)} N. ({_norm(*A,'N')}) -> ({_complex_equal(self_product,('N','0','0','0'))})",
             ("eisenstein_pair_natural_value_transport",*_POLY[:-1],"zero_add"),conjugate_product,
             "The actual product of an Eisenstein integer with its genuine conjugate is its natural norm plus zero times ω."),
        spec("eisenstein_natural_scalar_product",f"forall N {' '.join(B)}. ({_complex_equal(scalar_product,scaled)})",
             ("mul_zero_left","zero_add"),_intro("N",*B)+("split",_simp(("mul_zero_left","zero_add")),_simp(("mul_zero_left","zero_add"))),
             "Multiplication by a natural real Eisenstein scalar is actual coordinatewise scaling."),
        spec("eisenstein_adjoint_product_is_norm_scale",f"forall {' '.join((*A,*B))} N. ({_norm(*A,'N')}) -> ({_complex_equal(adjoint,scaled)})",
             ("gaussian_equal_transitive","gaussian_equal_symmetric","eisenstein_product_associate","eisenstein_product_integer_congruence","eisenstein_conjugate_product_is_norm","gaussian_equal_reflexive","eisenstein_natural_scalar_product"),adjoint_script,
             "The Eisenstein adjugate identity conjugate(a)*(a*b)=N(a)*b follows from checked coordinate associativity and the actual conjugate product."),
        spec("eisenstein_residual_conjugate_identity",f"forall {' '.join(names[:12])} N. ({_norm(*B,'N')}) -> ({_complex_equal(residual_product,actual_error)})",
             ("gaussian_equal_transitive","eisenstein_product_difference","gaussian_difference_integer_congruence","gaussian_equal_reflexive","eisenstein_adjoint_product_is_norm_scale"),residual_script,
             "Multiplying the actual residual a-bq by conjugate(b) yields exactly the numerator error conjugate(b)*a-N(b)*q."),
    ))
    return tuple(result)


def _weighted_product_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B,C,D = ("ap","an"),("bp","bn"),("cp","cn"),("dp","dn")
    variables = (*A,*B,*C,*D)
    U,V,W,X = _pair_mul(A,C),_pair_mul(B,D),_pair_mul(A,D),_pair_mul(B,C)
    scaledV = tuple(_mul("3",value) for value in V)
    UV,WX = _pair_mul(U,V),_pair_mul(W,X)
    scaledUV = _pair_mul(U,scaledV)
    uv,wx = _pair_mul(("up","un"),("vp","vn")),_pair_mul(("wp","wn"),("xp","xn"))
    real,imag = ("up + vn","un + vp"),("wp + xp","wn + xn")
    actual = _weighted_product((*A,*B),(*C,*D))
    values = ("x * x2","(3 * x1) * (3 * x3)","x * x3","x1 * x2")
    squares = ("hfirst_witness_witness_left","hfirst_witness_witness_right_left","hsecond_witness_witness_left","hsecond_witness_witness_right_left")
    product_script = _intro(*variables,"N","M","hfirst","hsecond")
    product_script += _cases("hfirst",2)+("cases hfirst_witness_witness","cases hfirst_witness_witness_right",)
    product_script += _cases("hsecond",2)+("cases hsecond_witness_witness","cases hsecond_witness_witness_right",)
    product_script += (f"have hreal : exists R. {_square(*actual[:2],'R')}",)+_call("gaussian_signed_square_exists",*actual[:2])+("cases hreal",)
    product_script += (f"have himag : exists I. {_square(*actual[2:],'I')}",)+_call("gaussian_signed_square_exists",*actual[2:])+("cases himag",)
    product_script += (f"have hcross : ({UV[0]} = {WX[0]}) /\\ ({UV[1]} = {WX[1]})",)+_call("gaussian_signed_product_cross_interchange",*variables)+("cases hcross",)
    product_script += (f"have hscale : ({scaledUV[0]} = 3 * ({UV[0]})) /\\ ({scaledUV[1]} = 3 * ({UV[1]}))",)+_call("eisenstein_signed_product_scaled_right",*U,*V,"3")+("cases hscale",)
    product_script += ("rewrite hcross_left at hscale_left","rewrite hcross_right at hscale_right",)
    product_script += (f"have hnorm : x4 + 3 * x5 = ({values[0]} + {values[1]}) + 3 * ({values[2]} + {values[3]})",)
    product_script += _call("eisenstein_weighted_square_lagrange",*U,*scaledV,*W,*X,*values,"x4","x5")
    product_script += _call("gaussian_signed_square_product",*A,*C,"x","x2")+("exact "+squares[0],"exact "+squares[2],)
    product_script += ("have hscalar : (3 * 3) * (x1 * x3) = (3 * x1) * (3 * x3)","apply mul_shuffle_four","rewrite <- hscalar",)
    product_script += _call("gaussian_signed_square_scaled",*V,"(x1 * x3)","3")
    product_script += _call("gaussian_signed_square_product",*B,*D,"x1","x3")+("exact "+squares[1],"exact "+squares[3],)
    product_script += _call("gaussian_signed_square_product",*A,*D,"x","x3")+("exact "+squares[0],"exact "+squares[3],)
    product_script += _call("gaussian_signed_square_product",*B,*C,"x1","x2")+("exact "+squares[1],"exact "+squares[2],)
    product_script += ("exact hscale_left","exact hscale_right","exact hreal_witness","exact himag_witness",)
    product_script += ("exists x4","exists x5","split","exact hreal_witness","split","exact himag_witness","rewrite hfirst_witness_witness_right_right","rewrite hsecond_witness_witness_right_right",)
    product_script += (f"trans ({values[0]} + {values[1]}) + 3 * ({values[2]} + {values[3]})",_simp(_POLY),"symm","exact hnorm",)
    scaled_product = _pair_mul(("p","n"),(_mul("k","q"),_mul("k","m")))
    ordinary_product = _pair_mul(("p","n"),("q","m"))
    return (
        spec(
            "eisenstein_signed_product_scaled_right",
            f"forall p n q m k. ({scaled_product[0]} = k * ({ordinary_product[0]})) /\\ ({scaled_product[1]} = k * ({ordinary_product[1]}))",
            _POLY,
            _intro("p","n","q","m","k")+("split",_simp(_POLY),_simp(_POLY)),
            "Scaling one genuine signed factor scales both exact natural product components.",
        ),
        spec(
            "eisenstein_weighted_lagrange_compensation",
            "forall su sv sw sx R I P Q p q. P = 3 * p -> Q = 3 * q -> "
            "R + (P + P) = (su + sv) + (Q + Q) -> I + (q + q) = (sw + sx) + (p + p) -> R + 3 * I = (su + sv) + 3 * (sw + sx)",
            ("add_cross_sum_chain","mul_add",*_ADD),
            _intro("su","sv","sw","sx","R","I","P","Q","p","q","hp","hq","hdifference","hsum")
            +("have hscaled : 3 * I + (Q + Q) = 3 * (sw + sx) + (P + P)","rewrite hp","rewrite hp","rewrite hq","rewrite hq",)
            +("trans 3 * (I + (q + q))",_simp(("mul_add",*_ADD)),"trans 3 * ((sw + sx) + (p + p))","congr","refl","exact hsum",_simp(("mul_add",*_ADD)),)
            +_call("add_cross_sum_chain","R","(su + sv)","(P + P)","(Q + Q)","(3 * I)","(3 * (sw + sx))")
            +("exact hdifference","trans 3 * I + (Q + Q)","apply add_comm","trans 3 * (sw + sx) + (P + P)","exact hscaled","apply add_comm"),
            "A weight-three multiple of the summed-square equation cancels the exact difference-square cross terms.",
        ),
        spec(
            "eisenstein_weighted_square_lagrange",
            "forall up un vp vn wp wn xp xn su sv sw sx R I. "
            +" -> ".join(f"({part})" for part in (
                _square("up","un","su"),_square("vp","vn","sv"),_square("wp","wn","sw"),_square("xp","xn","sx"),
                f"{uv[0]} = 3 * ({wx[0]})",f"{uv[1]} = 3 * ({wx[1]})",_square(*real,"R"),_square(*imag,"I"),
            ))+" -> R + 3 * I = (su + sv) + 3 * (sw + sx)",
            ("gaussian_signed_square_difference_compensation","gaussian_signed_square_sum_compensation","eisenstein_weighted_lagrange_compensation"),
            _intro("up","un","vp","vn","wp","wn","xp","xn","su","sv","sw","sx","R","I","hu","hv","hw","hx","hp","hq","hr","hi")
            +(f"have hdifference : R + ({_add(uv[0],uv[0])}) = (su + sv) + ({_add(uv[1],uv[1])})",)
            +_call("gaussian_signed_square_difference_compensation","up","un","vp","vn","su","sv","R")+("exact hu","exact hv","exact hr",)
            +(f"have hsum : I + ({_add(wx[1],wx[1])}) = (sw + sx) + ({_add(wx[0],wx[0])})",)
            +_call("gaussian_signed_square_sum_compensation","wp","wn","xp","xn","sw","sx","I")+("exact hw","exact hx","exact hi",)
            +_call("eisenstein_weighted_lagrange_compensation","su","sv","sw","sx","R","I",*uv,*wx)+("exact hp","exact hq","exact hdifference","exact hsum"),
            "Weighted Lagrange cancellation uses actual scalar squares and exact signed cross-component equations, with no norm oracle.",
        ),
        spec(
            "eisenstein_weighted_norm_product",
            f"forall {' '.join(variables)} N M. ({_weighted(*A,*B,'N','first_product')}) -> ({_weighted(*C,*D,'M','second_product')}) -> ({_weighted(*actual,'N * M','product')})",
            ("gaussian_signed_square_exists","gaussian_signed_square_product","gaussian_signed_square_scaled","gaussian_signed_product_cross_interchange","eisenstein_signed_product_scaled_right","eisenstein_weighted_square_lagrange","mul_shuffle_four",*_POLY),
            product_script,
            "The actual positive weight-three norm is multiplicative under (x,y)(u,v)=(xu−3yv,xv+yu), for all arbitrary signed representatives.",
        ),
    )


def _multiplicative_norm_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    names=tuple("abcdefghijklmnop")
    A,B,C,D=names[:4],names[4:8],names[8:12],names[12:]
    product=_eisenstein_product
    AB=product(A,B)
    BA=product(B,A)
    conjugated=_conjugate(AB)
    conjugate_product=product(_conjugate(A),_conjugate(B))
    commute=_intro(*A,*B)+("split",)
    conjugate=_intro(*A,*B)+("split",)
    for i in (0,2):
        commute+=_commutative_expansion_identity(_add(AB[i],BA[i+1]),_add(BA[i],AB[i+1]))
        conjugate+=_commutative_expansion_identity(_add(conjugated[i],conjugate_product[i+1]),_add(conjugate_product[i],conjugated[i+1]))
    T0=product(product(A,B),product(C,D))
    T1=product(A,product(B,product(C,D)))
    T2=product(A,product(product(B,C),D))
    T3=product(A,product(product(C,B),D))
    T4=product(A,product(C,product(B,D)))
    T5=product(product(A,C),product(B,D))
    step0=_call("eisenstein_product_associate",*A,*B,*product(C,D))
    step1=_call("eisenstein_product_integer_congruence",*A,*A,*product(B,product(C,D)),*product(product(B,C),D))+_call("gaussian_equal_reflexive",*A)
    step1+=_call("gaussian_equal_symmetric",*product(product(B,C),D),*product(B,product(C,D)))+_call("eisenstein_product_associate",*B,*C,*D)
    step2=(f"have hinner : {_complex_equal(product(product(B,C),D),product(product(C,B),D))}",)
    step2+=_call("eisenstein_product_integer_congruence",*product(B,C),*product(C,B),*D,*D)+_call("eisenstein_product_commute",*B,*C)+_call("gaussian_equal_reflexive",*D)
    step2+=_call("eisenstein_product_integer_congruence",*A,*A,*product(product(B,C),D),*product(product(C,B),D))+_call("gaussian_equal_reflexive",*A)+("exact hinner",)
    step3=_call("eisenstein_product_integer_congruence",*A,*A,*product(product(C,B),D),*product(C,product(B,D)))+_call("gaussian_equal_reflexive",*A)+_call("eisenstein_product_associate",*C,*B,*D)
    step4=_call("gaussian_equal_symmetric",*T5,*T4)+_call("eisenstein_product_associate",*A,*C,*product(B,D))
    shuffle=_intro(*names)+_coordinate_chain((T0,T1,T2,T3,T4,T5),(step0,step1,step2,step3,step4),"shuffle")

    self_product=product(conjugated,AB)
    factored=product(conjugate_product,AB)
    grouped=product(product(_conjugate(A),A),product(_conjugate(B),B))
    scalarA,scalarB=("N","0","0","0"),("M","0","0","0")
    scalar_product=product(scalarA,scalarB)
    scalar_result=("N * M","0","0","0")
    norm=_intro(*A,*B,"N","M","hfirst","hsecond")+(f"have hnorm : exists n. ({_norm(*AB,'n')})",)+_call("eisenstein_coordinate_norm_exists",*AB)+("cases hnorm",)
    norm+=(f"have hself : {_complex_equal(self_product,('x','0','0','0'))}",)+_call("eisenstein_conjugate_product_is_norm",*AB,"x")+("exact hnorm_witness",)
    norm+=(f"have hproduct : {_complex_equal(self_product,scalar_result)}",)
    norm0=_call("eisenstein_product_integer_congruence",*conjugated,*conjugate_product,*AB,*AB)+_call("eisenstein_product_conjugate",*A,*B)+_call("gaussian_equal_reflexive",*AB)
    norm1=_call("eisenstein_product_shuffle",*_conjugate(A),*_conjugate(B),*A,*B)
    norm2=_call("eisenstein_product_integer_congruence",*product(_conjugate(A),A),*scalarA,*product(_conjugate(B),B),*scalarB)
    norm2+=_call("eisenstein_conjugate_product_is_norm",*A,"N")+("exact hfirst",)+_call("eisenstein_conjugate_product_is_norm",*B,"M")+("exact hsecond",)
    norm3=("split",_simp(("mul_zero_left","zero_add")),_simp(("mul_zero_left","zero_add")),)
    norm+=_coordinate_chain((self_product,factored,grouped,scalar_product,scalar_result),(norm0,norm1,norm2,norm3),"norm")
    norm+=(f"have hscalar : {_complex_equal(('x','0','0','0'),scalar_result)}",)+_call("gaussian_equal_transitive","x","0","0","0",*self_product,*scalar_result)+_call("gaussian_equal_symmetric",*self_product,"x","0","0","0")+("exact hself","exact hproduct","cases hscalar",)
    norm+=("have hvalue : x = N * M","trans x + 0","symm","apply PA3","trans (N * M) + 0","exact hscalar_left","apply PA3","rewrite <- hvalue","exact hnorm_witness",)
    return (
        spec("eisenstein_product_commute",f"forall {' '.join((*A,*B))}. ({_complex_equal(AB,BA)})",
             tuple(dep for dep in _POLY if dep not in ("add_comm","natural_mul_swap_right_tail")),commute,"Genuine Eisenstein multiplication is commutative on represented integer coordinates."),
        spec("eisenstein_product_conjugate",f"forall {' '.join((*A,*B))}. ({_complex_equal(conjugated,conjugate_product)})",
             ("add_mul","mul_add","mul_assoc",*_ADD),conjugate,"Actual Eisenstein conjugation preserves multiplication for all signed coordinate representatives."),
        spec("eisenstein_product_shuffle",f"forall {' '.join(names)}. ({_complex_equal(T0,T5)})",
             ("gaussian_equal_transitive","gaussian_equal_symmetric","gaussian_equal_reflexive","eisenstein_product_associate","eisenstein_product_integer_congruence","eisenstein_product_commute"),shuffle,
             "The checked commutative Eisenstein product admits four-factor interchange without expanding a quartic polynomial."),
        spec("eisenstein_coordinate_norm_product",f"forall {' '.join((*A,*B))} N M. ({_norm(*A,'N')}) -> ({_norm(*B,'M')}) -> ({_norm(*AB,'N * M')})",
             ("eisenstein_coordinate_norm_exists","eisenstein_conjugate_product_is_norm","gaussian_equal_transitive","eisenstein_product_integer_congruence","eisenstein_product_conjugate","gaussian_equal_reflexive","eisenstein_product_shuffle","gaussian_equal_symmetric","mul_zero_left","zero_add"),norm,
             "The genuine Eisenstein norm is multiplicative, from checked conjugation, commutativity and associativity, without a norm or polynomial oracle."),
    )


def _raw_division(A: tuple[str,...], B: tuple[str,...], Q: tuple[str,...], R: tuple[str,...], U: str, V: str, tag: str) -> str:
    return _and(_complex_equal(_complex_add(_eisenstein_product(B,Q),R),A),_norm(*R,U),_norm(*B,V),_lt(U,V,tag))


def eisenstein_signed_division_remainder_relation(ap: str, an: str, bp: str, bn: str, cp: str, cn: str, dp: str, dn: str, qp: str, qn: str, up: str, un: str, rp: str, rn: str, sp: str, sn: str, remainder_norm: str, divisor_norm: str, *, tag: str, variables: tuple[str,...]) -> str:
    """The exact raw-coordinate Euclidean graph, with actual norm witnesses."""
    values=_public_arguments((ap,an,bp,bn,cp,cn,dp,dn,qp,qn,up,un,rp,rn,sp,sn,remainder_norm,divisor_norm),tag,variables)
    return _raw_division(values[:4],values[4:8],values[8:12],values[12:16],*values[16:],tag)


def _coordinate_floor(p: str, n: str, m: str, qp: str, qn: str, r: str, tag: str) -> str:
    return f"({_add(p,_mul(m,qn))} = {_add(_add(n,_mul(m,qp)),r)} /\\ ({_lt(r,m,tag)}))"


def _division_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B=("a","b","c","d"),("e","f","g","h")
    transformed=_transform(*A)
    zero_script=_intro(*A,"hnorm")+(f"have hweighted : {_weighted(*transformed,'4 * 0','zero')}",)
    zero_script+=_call("eisenstein_norm_to_weighted_norm",*A,"0")+("exact hnorm",)+_cases("hweighted",2)+_parts("hweighted_witness_witness",3)
    zero_script+=("have hsumzero : x + 3 * x1 = 0","trans 4 * 0","symm","exact hweighted_witness_witness_right_right","norm_num",)
    zero_script+=("have hfirstzero : x = 0",)+_call("add_eq_zero_left","x","(3 * x1)")+("exact hsumzero",)
    zero_script+=("have htriplezero : 3 * x1 = 0",)+_call("add_eq_zero_right","x","(3 * x1)")+("exact hsumzero",)
    zero_script+=("have hsecondzero : x1 = 0",)+_call("mul_left_cancel_nonzero","3","x1","0")+("intro hthreezero","apply PA1","exact hthreezero","trans 0","exact htriplezero","symm","apply PA5",)
    zero_script+=("have himaginary : c = d","have hsquareiff : (x1 = 0 -> c = d) /\\ (c = d -> x1 = 0)",)
    zero_script+=_call("gaussian_signed_square_zero_iff",*A[2:],"x1")+("exact hweighted_witness_witness_right_left","cases hsquareiff","apply hsquareiff_left","exact hsecondzero",)
    zero_script+=(f"have htransformed : {transformed[0]} = {transformed[1]}",f"have hsquareiff : (x = 0 -> {transformed[0]} = {transformed[1]}) /\\ ({transformed[0]} = {transformed[1]} -> x = 0)",)
    zero_script+=_call("gaussian_signed_square_zero_iff",*transformed[:2],"x")+("exact hweighted_witness_witness_left","cases hsquareiff","apply hsquareiff_left","exact hfirstzero","split",)
    zero_script+=_call("mul_left_cancel_nonzero","2","a","b")+("intro htwozero","apply PA1","exact htwozero",)
    zero_script+=_call("add_right_cancel","(2 * a)","(2 * b)","d")+("trans 2 * b + c","exact htransformed","rewrite himaginary","refl","exact himaginary",)

    numerator=_eisenstein_product(_conjugate(B),A)
    Q=("x1","x2","x4","x5")
    error=("x3","0","x6","0")
    R=_complex_difference(A,_eisenstein_product(B,Q))
    error_expression=_complex_difference(numerator,_scale("x",Q))
    conjugate_residual=_eisenstein_product(_conjugate(B),R)
    script=_intro(*A,*B,"hnonzero")
    script+=(f"have hdivisor : exists N. ({_norm(*B,'N')})",)+_call("eisenstein_coordinate_norm_exists",*B)+("cases hdivisor",)
    script+=("have hN : ~(x = 0)","intro hzero",)+_call("eisenstein_coordinate_norm_nonzero",*B,"x")+("exact hdivisor_witness","exact hnonzero","exact hzero",)
    script+=(f"have hreal : exists qp qn r. {_coordinate_floor(*numerator[:2],'x','qp','qn','r','real_floor')}",)
    script+=_call("signed_integer_floor_exists",*numerator[:2],"x")+("exact hN",)+_cases("hreal",3)+("cases hreal_witness_witness_witness",)
    script+=(f"have himaginary : exists qp qn r. {_coordinate_floor(*numerator[2:],'x','qp','qn','r','imaginary_floor')}",)
    script+=_call("signed_integer_floor_exists",*numerator[2:],"x")+("exact hN",)+_cases("himaginary",3)+("cases himaginary_witness_witness_witness",)
    script+=(f"have hremainder : exists M. ({_norm(*R,'M')})",)+_call("eisenstein_coordinate_norm_exists",*R)+("cases hremainder",)
    script+=(f"have herror : exists M. ({_natural_norm('x3','x6','M')})",)+_call("eisenstein_natural_norm_exists","x3","x6")+("cases herror",)
    script+=(f"have herrornorm : {_norm(*error,'x8')}",)+_call("eisenstein_natural_norm_coordinates","x3","x6","x8")+("exact herror_witness",)
    script+=(f"have herror_equation : {_complex_equal(error_expression,error)}","split",)
    for index,hyp in ((0,"hreal_witness_witness_witness_left"),(2,"himaginary_witness_witness_witness_left")):
        script+=(f"trans {error_expression[index]}","apply PA3",f"trans {_add(error_expression[index+1],error[index])}",f"exact {hyp}","apply add_comm",)
    script+=(f"have hconjugate_error : {_complex_equal(conjugate_residual,error)}",)
    script+=_call("gaussian_equal_transitive",*conjugate_residual,*error_expression,*error)
    script+=_call("eisenstein_residual_conjugate_identity",*A,*B,*Q,"x")+("exact hdivisor_witness","exact herror_equation",)
    script+=(f"have hproduct_norm : {_norm(*conjugate_residual,'x * x7')}",)
    script+=_call("eisenstein_coordinate_norm_product",*_conjugate(B),*R,"x","x7")+_call("eisenstein_coordinate_norm_conjugate",*B,"x")+("exact hdivisor_witness","exact hremainder_witness",)
    script+=(f"have htransported : {_norm(*error,'x * x7')}",)+_call("eisenstein_coordinate_norm_transport",*conjugate_residual,*error,"(x * x7)")+("cases hconjugate_error","exact hconjugate_error_left","cases hconjugate_error","exact hconjugate_error_right","exact hproduct_norm",)
    script+=("have hnormequation : x * x7 = x8",)+_call("eisenstein_coordinate_norm_functional",*error,"(x * x7)","x8")+("exact htransported","exact herrornorm",)
    script+=(f"have hstrict : {_lt('x8','x * x','error_strict')}",)+_call("eisenstein_parallelogram_norm_strict","x3","x6","x","x8")+("exact hreal_witness_witness_witness_right","exact himaginary_witness_witness_witness_right","exact herror_witness",)
    script+=tuple(f"exists {value}" for value in (*Q,*R,"x7","x"))+("split",)+_call("gaussian_difference_reconstructs_dividend",*A,*_eisenstein_product(B,Q))+("split","exact hremainder_witness","split","exact hdivisor_witness",)
    script+=_call("four_square_descent_norm_bound_forces_smaller_multiplier","x","x7","x8")+("exact hnormequation","exact hstrict",)
    Qvars,Rvars=("qp","qn","up","un"),("rp","rn","sp","sn")
    return (
        spec("eisenstein_coordinate_norm_zero",f"forall {' '.join(A)}. ({_norm(*A,'0')}) -> a = b /\\ c = d",
             ("eisenstein_norm_to_weighted_norm","add_eq_zero_left","add_eq_zero_right","mul_left_cancel_nonzero","gaussian_signed_square_zero_iff","add_right_cancel"),zero_script,
             "A genuine Eisenstein norm can be zero only when both represented integer coordinates are zero, with no sign-normality or positivity hypothesis."),
        spec("eisenstein_coordinate_norm_nonzero",f"forall {' '.join(A)} N. ({_norm(*A,'N')}) -> ~(a = b /\\ c = d) -> ~(N = 0)",
             ("eisenstein_coordinate_norm_zero",),_intro(*A,"N","hnorm","hnonzero","hzero")+("apply hnonzero",)+_call("eisenstein_coordinate_norm_zero",*A)+("rewrite hzero at hnorm","exact hnorm",),
             "Every nonzero represented Eisenstein integer has a strictly positive natural norm."),
        spec("eisenstein_natural_norm_coordinates",f"forall a b N. ({_natural_norm('a','b','N')}) -> ({_norm('a','0','b','0','N')})",
             ("mul_zero_left","zero_add"),_intro("a","b","N","hnorm")+(_simp(("mul_zero_left","zero_add")),),
             "The natural fundamental-parallelogram norm is exactly the signed-coordinate norm of the same nonnegative integers."),
        spec("eisenstein_signed_euclidean_division_exists",f"forall {' '.join((*A,*B))}. ~(e = f /\\ g = h) -> exists {' '.join((*Qvars,*Rvars,'U','V'))}. ({_raw_division(A,B,Qvars,Rvars,'U','V','full_signed_division')})",
             ("eisenstein_coordinate_norm_exists","eisenstein_coordinate_norm_nonzero","signed_integer_floor_exists","eisenstein_natural_norm_exists","eisenstein_natural_norm_coordinates","gaussian_equal_transitive","eisenstein_residual_conjugate_identity","eisenstein_coordinate_norm_product","eisenstein_coordinate_norm_conjugate","eisenstein_coordinate_norm_transport","eisenstein_coordinate_norm_functional","eisenstein_parallelogram_norm_strict","gaussian_difference_reconstructs_dividend","four_square_descent_norm_bound_forces_smaller_multiplier","add_comm"),script,
             "Construct a genuine Eisenstein quotient and remainder for every nonzero signed divisor, with exact a=bq+r and strict actual norm decrease; neither quotient, norm existence, nor a bound is supplied as a premise."),
    )


def _coded_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B=("a","b","c","d"),("e","f","g","h")
    X,Y=("x","x1","x2","x3"),("x4","x5","x6","x7")
    exists=lambda *values: tuple(f"exists {value}" for value in values)
    norm_for_rep=_intro("z",*A,"N","hrep","hnorm")+_cases("hnorm",4)+("cases hnorm_witness_witness_witness_witness",)
    norm_for_rep+=(f"have hequal : {_complex_equal(X,A)}",)+_call("gaussian_representation_equal","z",*X,*A)+("exact hnorm_witness_witness_witness_witness_left","exact hrep","cases hequal",)
    norm_for_rep+=_call("eisenstein_coordinate_norm_transport",*X,*A,"N")+("exact hequal_left","exact hequal_right","exact hnorm_witness_witness_witness_witness_right",)
    norm_exists=_intro("z","hvalid")+_cases("hvalid",4)+(f"have hnorm : exists N. ({_norm(*X,'N')})",)+_call("eisenstein_coordinate_norm_exists",*X)+("cases hnorm","exists x4",)
    norm_exists+=_call("eisenstein_norm_of_representation","z",*X,"x4")+_call("gaussian_decode_representation","z",*X)+("exact hvalid_witness_witness_witness_witness","exact hnorm_witness",)
    norm_unique=_intro("z","N","M","hfirst","hsecond")+_cases("hfirst",4)+("cases hfirst_witness_witness_witness_witness",)
    norm_unique+=_call("eisenstein_coordinate_norm_functional",*X,"N","M")+("exact hfirst_witness_witness_witness_witness_right",)+_call("eisenstein_norm_for_representation","z",*X,"M")+("exact hfirst_witness_witness_witness_witness_left","exact hsecond",)
    unique_norm=_and(_code_norm("z","N","unique_witness"),f"forall M. ({_code_norm('z','M','unique_compare')}) -> M = N")
    rows=[
        spec("eisenstein_norm_of_representation",f"forall z {' '.join(A)} N. ({_rep('z',*A,'norm_intro_rep')}) -> ({_norm(*A,'N')}) -> ({_code_norm('z','N','norm_intro_code')})",
             (),_intro("z",*A,"N","hrep","hnorm")+exists(*A)+("split","exact hrep","exact hnorm"),
             "Actual signed coordinates and their actual norm construct the canonical Eisenstein norm graph."),
        spec("eisenstein_norm_for_representation",f"forall z {' '.join(A)} N. ({_rep('z',*A,'norm_fixed_rep')}) -> ({_code_norm('z','N','norm_fixed_code')}) -> ({_norm(*A,'N')})",
             ("gaussian_representation_equal","eisenstein_coordinate_norm_transport"),norm_for_rep,
             "The canonical Eisenstein norm equals the actual norm of every representative of the same pair of integers."),
        spec("eisenstein_norm_exists",f"forall z. ({_gaussian('z','norm_input')}) -> exists N. ({_code_norm('z','N','norm_output')})",
             ("eisenstein_coordinate_norm_exists","eisenstein_norm_of_representation","gaussian_decode_representation"),norm_exists,
             "Every canonical Eisenstein integer has a genuinely constructed natural norm, including zero and all units."),
        spec("eisenstein_norm_functional",f"forall z N M. ({_code_norm('z','N','norm_first')}) -> ({_code_norm('z','M','norm_second')}) -> N = M",
             ("eisenstein_coordinate_norm_functional","eisenstein_norm_for_representation"),norm_unique,
             "The canonical natural Eisenstein norm is unique, independently of all signed-coordinate representatives."),
        spec("eisenstein_norm_exists_unique",f"forall z. ({_gaussian('z','norm_unique_input')}) -> exists N. ({unique_norm})",
             ("eisenstein_norm_exists","eisenstein_norm_functional"),_intro("z","hvalid")+(f"have hnorm : exists N. ({_code_norm('z','N','norm_unique_construct')})",)+_call("eisenstein_norm_exists","z")+("exact hvalid","cases hnorm","exists x","split","exact hnorm_witness","intro M","intro hother",)+_call("eisenstein_norm_functional","z","M","x")+("exact hother","exact hnorm_witness",),
             "Every valid canonical Eisenstein code has one actually computed and uniquely determined natural norm."),
        spec("eisenstein_add_exists",f"forall ac bc. ({_gaussian('ac','add_first')}) -> ({_gaussian('bc','add_second')}) -> exists cc. ({_code_add('ac','bc','cc','add_output')})",
             ("gaussian_add_exists",),("exact gaussian_add_exists",),
             "Eisenstein addition is exactly the shared neutral ZPair addition, with its already-checked constructive existence theorem."),
        spec("eisenstein_add_functional",f"forall ac bc cc dd. ({_code_add('ac','bc','cc','add_unique_first')}) -> ({_code_add('ac','bc','dd','add_unique_second')}) -> cc = dd",
             ("gaussian_add_functional",),("exact gaussian_add_functional",),
             "The same canonical ZPair addition has one literal output code in the Eisenstein presentation; no duplicate additive definition is introduced."),
    ]
    product=_eisenstein_product(A,B)
    raw_product=_eisenstein_product(X,Y)
    fixed=_intro("ac","bc","cc",*A,*B,"hfirst","hsecond","hoperation")+_cases("hoperation",8)+_parts("hoperation"+"_witness"*8,3)
    fixed+=_call("gaussian_representation_integer_transport","cc",*raw_product,*product)+_call("eisenstein_product_integer_congruence",*X,*A,*Y,*B)
    fixed+=_call("gaussian_representation_equal","ac",*X,*A)+(f"exact {_part('hoperation'+'_witness'*8,3,0)}","exact hfirst",)
    fixed+=_call("gaussian_representation_equal","bc",*Y,*B)+(f"exact {_part('hoperation'+'_witness'*8,3,1)}","exact hsecond",f"exact {_part('hoperation'+'_witness'*8,3,2)}",)
    multiply_exists=_intro("ac","bc","hfirst","hsecond")+_cases("hfirst",4)+_cases("hsecond",4)
    multiply_exists+=(f"have houtput : exists cc. ({_rep('cc',*raw_product,'multiply_construct_output')})",)+_call("gaussian_representation_exists",*raw_product)+("cases houtput","exists x8",)
    multiply_exists+=_call("eisenstein_multiply_of_representations","ac","bc","x8",*X,*Y)+_call("gaussian_decode_representation","ac",*X)+("exact hfirst_witness_witness_witness_witness",)+_call("gaussian_decode_representation","bc",*Y)+("exact hsecond_witness_witness_witness_witness","exact houtput_witness",)
    multiply_unique=_intro("ac","bc","cc","dd","hfirst","hsecond")+_cases("hfirst",8)+_parts("hfirst"+"_witness"*8,3)
    multiply_unique+=_call("gaussian_representation_functional","cc","dd",*raw_product)+(f"exact {_part('hfirst'+'_witness'*8,3,2)}",)+_call("eisenstein_multiply_for_representations","ac","bc","dd",*X,*Y)+(f"exact {_part('hfirst'+'_witness'*8,3,0)}",f"exact {_part('hfirst'+'_witness'*8,3,1)}","exact hsecond",)
    norm_multiply=_intro("ac","bc","cc","N","M","hfirst","hsecond","hproduct")+_cases("hproduct",8)+_parts("hproduct"+"_witness"*8,3)
    norm_multiply+=_call("eisenstein_norm_of_representation","cc",*raw_product,"N * M")+(f"exact {_part('hproduct'+'_witness'*8,3,2)}",)
    norm_multiply+=_call("eisenstein_coordinate_norm_product",*X,*Y,"N","M")+_call("eisenstein_norm_for_representation","ac",*X,"N")+(f"exact {_part('hproduct'+'_witness'*8,3,0)}","exact hfirst",)+_call("eisenstein_norm_for_representation","bc",*Y,"M")+(f"exact {_part('hproduct'+'_witness'*8,3,1)}","exact hsecond",)
    rows.extend((
        spec("eisenstein_multiply_of_representations",f"forall ac bc cc {' '.join((*A,*B))}. ({_rep('ac',*A,'multiply_intro_first')}) -> ({_rep('bc',*B,'multiply_intro_second')}) -> ({_rep('cc',*product,'multiply_intro_output')}) -> ({_code_mul('ac','bc','cc','multiply_intro_graph')})",
             (),_intro("ac","bc","cc",*A,*B,"hfirst","hsecond","houtput")+exists(*A,*B)+("split","exact hfirst","split","exact hsecond","exact houtput",),
             "The genuine signed-coordinate Eisenstein product constructs the exact canonical multiplication graph."),
        spec("eisenstein_multiply_for_representations",f"forall ac bc cc {' '.join((*A,*B))}. ({_rep('ac',*A,'multiply_fixed_first')}) -> ({_rep('bc',*B,'multiply_fixed_second')}) -> ({_code_mul('ac','bc','cc','multiply_fixed_graph')}) -> ({_rep('cc',*product,'multiply_fixed_output')})",
             ("gaussian_representation_integer_transport","eisenstein_product_integer_congruence","gaussian_representation_equal"),fixed,
             "Every witness of canonical Eisenstein multiplication represents the same actual product of any chosen integer representatives."),
        spec("eisenstein_multiply_exists",f"forall ac bc. ({_gaussian('ac','multiply_total_first')}) -> ({_gaussian('bc','multiply_total_second')}) -> exists cc. ({_code_mul('ac','bc','cc','multiply_total_output')})",
             ("gaussian_representation_exists","eisenstein_multiply_of_representations","gaussian_decode_representation"),multiply_exists,
             "Construct the actual canonical Eisenstein product of every two valid signed-coordinate codes."),
        spec("eisenstein_multiply_functional",f"forall ac bc cc dd. ({_code_mul('ac','bc','cc','multiply_unique_first')}) -> ({_code_mul('ac','bc','dd','multiply_unique_second')}) -> cc = dd",
             ("gaussian_representation_functional","eisenstein_multiply_for_representations"),multiply_unique,
             "Eisenstein multiplication has one literal canonical output code, not merely equivalent signed representatives."),
        spec("eisenstein_norm_multiply",f"forall ac bc cc N M. ({_code_norm('ac','N','norm_product_first')}) -> ({_code_norm('bc','M','norm_product_second')}) -> ({_code_mul('ac','bc','cc','norm_product_operation')}) -> ({_code_norm('cc','N * M','norm_product_output')})",
             ("eisenstein_norm_of_representation","eisenstein_coordinate_norm_product","eisenstein_norm_for_representation"),norm_multiply,
             "The actual canonical Eisenstein norm of a product is exactly the product of the two actual natural norms."),
    ))

    Q,R=("i","j","k","l"),("o","p","s","t")
    product=_eisenstein_product(B,Q)
    reconstruction=_complex_add(product,R)
    reconstruction_script=_intro("ac","bc","qc","rc",*A,*B,*Q,*R,"hfirst","hsecond","hquotient","hremainder","hequation")
    reconstruction_script+=(f"have hproduct : exists pc. ({_rep('pc',*product,'division_product_construct')})",)+_call("gaussian_representation_exists",*product)+("cases hproduct","exists x","split",)
    reconstruction_script+=_call("eisenstein_multiply_of_representations","bc","qc","x",*B,*Q)+("exact hsecond","exact hquotient","exact hproduct_witness",)
    reconstruction_script+=_call("gaussian_add_of_representations","x","rc","ac",*product,*R)+("exact hproduct_witness","exact hremainder",)
    reconstruction_script+=_call("gaussian_representation_integer_transport","ac",*A,*reconstruction)+_call("gaussian_equal_symmetric",*reconstruction,*A)+("exact hequation","exact hfirst",)
    quotient,remainder=("x8","x9","x10","x11"),("x12","x13","x14","x15")
    raw_name="hdivision"+"_witness"*10
    script=_intro("ac","bc","hfirst","hsecond","hnonzero")+_cases("hfirst",4)+_cases("hsecond",4)
    script+=(f"have hA : {_rep('ac',*X,'euclidean_dividend_rep')}",)+_call("gaussian_decode_representation","ac",*X)+("exact hfirst_witness_witness_witness_witness",)
    script+=(f"have hB : {_rep('bc',*Y,'euclidean_divisor_rep')}",)+_call("gaussian_decode_representation","bc",*Y)+("exact hsecond_witness_witness_witness_witness",)
    script+=("have hzero : (bc = 0 -> (x4 = x5 /\\ x6 = x7)) /\\ ((x4 = x5 /\\ x6 = x7) -> bc = 0)",)+_call("gaussian_representation_zero_iff","bc",*Y)+("exact hB","cases hzero","have hraw_nonzero : ~(x4 = x5 /\\ x6 = x7)","intro hvanishing","apply hnonzero","apply hzero_right","exact hvanishing",)
    script+=(f"have hdivision : exists {' '.join((*Q,*R,'U','V'))}. ({_raw_division(X,Y,Q,R,'U','V','euclidean_raw_construct')})",)+_call("eisenstein_signed_euclidean_division_exists",*X,*Y)+("exact hraw_nonzero",)+_cases("hdivision",10)+_parts(raw_name,4)
    script+=(f"have hQ : exists qc. ({_rep('qc',*quotient,'euclidean_quotient_construct')})",)+_call("gaussian_representation_exists",*quotient)+("cases hQ",)
    script+=(f"have hR : exists rc. ({_rep('rc',*remainder,'euclidean_remainder_construct')})",)+_call("gaussian_representation_exists",*remainder)+("cases hR",)
    script+=exists("x18","x19","x16","x17")+("split",)
    script+=_call("eisenstein_division_remainder_of_representations","ac","bc","x18","x19",*X,*Y,*quotient,*remainder)+("exact hA","exact hB","exact hQ_witness","exact hR_witness",f"exact {_part(raw_name,4,0)}","split",)
    script+=_call("eisenstein_norm_of_representation","x19",*remainder,"x16")+("exact hR_witness",f"exact {_part(raw_name,4,1)}","split",)
    script+=_call("eisenstein_norm_of_representation","bc",*Y,"x17")+("exact hB",f"exact {_part(raw_name,4,2)}",f"exact {_part(raw_name,4,3)}",)
    rows.extend((
        spec("eisenstein_division_remainder_of_representations",f"forall ac bc qc rc {' '.join((*A,*B,*Q,*R))}. ({_rep('ac',*A,'equation_first_rep')}) -> ({_rep('bc',*B,'equation_second_rep')}) -> ({_rep('qc',*Q,'equation_quotient_rep')}) -> ({_rep('rc',*R,'equation_remainder_rep')}) -> ({_complex_equal(reconstruction,A)}) -> ({_code_divrem('ac','bc','qc','rc','equation_code_graph')})",
             ("gaussian_representation_exists","eisenstein_multiply_of_representations","gaussian_add_of_representations","gaussian_representation_integer_transport","gaussian_equal_symmetric"),reconstruction_script,
             "An actual signed-coordinate a=bq+r equation constructs the genuine canonical Eisenstein product-and-sum graph."),
        spec("eisenstein_euclidean_division_exists",f"forall ac bc. ({_gaussian('ac','euclidean_input_dividend')}) -> ({_gaussian('bc','euclidean_input_divisor')}) -> ~(bc = 0) -> exists qc rc U V. ({_code_euclidean('ac','bc','qc','rc','U','V','euclidean_canonical_output')})",
             ("gaussian_decode_representation","gaussian_representation_zero_iff","eisenstein_signed_euclidean_division_exists","gaussian_representation_exists","eisenstein_division_remainder_of_representations","eisenstein_norm_of_representation"),script,
             "Full constructive Eisenstein Euclidean division: every canonical dividend and nonzero canonical divisor produce actual canonical quotient and remainder, an exact a=bq+r equation, and strict decrease of their actual norms a²-ab+b²."),
    ))
    return tuple(rows)


__all__ = [
    "eisenstein_coordinate_norm_relation","eisenstein_coordinate_product_relation",
    "eisenstein_integer_relation","eisenstein_add_relation","eisenstein_norm_relation",
    "eisenstein_multiply_relation","eisenstein_division_remainder_relation",
    "eisenstein_euclidean_division_relation","eisenstein_signed_division_remainder_relation",
    "make_eisenstein_euclidean_candidate_theorems",
]
