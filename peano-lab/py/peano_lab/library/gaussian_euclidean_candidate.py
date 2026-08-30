"""Unsealed constructive Gaussian Euclidean arithmetic in the original HA language.

Signed coordinates are genuine differences of naturals.  Public code surfaces
reuse the historic canonical signed decoder and injective natural pairing.
Every definition is a conservative abbreviation; the scripts below still need
their entire dependency closure checked before any Alpha admission.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from ..kernel.terms import Add, Mul, Succ, Var, Zero, parse_term_with_names
from .finite_fold_surface import _identifier
from .ha_signed_decode_candidate import signed_decode
from .ha_signed_add_candidate import signed_add
from .ha_signed_mul_candidate import signed_mul
from .four_square_descent_candidate import centered_signed_remainder
from .four_square_euler_candidate import _permute_addends, _right_group


def _args(*values: str) -> tuple[str, ...]:
    values = tuple(_identifier(value, "Gaussian argument") for value in values)
    if len(set(values)) != len(values):
        raise ValueError("Gaussian arguments must be distinct identifiers")
    if any(value.startswith(("ge_", "sd_", "sb_", "sif_")) for value in values):
        raise ValueError("Gaussian argument captures a generated binder")
    return values


def _names(tag: str, *stems: str) -> tuple[str, ...]:
    tag = _identifier(tag, "Gaussian binder tag")
    return tuple(f"ge_{stem}_{tag}" for stem in stems)


def _and(*parts: str) -> str:
    result = f"({parts[-1]})"
    for part in reversed(parts[:-1]):
        result = f"(({part}) /\\ {result})"
    return result


def _le(a: str, b: str, tag: str) -> str:
    gap, = _names(tag, "gap")
    return f"exists {gap}. {gap} + ({a}) = ({b})"


def _lt(a: str, b: str, tag: str) -> str:
    gap, = _names(tag, "gap")
    return f"exists {gap}. {gap} + S ({a}) = ({b})"


def _add(a: str, b: str) -> str:
    return f"(({a}) + ({b}))"


def _mul(a: str, b: str) -> str:
    return f"(({a}) * ({b}))"


def _positive(p: str, n: str) -> str:
    return _add(_mul(p,p),_mul(n,n))


def _negative(p: str, n: str) -> str:
    return _add(_mul(p,n),_mul(n,p))


def _square(p: str, n: str, value: str) -> str:
    return f"{_positive(p,n)} = {_add(value,_negative(p,n))}"


def signed_difference_square_relation(positive: str, negative: str, value: str) -> str:
    """The actual nonnegative square (positive-negative)^2, without subtraction."""
    return _square(*_args(positive,negative,value))


def _norm(p: str, n: str, q: str, m: str, value: str, tag: str) -> str:
    u,v = _names(tag,"real_square","imaginary_square")
    return f"exists {u} {v}. " + _and(_square(p,n,u),_square(q,m,v),f"({value}) = {u} + {v}")


def gaussian_signed_norm_relation(real_positive: str, real_negative: str, imaginary_positive: str, imaginary_negative: str, value: str, *, tag: str) -> str:
    """Actual squared complex modulus, invariant under signed representatives."""
    return _norm(*_args(real_positive,real_negative,imaginary_positive,imaginary_negative,value),_identifier(tag,"Gaussian norm tag"))


def _product(p: str, n: str, q: str, m: str) -> tuple[str,str]:
    return _add(_mul(p,q),_mul(n,m)),_add(_mul(p,m),_mul(n,q))


def _equal(p: str, n: str, q: str, m: str) -> str:
    return f"{_add(p,m)} = {_add(q,n)}"


def _complex_product(first: tuple[str,str,str,str], second: tuple[str,str,str,str]) -> tuple[str,str,str,str]:
    p,n,q,m = first
    u,v,w,x = second
    ac,bd,ad,bc = _product(p,n,u,v),_product(q,m,w,x),_product(p,n,w,x),_product(q,m,u,v)
    return _add(ac[0],bd[1]),_add(ac[1],bd[0]),_add(ad[0],bc[0]),_add(ad[1],bc[1])


def _complex_equal(first: tuple[str,...], second: tuple[str,...]) -> str:
    return _and(_equal(*first[:2],*second[:2]),_equal(*first[2:],*second[2:]))


def _complex_add(first: tuple[str,...], second: tuple[str,...]) -> tuple[str,...]:
    return tuple(_add(a,b) for a,b in zip(first,second,strict=True))


def _complex_difference(first: tuple[str,...], second: tuple[str,...]) -> tuple[str,...]:
    return _complex_add(first,(second[1],second[0],second[3],second[2]))


def _conjugate(value: tuple[str,...]) -> tuple[str,...]:
    return value[0],value[1],value[3],value[2]


def _scale(scalar: str, value: tuple[str,...]) -> tuple[str,...]:
    return tuple(_mul(scalar,part) for part in value)


def _pair(real: str, imaginary: str) -> str:
    return f"(({real}) + ({imaginary})) * S (({real}) + ({imaginary})) + (({imaginary}) + ({imaginary}))"


def _sd(code: str, p: str, n: str, tag: str) -> str:
    """Term-valued internal expansion of the unchanged historic SignedDecode."""
    half, = _names(tag,'signed_half')
    return f"((({code}) = 2 * ({p}) /\\ ({n}) = 0) \\/ exists {half}. ((({code}) = 2 * {half} + 1 /\\ ({p}) = 0) /\\ ({n}) = S {half}))"


def _balance(code: str, p: str, n: str, tag: str) -> str:
    pos,neg=_names(tag,'balance_positive','balance_negative')
    return f"exists {pos} {neg}. "+_and(_sd(code,pos,neg,tag+'decode'),f"({p}) + {neg} = ({n}) + {pos}")


def _decode(code: str, p: str, n: str, q: str, m: str, tag: str) -> str:
    real,imag = _names(tag,"real_code","imaginary_code")
    return f"exists {real} {imag}. " + _and(
        f"({code}) = {_pair(real,imag)}",
        _sd(real,p,n,tag=f"ge_{tag}_real"),
        _sd(imag,q,m,tag=f"ge_{tag}_imaginary"),
    )


def gaussian_decode_relation(code: str, real_positive: str, real_negative: str, imaginary_positive: str, imaginary_negative: str, *, tag: str) -> str:
    """The canonical natural pairing of two historic normalized signed codes."""
    return _decode(*_args(code,real_positive,real_negative,imaginary_positive,imaginary_negative),_identifier(tag,"Gaussian decode tag"))


def _gaussian(code: str, tag: str) -> str:
    p,n,q,m = _names(tag,"real_positive","real_negative","imaginary_positive","imaginary_negative")
    return f"exists {p} {n} {q} {m}. ({_decode(code,p,n,q,m,tag+'decode')})"


def gaussian_integer_relation(code: str, *, tag: str) -> str:
    """A genuine canonical Gaussian integer code; not every natural is a pair code."""
    return _gaussian(*_args(code),_identifier(tag,"Gaussian integer tag"))


def _rep(code: str, p: str, n: str, q: str, m: str, tag: str) -> str:
    real,imag=_names(tag,'representation_real_code','representation_imaginary_code')
    return f"exists {real} {imag}. "+_and(f"({code}) = {_pair(real,imag)}",_balance(real,p,n,tag+'real'),_balance(imag,q,m,tag+'imaginary'))


def gaussian_representation_relation(code: str, real_positive: str, real_negative: str, imaginary_positive: str, imaginary_negative: str, *, tag: str) -> str:
    """A canonical code represents arbitrary, possibly overlapping signed coordinates."""
    return _rep(*_args(code,real_positive,real_negative,imaginary_positive,imaginary_negative),_identifier(tag,'Gaussian representation tag'))


def _code_norm(code: str, value: str, tag: str) -> str:
    coords=_names(tag,'norm_rp','norm_rn','norm_ip','norm_in')
    return f"exists {' '.join(coords)}. "+_and(_rep(code,*coords,tag+'representation'),_norm(*coords,value,tag+'square'))


def gaussian_norm_relation(code: str, value: str, *, tag: str) -> str:
    """Actual squared norm of a canonical Gaussian integer, including zero."""
    return _code_norm(*_args(code,value),_identifier(tag,'Gaussian norm tag'))


def _code_operation(first: str, second: str, output: str, tag: str, *, multiply: bool) -> str:
    A=_names(tag,'first_rp','first_rn','first_ip','first_in')
    B=_names(tag,'second_rp','second_rn','second_ip','second_in')
    result=_complex_product(A,B) if multiply else _complex_add(A,B)
    return f"exists {' '.join((*A,*B))}. "+_and(_rep(first,*A,tag+'first'),_rep(second,*B,tag+'second'),_rep(output,*result,tag+'output'))


def _code_add(first: str, second: str, output: str, tag: str) -> str:
    return _code_operation(first,second,output,tag,multiply=False)


def gaussian_add_relation(first: str, second: str, output: str, *, tag: str) -> str:
    """The actual sum in the canonical signed-coordinate Gaussian carrier."""
    return _code_add(*_args(first,second,output),_identifier(tag,'Gaussian addition tag'))


def _code_mul(first: str, second: str, output: str, tag: str) -> str:
    return _code_operation(first,second,output,tag,multiply=True)


def gaussian_multiply_relation(first: str, second: str, output: str, *, tag: str) -> str:
    """The actual Gaussian product (ac-bd)+(ad+bc)i, not component multiplication."""
    return _code_mul(*_args(first,second,output),_identifier(tag,'Gaussian multiplication tag'))


def _code_divrem(dividend: str, divisor: str, quotient: str, remainder: str, tag: str) -> str:
    product,=_names(tag,'division_product')
    return f"exists {product}. "+_and(_code_mul(divisor,quotient,product,tag+'product'),_code_add(product,remainder,dividend,tag+'sum'))


def gaussian_division_remainder_relation(dividend: str, divisor: str, quotient: str, remainder: str, *, tag: str) -> str:
    """Exact canonical Gaussian equation dividend=divisor*quotient+remainder."""
    return _code_divrem(*_args(dividend,divisor,quotient,remainder),_identifier(tag,'Gaussian division equation tag'))


def _code_euclidean(dividend: str, divisor: str, quotient: str, remainder: str, remainder_norm: str, divisor_norm: str, tag: str) -> str:
    return _and(_gaussian(quotient,tag+'quotient'),_gaussian(remainder,tag+'remainder'),_code_divrem(dividend,divisor,quotient,remainder,tag+'equation'),_code_norm(remainder,remainder_norm,tag+'smallnorm'),_code_norm(divisor,divisor_norm,tag+'largenorm'),_lt(remainder_norm,divisor_norm,tag+'strict'))


def gaussian_euclidean_division_relation(dividend: str, divisor: str, quotient: str, remainder: str, remainder_norm: str, divisor_norm: str, *, tag: str) -> str:
    """Actual canonical quotient/remainder witnesses with their strict norm decrease."""
    return _code_euclidean(*_args(dividend,divisor,quotient,remainder,remainder_norm,divisor_norm),_identifier(tag,'Gaussian Euclidean division tag'))


def _intro(*names: str) -> tuple[str,...]:
    return tuple(f"intro {name}" for name in names)


def _call(name: str, *arguments: str) -> tuple[str,...]:
    return tuple(f"specialize {name} {argument}" for argument in arguments)+(f"apply {name}",)


def _cases(name: str, count: int) -> tuple[str,...]:
    return tuple("cases "+name+"_witness"*i for i in range(count))


def _parts(name: str, count: int) -> tuple[str,...]:
    return tuple("cases "+name+"_right"*i for i in range(count-1))


def _part(name: str, count: int, index: int) -> str:
    return name+"_right"*index+("_left" if index<count-1 else "")


def _exists(*values: str) -> tuple[str,...]:
    return tuple(f"exists {value}" for value in values)


def _rewrite(equation: str, variable: str, formula: str, *, at: str = "") -> tuple[str,...]:
    count = len(re.findall(r"(?<![A-Za-z0-9_'])"+re.escape(variable)+r"(?![A-Za-z0-9_'])",formula))
    return tuple(f"rewrite {equation}"+(f" at {at}" if at else "") for _ in range(count))


_AC = ("add_assoc","add_comm","four_square_add_swap_right_tail")
_POLY = ("add_mul","mul_add","mul_assoc","mul_comm",*_AC,"natural_mul_swap_right_tail")


def _simp(*rules: str) -> tuple[str,...]:
    return ("simp ["+", ".join(rules)+"]",)


def _ordered_monomials(expression: str) -> tuple[tuple[str,...],...]:
    """Untrusted finite expansion guide; no equality is accepted from this computation."""
    term,names=parse_term_with_names(expression)
    def bounded(values):
        values=tuple((coefficient,factors) for coefficient,factors in values if coefficient)
        if sum(coefficient for coefficient,_ in values)>64 or any(len(factors)>8 for _,factors in values):
            raise ValueError('the Gaussian expansion guide exceeded its 64-monomial/degree-eight authoring budget')
        return values
    def expand(node):
        literal=node
        coefficient=0
        while type(literal) is Succ:
            coefficient+=1
            literal=literal.term
        if type(literal) is Zero:
            return bounded(((coefficient,()),))
        if type(node) is Var:
            return ((1,(names[node.index],)),)
        if type(node) is Succ:
            return bounded(expand(node.term)+((1,()),))
        if type(node) is Add:
            return bounded(expand(node.left)+expand(node.right))
        if type(node) is Mul:
            return bounded((a*b,x+y) for a,x in expand(node.left) for b,y in expand(node.right))
        raise ValueError('the bounded Gaussian expansion guide only accepts strict natural terms')
    return tuple(factors for coefficient,factors in expand(term) for _ in range(coefficient))


def _ordered_expansion_identity(left: str, right: str) -> tuple[str,...]:
    """Emit ordinary distribution/association/permutation proofs, with no AC search."""
    def monomial(factors):
        result=factors[-1]
        for factor in reversed(factors[:-1]):
            result=_mul(factor,result)
        return result
    first=tuple(monomial(value) for value in _ordered_monomials(left))
    second=tuple(monomial(value) for value in _ordered_monomials(right))
    if sorted(first)!=sorted(second):
        raise ValueError('ordered Gaussian expansions are not the same monomials')
    rules=('add_mul','mul_add','mul_assoc','add_assoc')
    return (f'trans {_right_group(first)}',)+_simp(*rules)+(f'trans {_right_group(second)}',)+tuple(_permute_addends(first,second))+('symm',)+_simp(*rules)


def _factor_group(factors: tuple[str,...]) -> str:
    if not factors:
        return '1'
    result=factors[-1]
    for factor in reversed(factors[:-1]):
        result=_mul(factor,result)
    return result


def _sum_group(parts: tuple[str,...]) -> str:
    return _right_group(parts) if parts else '0'


def _move_factor_front(parts: tuple[str,...], position: int) -> tuple[str,...]:
    if position==0:
        return ('refl',)
    if len(parts)==2:
        return ('apply mul_comm',)
    if position==1:
        return ('apply natural_mul_swap_right_tail',)
    selected=parts[position]
    tail=parts[1:]
    moved=(selected,)+tuple(value for i,value in enumerate(tail) if i!=position-1)
    return (f'trans {_factor_group((parts[0],)+moved)}','congr','refl')+_move_factor_front(tail,position-1)+('apply natural_mul_swap_right_tail',)


def _factor_permutation(source: tuple[str,...], target: tuple[str,...]) -> tuple[str,...]:
    if sorted(source)!=sorted(target):
        raise ValueError('Gaussian factor permutations require the same exact factors')
    if source==target:
        return ('refl',)
    position=source.index(target[0])
    if position==0:
        return ('congr','refl')+_factor_permutation(source[1:],target[1:])
    remaining=tuple(value for i,value in enumerate(source) if i!=position)
    return (f'trans {_factor_group((target[0],)+remaining)}',)+_move_factor_front(source,position)+('congr','refl')+_factor_permutation(remaining,target[1:])


def _factor_list_normalization(monomials: tuple[tuple[str,...],...]) -> tuple[str,...]:
    if not monomials:
        return ('refl',)
    first=_factor_permutation(monomials[0],tuple(sorted(monomials[0])))
    if len(monomials)==1:
        return first
    return ('congr',)+first+_factor_list_normalization(monomials[1:])


def _polynomial_expansion_dependencies(left: str, right: str) -> tuple[str,...]:
    numeric=False
    for expression in (left,right):
        pending=[parse_term_with_names(expression)[0]]
        while pending:
            node=pending.pop()
            if type(node) in (Zero,Succ):
                numeric=True
                break
            if type(node) in (Add,Mul):
                pending.extend((node.left,node.right))
        if numeric:
            break
    return _POLY+(("mul_succ_left","mul_zero_left","zero_add","one_mul","mul_one") if numeric else ())


def _commutative_expansion_identity(left: str, right: str) -> tuple[str,...]:
    """Guide ordinary equality certificates, also for small literal coefficients.

    The guide is not trusted and does not add a tactic.  Both distributive
    expansions, each factor permutation, and the sum permutation remain
    explicit checked uses of the declared historic arithmetic laws.
    """
    first,second=_ordered_monomials(left),_ordered_monomials(right)
    first_raw=tuple(_factor_group(value) for value in first)
    second_raw=tuple(_factor_group(value) for value in second)
    first_sorted=tuple(_factor_group(tuple(sorted(value))) for value in first)
    second_sorted=tuple(_factor_group(tuple(sorted(value))) for value in second)
    if sorted(first_sorted)!=sorted(second_sorted):
        raise ValueError('Gaussian polynomial guides require exactly equal expanded monomials')
    numeric=_polynomial_expansion_dependencies(left,right)[len(_POLY):]
    rules=('add_mul','mul_add','mul_assoc','add_assoc',*numeric)
    return (f'trans {_sum_group(first_raw)}',)+_simp(*rules)+(f'trans {_sum_group(first_sorted)}',)+_factor_list_normalization(first)+(f'trans {_sum_group(second_sorted)}',)+tuple(_permute_addends(first_sorted,second_sorted))+(f'trans {_sum_group(second_raw)}','symm')+_factor_list_normalization(second)+('symm',)+_simp(*rules)


def make_gaussian_euclidean_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    p,n,q,m = "p","n","q","m"
    P,N = _product(p,n,q,m)
    SP,SQ,TP,TQ = _positive(p,n),_positive(q,m),_negative(p,n),_negative(q,m)
    plusP,plusN = _add(p,q),_add(n,m)
    product_positive = _add(_mul(SP,SQ),_mul(TP,TQ))
    product_negative = _add(_mul(SP,TQ),_mul(TP,SQ))
    plus_positive = _add(_add(SP,SQ),_add(P,P))
    plus_negative = _add(_add(TP,TQ),_add(N,N))
    return (
        spec(
            "gaussian_signed_square_exists",
            f"forall p n. exists s. ({_square(p,n,'s')})",
            ("matrix_lattice_absolute_difference_exists","four_square_absolute_square_balance"),
            _intro(p,n)+("specialize matrix_lattice_absolute_difference_exists p","specialize matrix_lattice_absolute_difference_exists n","cases matrix_lattice_absolute_difference_exists","exists x * x")
            +_call("four_square_absolute_square_balance",p,n,"x")+("exact matrix_lattice_absolute_difference_exists_witness",),
            "Construct the actual natural square of every represented integer from its witnessed absolute difference.",
        ),
        spec(
            "gaussian_signed_square_functional",
            f"forall p n s t. ({_square(p,n,'s')}) -> ({_square(p,n,'t')}) -> s = t",
            ("add_right_cancel",),
            _intro(p,n,"s","t","hfirst","hsecond")+_call("add_right_cancel","s","t",_negative(p,n))
            +(f"trans {_positive(p,n)}","symm","exact hfirst","exact hsecond"),
            "The actual nonnegative square of a signed pair is unique by cancellative natural arithmetic.",
        ),
        spec(
            "gaussian_signed_square_negated",
            f"forall p n s. ({_square(p,n,'s')}) -> ({_square(n,p,'s')})",
            ("add_comm",),
            _intro(p,n,"s","hsquare")+(f"trans {_positive(p,n)}","apply add_comm",f"trans {_add('s',_negative(p,n))}","exact hsquare","congr","refl","apply add_comm"),
            "Negating an arbitrary signed representative leaves its actual square unchanged.",
        ),
        spec(
            "gaussian_signed_square_integer_transport",
            f"forall p n q m s. ({_equal(p,n,q,m)}) -> ({_square(p,n,'s')}) -> ({_square(q,m,'s')})",
            ("matrix_integer_pair_product_balance","add_right_cancel",*_AC),
            _intro(p,n,q,m,"s","hequal","hsquare")
            +(f"have hproduct : {_add(_positive(p,n),_negative(q,m))} = {_add(_positive(q,m),_negative(p,n))}",)
            +_call("matrix_integer_pair_product_balance",p,n,q,m,p,n,q,m)+("exact hequal","exact hequal")
            +_call("add_right_cancel",_positive(q,m),_add('s',_negative(q,m)),_negative(p,n))
            +(f"trans {_add(_positive(p,n),_negative(q,m))}","symm","exact hproduct","rewrite hsquare")+_simp(*_AC),
            "Squaring respects equality of represented integers, not equality of positive and negative components.",
        ),
        spec(
            "gaussian_signed_product_square_positive",
            f"forall p n q m. {_positive(P,N)} = {product_positive}",
            _POLY,
            _intro(p,n,q,m)+_commutative_expansion_identity(_positive(P,N),product_positive),
            "The positive square block of an actual signed product expands into its two positive convolution blocks.",
        ),
        spec(
            "gaussian_signed_product_square_negative",
            f"forall p n q m. {_negative(P,N)} = {product_negative}",
            _POLY,
            _intro(p,n,q,m)+_commutative_expansion_identity(_negative(P,N),product_negative),
            "The negative square block of an actual signed product expands into the two negative convolution blocks.",
        ),
        spec(
            "gaussian_signed_product_square_compensation",
            "forall A B C D s t. A = s + B -> C = t + D -> A * C + B * D = s * t + (A * D + B * C)",
            ("add_mul","mul_add",*_AC),
            _intro("A","B","C","D","s","t","hA","hC")+_simp("hA","hC","add_mul","mul_add",*_AC),
            "Two actual nonnegative signed gaps multiply with an exact, subtraction-free compensation identity.",
        ),
        spec(
            "gaussian_signed_square_product",
            f"forall p n q m s t. ({_square(p,n,'s')}) -> ({_square(q,m,'t')}) -> ({_square(P,N,'s * t')})",
            ("gaussian_signed_product_square_positive","gaussian_signed_product_square_negative","gaussian_signed_product_square_compensation"),
            _intro(p,n,q,m,"s","t","hfirst","hsecond")+(f"trans {product_positive}",)
            +("apply gaussian_signed_product_square_positive",)
            +(f"trans {_add('s * t',product_negative)}",)
            +("apply gaussian_signed_product_square_compensation","exact hfirst","exact hsecond","congr","refl","symm","apply gaussian_signed_product_square_negative"),
            "The actual square of a signed product is the product of its two actual natural squares.",
        ),
        spec(
            "gaussian_signed_sum_square_positive",
            f"forall p n q m. {_positive(plusP,plusN)} = {plus_positive}",
            ("add_mul","mul_add","mul_comm",*_AC),
            _intro(p,n,q,m)+_simp("add_mul","mul_add","mul_comm",*_AC),
            "Positive square expansion for the sum of two genuine signed pairs.",
        ),
        spec(
            "gaussian_signed_sum_square_negative",
            f"forall p n q m. {_negative(plusP,plusN)} = {plus_negative}",
            ("add_mul","mul_add","mul_comm",*_AC),
            _intro(p,n,q,m)+_simp("add_mul","mul_add","mul_comm",*_AC),
            "Negative square expansion for the sum of two genuine signed pairs.",
        ),
        spec(
            "gaussian_signed_square_sum_compensation",
            f"forall p n q m s t z. ({_square(p,n,'s')}) -> ({_square(q,m,'t')}) -> ({_square(plusP,plusN,'z')}) -> {_add('z',_add(N,N))} = {_add('s + t',_add(P,P))}",
            ("gaussian_signed_sum_square_positive","gaussian_signed_sum_square_negative","add_right_cancel",*_AC),
            _intro(p,n,q,m,"s","t","z","hfirst","hsecond","hsum")
            +_call("add_right_cancel",_add('z',_add(N,N)),_add('s + t',_add(P,P)),_add(TP,TQ))
            +(f"trans {_add('z',plus_negative)}",)+_simp(*_AC)
            +(f"trans {_add('z',_negative(plusP,plusN))}","congr","refl","symm","apply gaussian_signed_sum_square_negative")
            +(f"trans {_positive(plusP,plusN)}","symm","exact hsum",f"trans {plus_positive}")
            +("apply gaussian_signed_sum_square_positive","rewrite hfirst","rewrite hsecond")+_simp(*_AC),
            "Exact signed cross-term compensation for a squared sum, with no unproved norm premise.",
        ),
        spec(
            "gaussian_signed_square_difference_compensation",
            f"forall p n q m s t z. ({_square(p,n,'s')}) -> ({_square(q,m,'t')}) -> ({_square(_add(p,m),_add(n,q),'z')}) -> {_add('z',_add(P,P))} = {_add('s + t',_add(N,N))}",
            ("gaussian_signed_square_sum_compensation","gaussian_signed_square_negated"),
            _intro(p,n,q,m,"s","t","z","hfirst","hsecond","hdifference")
            +_call("gaussian_signed_square_sum_compensation",p,n,m,q,"s","t","z")+("exact hfirst",)
            +_call("gaussian_signed_square_negated",q,m,"t")+("exact hsecond","exact hdifference"),
            "Exact signed cross-term compensation for a squared difference; sign reversal preserves the same actual square.",
        ),
        spec(
            "gaussian_signed_norm_exists",
            f"forall p n q m. exists N. ({_norm(p,n,q,m,'N','exists_total')})",
            ("gaussian_signed_square_exists",),
            _intro(p,n,q,m)+(f"have hreal : exists u. ({_square(p,n,'u')})",)+_call("gaussian_signed_square_exists",p,n)+("cases hreal",)
            +(f"have himaginary : exists v. ({_square(q,m,'v')})",)+_call("gaussian_signed_square_exists",q,m)+("cases himaginary",)
            +_exists("x + x1","x","x1")+("split","exact hreal_witness","split","exact himaginary_witness","refl"),
            "Every signed Gaussian coordinate pair has a constructed actual nonnegative squared norm.",
        ),
        spec(
            "gaussian_signed_norm_functional",
            f"forall p n q m N M. ({_norm(p,n,q,m,'N','first')}) -> ({_norm(p,n,q,m,'M','second')}) -> N = M",
            ("gaussian_signed_square_functional",),
            _intro(p,n,q,m,"N","M","hfirst","hsecond")+_cases("hfirst",2)+_parts("hfirst_witness_witness",3)+_cases("hsecond",2)+_parts("hsecond_witness_witness",3)
            +("trans x + x1","exact hfirst_witness_witness_right_right","trans x2 + x3","congr")
            +("apply gaussian_signed_square_functional","exact hfirst_witness_witness_left","exact hsecond_witness_witness_left")
            +("apply gaussian_signed_square_functional","exact hfirst_witness_witness_right_left","exact hsecond_witness_witness_right_left","symm","exact hsecond_witness_witness_right_right"),
            "The squared Gaussian norm is functional across every possible square-witness choice.",
        ),
    ) + _norm_product_rows(spec) + _complex_algebra_rows(spec) + _rounding_rows(spec) + _raw_division_rows(spec) + _code_rows(spec) + _zero_and_signed_bridge_rows(spec) + _coded_arithmetic_rows(spec) + _coded_division_rows(spec)


def _components(first: tuple[str,...], second: tuple[str,...]) -> str:
    return _and(*(f"({a}) = ({b})" for a,b in zip(first,second,strict=True)))


def _norm_product_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    variables = ("a","b","c","d","e","f","g","h")
    A,B,C,D = variables[:2],variables[2:4],variables[4:6],variables[6:]
    def product(X,Y):
        return _product(*X,*Y)
    AB,AC,BD,CD,DC = product(A,B),product(A,C),product(B,D),product(C,D),product(D,C)
    inner_left,inner_right = product(B,CD),product(C,BD)
    shuffle_left,shuffle_right = product(AB,CD),product(AC,BD)
    shuffle_middle_left,shuffle_middle_right = product(A,inner_left),product(A,inner_right)
    shuffle_script = _intro(*variables)
    shuffle_script += (f"have hleft : {_components(shuffle_left,shuffle_middle_left)}",)+_call("signed_pair_mul_components_associate",*A,*B,*CD)+("cases hleft",)
    shuffle_script += (f"have hright : {_components(shuffle_right,shuffle_middle_right)}",)+_call("signed_pair_mul_components_associate",*A,*C,*BD)+("cases hright",)
    for i,label in enumerate(("positive","negative")):
        shuffle_script += (f"have hmiddle_{label} : {inner_left[i]} = {inner_right[i]}",)+_call("gaussian_signed_product_interchange_"+label,*B,*C,*D)
    shuffle_script += ("split",)
    for i,side in enumerate(("left","right")):
        middle = ("positive","negative") if i==0 else ("negative","positive")
        shuffle_script += (f"trans {shuffle_middle_left[i]}",f"exact hleft_{side}",f"trans {shuffle_middle_right[i]}","congr","congr","refl",f"exact hmiddle_{middle[0]}","congr","refl",f"exact hmiddle_{middle[1]}","symm",f"exact hright_{side}")
    U,V,W,X = product(A,C),product(B,D),product(A,D),product(B,C)
    cross_left,cross_right = product(U,V),product(W,X)
    cross_common_left,cross_common_right = product(AB,CD),product(AB,DC)
    cross_script = _intro(*variables)
    cross_script += (f"have hleft : {_components(cross_left,cross_common_left)}",)+_call("gaussian_signed_product_shuffle",*A,*C,*B,*D)+("cases hleft",)
    cross_script += (f"have hright : {_components(cross_right,cross_common_right)}",)+_call("gaussian_signed_product_shuffle",*A,*D,*B,*C)+("cases hright",)
    cross_script += (f"have hcommute : {_components(CD,DC)}",)+_call("gaussian_signed_product_commutative",*C,*D)+("cases hcommute","split")
    for i,side in enumerate(("left","right")):
        middle = ("left","right") if i==0 else ("right","left")
        cross_script += (f"trans {cross_common_left[i]}",f"exact hleft_{side}",f"trans {cross_common_right[i]}","congr","congr","refl",f"exact hcommute_{middle[0]}","congr","refl",f"exact hcommute_{middle[1]}","symm",f"exact hright_{side}")

    four_pairs=(('up','un'),('vp','vn'),('wp','wn'),('xp','xn'))
    uu,vv,ww,xx=four_pairs
    uv,wx=product(uu,vv),product(ww,xx)
    real_pair=(_add(uu[0],vv[1]),_add(uu[1],vv[0]))
    imag_pair=(_add(ww[0],xx[0]),_add(ww[1],xx[1]))
    all_square_inputs=tuple(_square(*pair,value) for pair,value in zip(four_pairs,('su','sv','sw','sx')))
    lagrange_statement=("forall up un vp vn wp wn xp xn su sv sw sx R I. "+' -> '.join(f'({part})' for part in (*all_square_inputs,f'{uv[0]} = {wx[0]}',f'{uv[1]} = {wx[1]}',_square(*real_pair,'R'),_square(*imag_pair,'I')))+" -> R + I = (su + sv) + (sw + sx)")
    lagrange_script=_intro('up','un','vp','vn','wp','wn','xp','xn','su','sv','sw','sx','R','I','hu','hv','hw','hx','hpositive','hnegative','hreal','himaginary')
    lagrange_script+=(f"have hdifference : {_add('R',_add(uv[0],uv[0]))} = {_add('su + sv',_add(uv[1],uv[1]))}",)+_call('gaussian_signed_square_difference_compensation',*uu,*vv,'su','sv','R')+('exact hu','exact hv','exact hreal')
    lagrange_script+=(f"have hsum : {_add('I',_add(wx[1],wx[1]))} = {_add('sw + sx',_add(wx[0],wx[0]))}",)+_call('gaussian_signed_square_sum_compensation',*ww,*xx,'sw','sx','I')+('exact hw','exact hx','exact himaginary')
    lagrange_script+=('rewrite <- hpositive at hsum','rewrite <- hpositive at hsum','rewrite <- hnegative at hsum','rewrite <- hnegative at hsum')
    lagrange_script+=_call('add_cross_sum_chain','R','su + sv',_add(uv[0],uv[0]),_add(uv[1],uv[1]),'I','sw + sx')+('exact hdifference',f"trans {_add('I',_add(uv[1],uv[1]))}",'apply add_comm',f"trans {_add('sw + sx',_add(uv[0],uv[0]))}",'exact hsum','apply add_comm')

    actual_product=_complex_product((*A,*B),(*C,*D))
    scalar_values=('x * x2','x1 * x3','x * x3','x1 * x2')
    norm_product_script=_intro(*variables,'N','M','hfirst','hsecond')+_cases('hfirst',2)+_parts('hfirst_witness_witness',3)+_cases('hsecond',2)+_parts('hsecond_witness_witness',3)
    norm_product_script+=(f"have hreal : exists s. ({_square(*actual_product[:2],'s')})",)+_call('gaussian_signed_square_exists',*actual_product[:2])+('cases hreal',)
    norm_product_script+=(f"have himaginary : exists t. ({_square(*actual_product[2:],'t')})",)+_call('gaussian_signed_square_exists',*actual_product[2:])+('cases himaginary',)
    norm_product_script+=(f"have hcross : {_components(cross_left,cross_right)}",)+_call('gaussian_signed_product_cross_interchange',*variables)+('cases hcross',)
    norm_product_script+=(f"have hnorm : x4 + x5 = {_add(_add(scalar_values[0],scalar_values[1]),_add(scalar_values[2],scalar_values[3]))}",)
    norm_product_script+=_call('gaussian_signed_square_lagrange',*U,*V,*W,*X,*scalar_values,'x4','x5')
    for args,hs,ht in (
        ((*A,*C,'x','x2'),'hfirst_witness_witness_left','hsecond_witness_witness_left'),
        ((*B,*D,'x1','x3'),'hfirst_witness_witness_right_left','hsecond_witness_witness_right_left'),
        ((*A,*D,'x','x3'),'hfirst_witness_witness_left','hsecond_witness_witness_right_left'),
        ((*B,*C,'x1','x2'),'hfirst_witness_witness_right_left','hsecond_witness_witness_left'),
    ):
        norm_product_script+=_call('gaussian_signed_square_product',*args)+(f'exact {hs}',f'exact {ht}')
    norm_product_script+=('exact hcross_left','exact hcross_right','exact hreal_witness','exact himaginary_witness')
    norm_product_script+=_exists('x4','x5')+('split','exact hreal_witness','split','exact himaginary_witness','rewrite hfirst_witness_witness_right_right','rewrite hsecond_witness_witness_right_right',f"trans {_add(_add(scalar_values[0],scalar_values[1]),_add(scalar_values[2],scalar_values[3]))}")
    norm_product_script+=_simp('add_mul','mul_add',*_AC)+('symm','exact hnorm')

    output = [
        spec('gaussian_signed_product_interchange_'+label,
             f"forall a b c d e f. {product(A,product(B,C))[i]} = {product(B,product(A,C))[i]}",
             _POLY,_intro('a','b','c','d','e','f')+_simp(*_POLY),
             'Actual signed-product '+label+' components permit interchange of the first two factors, by ordinary semiring certificates.')
        for i,label in enumerate(('positive','negative'))
    ]
    output.extend((
        spec('gaussian_signed_product_commutative',f"forall a b c d. {_components(product(A,B),product(B,A))}",
             ('mul_comm','add_comm'),_intro('a','b','c','d')+('split',)+_simp('mul_comm','add_comm')+_simp('mul_comm','add_comm'),
             'The two actual signed product components are commutative, before any quotient normalization.'),
        spec('gaussian_signed_product_shuffle',f"forall {' '.join(variables)}. {_components(shuffle_left,shuffle_right)}",
             ('signed_pair_mul_components_associate','gaussian_signed_product_interchange_positive','gaussian_signed_product_interchange_negative'),
             shuffle_script,'Four actual signed factors admit the exact middle-factor interchange, assembled from checked associative and commutative components.'),
        spec('gaussian_signed_product_cross_interchange',f"forall {' '.join(variables)}. {_components(cross_left,cross_right)}",
             ('gaussian_signed_product_shuffle','gaussian_signed_product_commutative'),cross_script,
             'The actual cross products (ac)(bd) and (ad)(bc) agree in both signed components.'),
        spec('gaussian_signed_square_lagrange',lagrange_statement,
             ('gaussian_signed_square_difference_compensation','gaussian_signed_square_sum_compensation','add_cross_sum_chain','add_comm'),lagrange_script,
             'Lagrange cancellation for two signed squared coordinates, with exact cross-product equations and all four actual scalar squares.'),
        spec('gaussian_signed_norm_product',
             f"forall {' '.join(variables)} N M. ({_norm(*A,*B,'N','factor_left')}) -> ({_norm(*C,*D,'M','factor_right')}) -> ({_norm(*actual_product,'N * M','product_norm')})",
             ('gaussian_signed_square_exists','gaussian_signed_product_cross_interchange','gaussian_signed_square_lagrange','gaussian_signed_square_product','add_mul','mul_add',*_AC),norm_product_script,
             'The actual squared Gaussian norm is multiplicative for arbitrary signed representatives, by checked two-coordinate Lagrange cancellation.'),
        spec('gaussian_signed_norm_integer_transport',
             f"forall {' '.join(variables)} N. ({_complex_equal((*A,*B),(*C,*D))}) -> ({_norm(*A,*B,'N','transport_first')}) -> ({_norm(*C,*D,'N','transport_second')})",
             ('gaussian_signed_square_integer_transport',),
             _intro(*variables,'N','hequal','hnorm')+('cases hequal',)+_cases('hnorm',2)+_parts('hnorm_witness_witness',3)+_exists('x','x1')+('split',)
             +_call('gaussian_signed_square_integer_transport',*A,*C,'x')+('exact hequal_left','exact hnorm_witness_witness_left','split')
             +_call('gaussian_signed_square_integer_transport',*B,*D,'x1')+('exact hequal_right','exact hnorm_witness_witness_right_left','exact hnorm_witness_witness_right_right'),
             'The actual Gaussian norm is invariant under equality of both represented integer coordinates.'),
        spec('gaussian_signed_norm_conjugate',
             f"forall a b c d N. ({_norm(*A,*B,'N','conjugate_source')}) -> ({_norm(*A,B[1],B[0],'N','conjugate_target')})",
             ('gaussian_signed_square_negated',),
             _intro('a','b','c','d','N','hnorm')+_cases('hnorm',2)+_parts('hnorm_witness_witness',3)+_exists('x','x1')+('split','exact hnorm_witness_witness_left','split')
             +_call('gaussian_signed_square_negated',*B,'x1')+('exact hnorm_witness_witness_right_left','exact hnorm_witness_witness_right_right'),
             'Complex conjugation preserves the actual squared Gaussian norm, for every signed representative.'),
        spec('gaussian_signed_square_zero_iff',
             f"forall p n s. ({_square('p','n','s')}) -> ((s = 0 -> p = n) /\\ (p = n -> s = 0))",
             ('matrix_lattice_absolute_difference_exists','four_square_absolute_square_balance','gaussian_signed_square_functional','square_zero_root','zero_add'),
             _intro('p','n','s','hsquare')+('split','intro hzero','specialize matrix_lattice_absolute_difference_exists p','specialize matrix_lattice_absolute_difference_exists n','cases matrix_lattice_absolute_difference_exists')
             +(f"have hmagnitude : {_square('p','n','x * x')}",)+_call('four_square_absolute_square_balance','p','n','x')+('exact matrix_lattice_absolute_difference_exists_witness','have hsquarezero : x * x = s')
             +_call('gaussian_signed_square_functional','p','n','x * x','s')+('exact hmagnitude','exact hsquare','rewrite hzero at hsquarezero','have hmagnitudezero : x = 0')
             +_call('square_zero_root','x')+('exact hsquarezero','cases matrix_lattice_absolute_difference_exists_witness','trans n + x','exact matrix_lattice_absolute_difference_exists_witness_left','rewrite hmagnitudezero','apply PA3','symm','trans p + x','exact matrix_lattice_absolute_difference_exists_witness_right','rewrite hmagnitudezero','apply PA3')
             +('intro hequal',f"have hzero : {_square('p','n','0')}")+_simp('hequal','zero_add')+_call('gaussian_signed_square_functional','p','n','s','0')+('exact hsquare','exact hzero'),
             'A genuine natural signed square is zero exactly when the represented integer is zero.'),
        spec('gaussian_signed_norm_nonzero',
             f"forall a b c d N. ({_norm(*A,*B,'N','nonzero')}) -> ~(a = b /\\ c = d) -> ~(N = 0)",
             ('gaussian_signed_square_zero_iff','add_eq_zero_left','add_eq_zero_right'),
             _intro('a','b','c','d','N','hnorm','hnonzero','hzero')+_cases('hnorm',2)+_parts('hnorm_witness_witness',3)
             +('have hsumzero : x + x1 = 0','trans N','symm','exact hnorm_witness_witness_right_right','exact hzero')
             +('have hrealzero : (x = 0 -> a = b) /\\ (a = b -> x = 0)',)+_call('gaussian_signed_square_zero_iff',*A,'x')+('exact hnorm_witness_witness_left','cases hrealzero')
             +('have himagzero : (x1 = 0 -> c = d) /\\ (c = d -> x1 = 0)',)+_call('gaussian_signed_square_zero_iff',*B,'x1')+('exact hnorm_witness_witness_right_left','cases himagzero','apply hnonzero','split','apply hrealzero_left')
             +_call('add_eq_zero_left','x','x1')+('exact hsumzero','apply himagzero_left')+_call('add_eq_zero_right','x','x1')+('exact hsumzero',),
             'Every nonzero represented Gaussian integer has an actually positive natural norm.'),
        spec('gaussian_signed_square_scaled',
             f"forall p n s k. ({_square('p','n','s')}) -> ({_square('k * p','k * n','(k * k) * s')})",
             ('gaussian_signed_square_product','mul_zero_left','zero_add'),
             _intro('p','n','s','k','hsquare')+(f"have hnatural : {_square('k','0','k * k')}",)+_simp('mul_zero_left','zero_add')
             +(f"have hproduct : {_square(*_product('k','0','p','n'),'(k * k) * s')}",)+_call('gaussian_signed_square_product','k','0','p','n','k * k','s')+('exact hnatural','exact hsquare')
             +('have hpositive : k * p + 0 * n = k * p',)+_simp('mul_zero_left','zero_add')+('have hnegative : k * n + 0 * p = k * n',)+_simp('mul_zero_left','zero_add')
             +('rewrite hpositive at hproduct',)*4+('rewrite hnegative at hproduct',)*4+('exact hproduct',),
             'Scaling a genuine signed pair by any natural multiplies its actual square by the scalar square, including zero.'),
    ))
    return tuple(output)


def _complex_algebra_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    names=tuple('abcdefghijklmnop')
    A,B,C,D=names[:4],names[4:8],names[8:12],names[12:]
    product=_complex_product
    left_assoc,right_assoc=product(product(A,B),C),product(A,product(B,C))
    left_difference=product(A,_complex_difference(B,C))
    right_difference=_complex_difference(product(A,B),product(A,C))
    labels=('real_positive','real_negative','imaginary_positive','imaginary_negative')
    assoc_basis=('add_mul','mul_add','mul_assoc',*_AC)
    difference_basis=('mul_add',*_AC)
    result=[]
    for i,label in enumerate(labels):
        result.append(spec('gaussian_product_associate_'+label,
                           f"forall {' '.join(names[:12])}. {left_assoc[i]} = {right_assoc[i]}",
                           assoc_basis,_intro(*names[:12])+_ordered_expansion_identity(left_assoc[i],right_assoc[i]),
                           'Exact '+label.replace('_',' ')+' component associativity for the actual four-component Gaussian product.'))
    for i,label in enumerate(labels):
        result.append(spec('gaussian_product_difference_'+label,
                           f"forall {' '.join(names[:12])}. {left_difference[i]} = {right_difference[i]}",
                           difference_basis,_intro(*names[:12])+_simp(*difference_basis),
                           'Exact '+label.replace('_',' ')+' component distributivity over a genuine signed Gaussian difference.'))
    for operation,left,right in (('associate',left_assoc,right_assoc),('difference',left_difference,right_difference)):
        script=_intro(*names[:12])+('split','congr',f'apply gaussian_product_{operation}_real_positive','symm',f'apply gaussian_product_{operation}_real_negative','congr',f'apply gaussian_product_{operation}_imaginary_positive','symm',f'apply gaussian_product_{operation}_imaginary_negative')
        result.append(spec('gaussian_product_'+operation,
                           f"forall {' '.join(names[:12])}. ({_complex_equal(left,right)})",
                           tuple('gaussian_product_'+operation+'_'+label for label in labels),script,
                           'The actual Gaussian product '+('is associative' if operation=='associate' else 'distributes over subtraction')+' in represented integer coordinates.'))

    product_congruence_script=_intro(*names,'hfirst','hsecond')+('cases hfirst','cases hsecond','split')
    for imaginary in (False,True):
        if not imaginary:
            oldfirst,newfirst=_product(*A[:2],*C[:2]),_product(*B[:2],*D[:2])
            oldsecond,newsecond=_product(*A[2:],*C[2:]),_product(*B[2:],*D[2:])
            product_congruence_script+=_call('integer_span_pair_add_congruence',*oldfirst,*oldsecond[::-1],*newfirst,*newsecond[::-1])
            product_congruence_script+=_call('matrix_integer_pair_product_balance',*A[:2],*B[:2],*C[:2],*D[:2])+('exact hfirst_left','exact hsecond_left')
            product_congruence_script+=_call('matrix_integer_pair_negation_balance',*oldsecond,*newsecond)
            product_congruence_script+=_call('matrix_integer_pair_product_balance',*A[2:],*B[2:],*C[2:],*D[2:])+('exact hfirst_right','exact hsecond_right')
        else:
            oldfirst,newfirst=_product(*A[:2],*C[2:]),_product(*B[:2],*D[2:])
            oldsecond,newsecond=_product(*A[2:],*C[:2]),_product(*B[2:],*D[:2])
            product_congruence_script+=_call('integer_span_pair_add_congruence',*oldfirst,*oldsecond,*newfirst,*newsecond)
            product_congruence_script+=_call('matrix_integer_pair_product_balance',*A[:2],*B[:2],*C[2:],*D[2:])+('exact hfirst_left','exact hsecond_right')
            product_congruence_script+=_call('matrix_integer_pair_product_balance',*A[2:],*B[2:],*C[:2],*D[:2])+('exact hfirst_right','exact hsecond_left')
    difference_congruence_script=_intro(*names,'hfirst','hsecond')+('cases hfirst','cases hsecond','split')
    for offset,side in ((0,'left'),(2,'right')):
        aa,bb,cc,dd=A[offset:offset+2],B[offset:offset+2],C[offset:offset+2],D[offset:offset+2]
        difference_congruence_script+=_call('integer_span_pair_add_congruence',*aa,*cc[::-1],*bb,*dd[::-1])+(f'exact hfirst_{side}',)
        difference_congruence_script+=_call('matrix_integer_pair_negation_balance',*cc,*dd)+(f'exact hsecond_{side}',)

    SP,SQ,TP,TQ=_positive(*A[:2]),_positive(*A[2:]),_negative(*A[:2]),_negative(*A[2:])
    self_product=product(_conjugate(A),A)
    conjugate_script=_intro(*A,'N','hnorm')+(f"have hbalance : {_add(SP,SQ)} = {_add('N',_add(TP,TQ))}",)+_call('gaussian_signed_norm_balance',*A,'N')+('exact hnorm',)
    conjugate_script+=(f"have hpositive : {self_product[0]} = {_add(SP,SQ)}",)+_simp('mul_comm',*_AC)
    conjugate_script+=(f"have hnegative : {self_product[1]} = {_add(TP,TQ)}",)+_simp('mul_comm',*_AC)
    conjugate_script+=(f"have himaginary : {self_product[2]} = {self_product[3]}",)+_simp('mul_comm',*_AC)
    conjugate_script+=('split',f'trans {self_product[0]}','apply PA3',f'trans {_add(SP,SQ)}','exact hpositive',f'trans {_add("N",_add(TP,TQ))}','exact hbalance','congr','refl','symm','exact hnegative',f'trans {self_product[2]}','apply PA3',f'trans {self_product[3]}','exact himaginary','symm','apply zero_add')
    adjoint=product(_conjugate(A),product(A,B))
    associated=product(self_product,B)
    scalar_product=product(('N','0','0','0'),B)
    scaled=_scale('N',B)
    adjoint_script=_intro(*A,*B,'N','hnorm')+(f"have hassociation : {_complex_equal(adjoint,associated)}",)
    adjoint_script+=_call('gaussian_equal_symmetric',*associated,*adjoint)+_call('gaussian_product_associate',*_conjugate(A),*A,*B)
    adjoint_script+=(f"have hscaling : {_complex_equal(associated,scaled)}",)
    adjoint_script+=_call('gaussian_equal_transitive',*associated,*scalar_product,*scaled)
    adjoint_script+=_call('gaussian_product_integer_congruence',*self_product,'N','0','0','0',*B,*B)
    adjoint_script+=_call('gaussian_conjugate_product_is_norm',*A,'N')+('exact hnorm',)+_call('gaussian_equal_reflexive',*B)
    adjoint_script+=_call('gaussian_natural_scalar_product','N',*B)
    adjoint_script+=_call('gaussian_equal_transitive',*adjoint,*associated,*scaled)+('exact hassociation','exact hscaling')
    residual=_complex_difference(A,product(B,C))
    numerator=product(_conjugate(B),A)
    residual_product=product(_conjugate(B),residual)
    expanded_residual=_complex_difference(numerator,product(_conjugate(B),product(B,C)))
    actual_error=_complex_difference(numerator,_scale('N',C))
    residual_script=_intro(*names[:12],'N','hnorm')
    residual_script+=_call('gaussian_equal_transitive',*residual_product,*expanded_residual,*actual_error)
    residual_script+=_call('gaussian_product_difference',*_conjugate(B),*A,*product(B,C))
    residual_script+=_call('gaussian_difference_integer_congruence',*numerator,*numerator,*product(_conjugate(B),product(B,C)),*_scale('N',C))
    residual_script+=_call('gaussian_equal_reflexive',*numerator)+_call('gaussian_adjoint_product_is_norm_scale',*B,*C,'N')+('exact hnorm',)

    result.extend((
        spec('gaussian_equal_reflexive',f"forall {' '.join(A)}. ({_complex_equal(A,A)})",(),_intro(*A)+('split','refl','refl'),
             'Represented Gaussian integer equality is reflexive.'),
        spec('gaussian_equal_symmetric',f"forall {' '.join((*A,*B))}. ({_complex_equal(A,B)}) -> ({_complex_equal(B,A)})",(),
             _intro(*A,*B,'hequal')+('cases hequal','split','symm','exact hequal_left','symm','exact hequal_right'),
             'Represented Gaussian integer equality is symmetric.'),
        spec('gaussian_equal_transitive',f"forall {' '.join((*A,*B,*C))}. ({_complex_equal(A,B)}) -> ({_complex_equal(B,C)}) -> ({_complex_equal(A,C)})",
             ('integer_span_pair_equal_transitive',),_intro(*A,*B,*C,'hfirst','hsecond')+('cases hfirst','cases hsecond','split')
             +_call('integer_span_pair_equal_transitive',*A[:2],*B[:2],*C[:2])+('exact hfirst_left','exact hsecond_left')
             +_call('integer_span_pair_equal_transitive',*A[2:],*B[2:],*C[2:])+('exact hfirst_right','exact hsecond_right'),
             'Represented Gaussian integer equality is transitive by actual signed cross-sum cancellation.'),
        spec('gaussian_product_integer_congruence',f"forall {' '.join(names)}. ({_complex_equal(A,B)}) -> ({_complex_equal(C,D)}) -> ({_complex_equal(product(A,C),product(B,D))})",
             ('integer_span_pair_add_congruence','matrix_integer_pair_product_balance','matrix_integer_pair_negation_balance'),product_congruence_script,
             'The actual Gaussian multiplication preserves equality of represented integers in both operands.'),
        spec('gaussian_difference_integer_congruence',f"forall {' '.join(names)}. ({_complex_equal(A,B)}) -> ({_complex_equal(C,D)}) -> ({_complex_equal(_complex_difference(A,C),_complex_difference(B,D))})",
             ('integer_span_pair_add_congruence','matrix_integer_pair_negation_balance'),difference_congruence_script,
             'Actual Gaussian subtraction preserves integer representative equivalence in both operands.'),
        spec('gaussian_signed_norm_balance',f"forall {' '.join(A)} N. ({_norm(*A,'N','norm_balance')}) -> {_add(SP,SQ)} = {_add('N',_add(TP,TQ))}",
             _AC,_intro(*A,'N','hnorm')+_cases('hnorm',2)+_parts('hnorm_witness_witness',3)+('rewrite hnorm_witness_witness_left','rewrite hnorm_witness_witness_right_left','rewrite hnorm_witness_witness_right_right')+_simp(*_AC),
             'An actual Gaussian norm is exactly the difference of its positive-square and negative-cross blocks.'),
        spec('gaussian_conjugate_product_is_norm',f"forall {' '.join(A)} N. ({_norm(*A,'N','self_norm')}) -> ({_complex_equal(self_product,('N','0','0','0'))})",
             ('gaussian_signed_norm_balance','mul_comm','zero_add',*_AC),conjugate_script,
             'Multiplication by the genuine complex conjugate produces the actual natural norm with zero imaginary coordinate.'),
        spec('gaussian_natural_scalar_product',f"forall N {' '.join(B)}. ({_complex_equal(scalar_product,scaled)})",
             ('mul_zero_left','zero_add'),_intro('N',*B)+('split',)+_simp('mul_zero_left','zero_add')+_simp('mul_zero_left','zero_add'),
             'Gaussian multiplication by a natural real scalar is actual coordinatewise natural scaling.'),
        spec('gaussian_adjoint_product_is_norm_scale',f"forall {' '.join((*A,*B))} N. ({_norm(*A,'N','adjoint_norm')}) -> ({_complex_equal(adjoint,scaled)})",
             ('gaussian_equal_transitive','gaussian_equal_symmetric','gaussian_product_associate','gaussian_product_integer_congruence','gaussian_conjugate_product_is_norm','gaussian_equal_reflexive','gaussian_natural_scalar_product'),adjoint_script,
             'The actual conjugate times a Gaussian product equals the genuine norm-scaled second factor.'),
        spec('gaussian_residual_conjugate_identity',f"forall {' '.join(names[:12])} N. ({_norm(*B,'N','residual_divisor_norm')}) -> ({_complex_equal(residual_product,actual_error)})",
             ('gaussian_equal_transitive','gaussian_product_difference','gaussian_difference_integer_congruence','gaussian_equal_reflexive','gaussian_adjoint_product_is_norm_scale'),residual_script,
             'For the actual residual a-bq, multiplication by the conjugate divisor gives exactly the rounded numerator error a*conjugate(b)-N(b)q.'),
        spec('gaussian_difference_reconstructs_dividend',f"forall {' '.join((*A,*B))}. ({_complex_equal(_complex_add(B,_complex_difference(A,B)),A)})",
             _AC,_intro(*A,*B)+('split',)+_simp(*_AC)+_simp(*_AC),
             'Adding a Gaussian subtrahend to its actual signed residual reconstructs the dividend in both integer coordinates.'),
    ))
    return tuple(result)


def _rounded(p: str, n: str, modulus: str, qp: str, qn: str, ep: str, en: str, magnitude: str, tag: str) -> str:
    return _and(
        f"(({p}) + ({modulus}) * ({qn})) + ({en}) = (({n}) + ({modulus}) * ({qp})) + ({ep})",
        _square(ep,en,_mul(magnitude,magnitude)),
        _le(_add(magnitude,magnitude),modulus,tag+'half_bound'),
    )


def gaussian_rounded_signed_division_relation(positive: str, negative: str, modulus: str, quotient_positive: str, quotient_negative: str, error_positive: str, error_negative: str, magnitude: str, *, tag: str) -> str:
    """A constructed nearest signed quotient with an actual twice-magnitude bound."""
    return _rounded(*_args(positive,negative,modulus,quotient_positive,quotient_negative,error_positive,error_negative,magnitude),_identifier(tag,'Gaussian rounding tag'))


def _rounding_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    rounding_script=_intro('p','n','N','hN')
    rounding_script+=(f"have hfloor : exists qp qn r. (p + N * qn = (n + N * qp) + r /\\ ({_lt('r','N','floor_bound')}))",)+_call('signed_integer_floor_exists','p','n','N')+('exact hN',)+_cases('hfloor',3)+('cases hfloor_witness_witness_witness',)
    rounding_script+=(f"have hcenter : exists t. ({centered_signed_remainder('N','x2','t',tag='gaussian_center')})",)+_call('four_square_descent_centered_signed_remainder_exists','N','x2')+('exact hN','cases hcenter','cases hcenter_witness','cases hcenter_witness_right','cases hcenter_witness_right_left')
    rounding_script+=_exists('x + x4','x1','x3','0','x3')+('split','trans p + N * x1','apply PA3','trans (n + N * x) + x2','exact hfloor_witness_witness_witness_left','rewrite hcenter_witness_right_left_witness')+_simp('mul_add','add_assoc')
    rounding_script+=('split',)+_simp('mul_zero_left','zero_add')+('exact hcenter_witness_left','cases hcenter_witness_right_right')
    rounding_script+=_exists('x + x4','x1','0','x3','x3')+('split','trans ((n + N * x) + x2) + x3','congr','exact hfloor_witness_witness_witness_left','refl','trans (n + N * x) + (x2 + x3)','apply add_assoc','rewrite hcenter_witness_right_right_witness')+_simp('mul_add','add_assoc')
    rounding_script+=('split',)+_simp('mul_zero_left','zero_add')+('exact hcenter_witness_left',)
    return (
        spec('gaussian_nonzero_natural_positive',f"forall n. ~(n = 0) -> ({_lt('0','n','positive')})",
             ('nonzero_is_succ',),_intro('n','hn')+('specialize nonzero_is_succ n','have hsuccessor : exists k. n = S k','apply nonzero_is_succ','exact hn','cases hsuccessor','exists x','rewrite hsuccessor_witness','simp'),
             'Every nonzero natural has an explicit strict-positive gap witness.'),
        spec('gaussian_double_square_strict',f"forall h. ~(h = 0) -> ({_lt('h * h + h * h','(h + h) * (h + h)','double_square')})",
             ('mul_ne_zero','add_eq_zero_left','pairing_double_equals_two_mul','four_square_descent_double_square_four_sum','fermat_four_lt_add_positive'),
             _intro('h','hh')+('have hsquare : ~(h * h = 0)','intro hsquarezero')+_call('mul_ne_zero','h','h')+('exact hh','exact hh','exact hsquarezero','have hsum : ~(h * h + h * h = 0)','intro hzero','apply hsquare')
             +_call('add_eq_zero_left','h * h','h * h')+('exact hzero','have hdouble : h + h = 2 * h')+_call('pairing_double_equals_two_mul','h')
             +('have hexpansion : (h + h) * (h + h) = (h * h + h * h) + (h * h + h * h)','rewrite hdouble','rewrite hdouble','apply four_square_descent_double_square_four_sum','rewrite hexpansion')
             +_call('fermat_four_lt_add_positive','h * h + h * h','h * h + h * h')+('exact hsum',),
             'Twice the square of a positive natural is strictly smaller than the square of its double.'),
        spec('gaussian_half_double_square_strict',f"forall N h. ~(N = 0) -> ({_le('h + h','N','half_size')}) -> ({_lt('h * h + h * h','N * N','half_square')})",
             ('zero_or_succ','mul_ne_zero','gaussian_nonzero_natural_positive','succ_ne_zero','gaussian_double_square_strict','natural_square_monotone_expanded','lt_of_lt_of_le','mul_zero_left','zero_add'),
             _intro('N','h','hN','hbound')+('specialize zero_or_succ h','cases zero_or_succ')
             +(f"have hpositive : {_lt('0','N * N','zero_half_positive')}",)+_call('gaussian_nonzero_natural_positive','N * N')+('intro hproductzero',)+_call('mul_ne_zero','N','N')+('exact hN','exact hN','exact hproductzero')
             +('have hsumzero : h * h + h * h = 0',)+_simp('zero_or_succ_left','mul_zero_left','zero_add')+('rewrite hsumzero','exact hpositive','cases zero_or_succ_right','have hh : ~(h = 0)','intro hzero','specialize succ_ne_zero x','apply succ_ne_zero','trans h','symm','exact zero_or_succ_right_witness','exact hzero')
             +_call('lt_of_lt_of_le','h * h + h * h','(h + h) * (h + h)','N * N')+_call('gaussian_double_square_strict','h')+('exact hh',)
             +_call('natural_square_monotone_expanded','h + h','N')+('exact hbound',),
             'For every positive modulus, any half-size magnitude has twice-square strictly below the full modulus square, including magnitude zero.'),
        spec('gaussian_two_half_squares_strict',f"forall N e f. ~(N = 0) -> ({_le('e + e','N','first_half')}) -> ({_le('f + f','N','second_half')}) -> ({_lt('e * e + f * f','N * N','two_half_norm')})",
             ('le_total','natural_square_monotone_expanded','add_le_add_right','add_le_add_left','lt_of_le_of_lt','gaussian_half_double_square_strict'),
             _intro('N','e','f','hN','he','hf')+('specialize le_total e','specialize le_total f','cases le_total')
             +_call('lt_of_le_of_lt','e * e + f * f','f * f + f * f','N * N')+_call('add_le_add_right','e * e','f * f','f * f')+_call('natural_square_monotone_expanded','e','f')+('exact le_total_left',)
             +_call('gaussian_half_double_square_strict','N','f')+('exact hN','exact hf')
             +_call('lt_of_le_of_lt','e * e + f * f','e * e + e * e','N * N')+_call('add_le_add_left','f * f','e * e','e * e')+_call('natural_square_monotone_expanded','f','e')+('exact le_total_right',)
             +_call('gaussian_half_double_square_strict','N','e')+('exact hN','exact he'),
             'The sum of two genuinely half-bounded coordinate squares is strictly below the positive modulus square; no parity or positive-remainder assumption is needed.'),
        spec('gaussian_nearest_signed_quotient_exists',
             f"forall p n N. ~(N = 0) -> exists qp qn ep en t. ({_rounded('p','n','N','qp','qn','ep','en','t','nearest')})",
             ('signed_integer_floor_exists','four_square_descent_centered_signed_remainder_exists','mul_add','add_assoc','mul_zero_left','zero_add'),rounding_script,
             'Construct an actual nearest signed quotient, signed error, and half-bounded magnitude from one floor division and the checked centered natural remainder constructor.'),
    )


def _raw_division(A: tuple[str,...], B: tuple[str,...], Q: tuple[str,...], R: tuple[str,...], remainder_norm: str, divisor_norm: str, tag: str) -> str:
    return _and(
        _complex_equal(_complex_add(_complex_product(B,Q),R),A),
        _norm(*R,remainder_norm,tag+'remainder'),
        _norm(*B,divisor_norm,tag+'divisor'),
        _lt(remainder_norm,divisor_norm,tag+'strict'),
    )


def gaussian_signed_division_remainder_relation(ap: str, an: str, bp: str, bn: str, cp: str, cn: str, dp: str, dn: str, qp: str, qn: str, up: str, un: str, rp: str, rn: str, sp: str, sn: str, remainder_norm: str, divisor_norm: str, *, tag: str) -> str:
    """Actual signed Gaussian a=bq+r and genuinely smaller squared remainder norm."""
    values=_args(ap,an,bp,bn,cp,cn,dp,dn,qp,qn,up,un,rp,rn,sp,sn,remainder_norm,divisor_norm)
    return _raw_division(values[:4],values[4:8],values[8:12],values[12:16],*values[16:],_identifier(tag,'Gaussian division tag'))


def _raw_division_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B=('a','b','c','d'),('e','f','g','h')
    numerator=_complex_product(_conjugate(B),A)
    Q=('x1','x2','x6','x7')
    error=('x3','x4','x8','x9')
    R=_complex_difference(A,_complex_product(B,Q))
    error_expression=_complex_difference(numerator,_scale('x',Q))
    conjugate_residual=_complex_product(_conjugate(B),R)
    sum_squares='x5 * x5 + x10 * x10'
    real='hreal'+'_witness'*5
    imag='himaginary'+'_witness'*5
    script=_intro(*A,*B,'hnonzero')
    script+=(f"have hdivisor : exists N. ({_norm(*B,'N','division_divisor_norm')})",)+_call('gaussian_signed_norm_exists',*B)+('cases hdivisor',)
    script+=('have hN : ~(x = 0)','intro hzero')+_call('gaussian_signed_norm_nonzero',*B,'x')+('exact hdivisor_witness','exact hnonzero','exact hzero')
    script+=(f"have hreal : exists qp qn ep en t. ({_rounded(*numerator[:2],'x','qp','qn','ep','en','t','division_real_round')})",)+_call('gaussian_nearest_signed_quotient_exists',*numerator[:2],'x')+('exact hN',)+_cases('hreal',5)+_parts(real,3)
    script+=(f"have himaginary : exists qp qn ep en t. ({_rounded(*numerator[2:],'x','qp','qn','ep','en','t','division_imaginary_round')})",)+_call('gaussian_nearest_signed_quotient_exists',*numerator[2:],'x')+('exact hN',)+_cases('himaginary',5)+_parts(imag,3)
    script+=(f"have hremainder : exists M. ({_norm(*R,'M','constructed_remainder_norm')})",)+_call('gaussian_signed_norm_exists',*R)+('cases hremainder',)
    script+=(f"have herror_norm : {_norm(*error,sum_squares,'constructed_error_norm')}",)+_exists('x5 * x5','x10 * x10')+('split',f'exact {real}_right_left','split',f'exact {imag}_right_left','refl')
    script+=(f"have herror_equation : {_complex_equal(error_expression,error)}",)+('split',)
    for index,round_hyp in ((0,real),(2,imag)):
        rhs=f"(({numerator[index+1]}) + x * ({Q[index]})) + ({error[index]})"
        script+=(f'trans {rhs}',f'exact {round_hyp}_left','apply add_comm')
    script+=(f"have hconjugate_error : {_complex_equal(conjugate_residual,error)}",)
    script+=_call('gaussian_equal_transitive',*conjugate_residual,*error_expression,*error)
    script+=_call('gaussian_residual_conjugate_identity',*A,*B,*Q,'x')+('exact hdivisor_witness','exact herror_equation')
    script+=(f"have hproduct_norm : {_norm(*conjugate_residual,'x * x11','actual_product_norm')}",)
    script+=_call('gaussian_signed_norm_product',*_conjugate(B),*R,'x','x11')+_call('gaussian_signed_norm_conjugate',*B,'x')+('exact hdivisor_witness','exact hremainder_witness')
    script+=(f"have htransported_norm : {_norm(*error,'x * x11','actual_error_product_norm')}",)+_call('gaussian_signed_norm_integer_transport',*conjugate_residual,*error,'x * x11')+('exact hconjugate_error','exact hproduct_norm')
    script+=(f"have hnorm_equation : x * x11 = {sum_squares}",)+_call('gaussian_signed_norm_functional',*error,'x * x11',sum_squares)+('exact htransported_norm','exact herror_norm')
    script+=(f"have hstrict : {_lt(sum_squares,'x * x','actual_error_strict_bound')}",)+_call('gaussian_two_half_squares_strict','x','x5','x10')+('exact hN',f'exact {real}_right_right',f'exact {imag}_right_right')
    script+=_exists(*Q,*R,'x11','x')+('split',)+_call('gaussian_difference_reconstructs_dividend',*A,*_complex_product(B,Q))+('split','exact hremainder_witness','split','exact hdivisor_witness')
    script+=_call('four_square_descent_norm_bound_forces_smaller_multiplier','x','x11',sum_squares)+('exact hnorm_equation','exact hstrict')
    Qvars,Rvars=('qp','qn','up','un'),('rp','rn','sp','sn')
    return (spec('gaussian_signed_euclidean_division_exists',
                 f"forall {' '.join((*A,*B))}. ~(e = f /\\ g = h) -> exists {' '.join((*Qvars,*Rvars,'U','V'))}. ({_raw_division(A,B,Qvars,Rvars,'U','V','full_signed_division')})",
                 ('gaussian_signed_norm_exists','gaussian_signed_norm_nonzero','gaussian_nearest_signed_quotient_exists','gaussian_equal_transitive','gaussian_residual_conjugate_identity','gaussian_signed_norm_product','gaussian_signed_norm_conjugate','gaussian_signed_norm_integer_transport','gaussian_signed_norm_functional','gaussian_two_half_squares_strict','gaussian_difference_reconstructs_dividend','four_square_descent_norm_bound_forces_smaller_multiplier','add_comm'),
                 script,
                 'Construct a genuine Gaussian quotient and remainder with exact a=bq+r and strict norm decrease for every nonzero divisor; neither quotients nor a remainder bound are assumed.'),)


def _code_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B=('a','b','c','d'),('e','f','g','h')
    same_script=_intro('code','p','n','q','m','hfirst','hsecond')+_cases('hfirst',2)+('cases hfirst_witness_witness',)+_cases('hsecond',2)+('cases hsecond_witness_witness',)
    same_script+=('have hdecoded : x = x2 /\\ x1 = x3',)+_call('signed_decode_functional','code','x','x1','x2','x3')+('exact hfirst_witness_witness_left','exact hsecond_witness_witness_left','cases hdecoded','rewrite hdecoded_left at hfirst_witness_witness_right','rewrite hdecoded_right at hfirst_witness_witness_right')
    same_script+=('have hcross : p + m = n + q',)+_call('add_cross_sum_chain','p','n','x3','x2','m','q')+('exact hfirst_witness_witness_right','trans m + x2','apply add_comm','trans q + x3','symm','exact hsecond_witness_witness_right','apply add_comm','trans n + q','exact hcross','apply add_comm')
    representation_functional_script=_intro('z','w',*A,'hfirst','hsecond')+_cases('hfirst',2)+_parts('hfirst_witness_witness',3)+_cases('hsecond',2)+_parts('hsecond_witness_witness',3)
    representation_functional_script+=('have hreal : x = x2',)+_call('signed_balance_functional',*A[:2],'x','x2')+('exact hfirst_witness_witness_right_left','exact hsecond_witness_witness_right_left')
    representation_functional_script+=('have himaginary : x1 = x3',)+_call('signed_balance_functional',*A[2:],'x1','x3')+('exact hfirst_witness_witness_right_right','exact hsecond_witness_witness_right_right')
    representation_functional_script+=_rewrite('hreal','x',_pair('x','x1'),at='hfirst_witness_witness_left')+_rewrite('himaginary','x1',_pair('x2','x1'),at='hfirst_witness_witness_left')+(f'trans {_pair("x2","x3")}','exact hfirst_witness_witness_left','symm','exact hsecond_witness_witness_left')
    decode_functional_script=_intro('z',*A,*B,'hfirst','hsecond')+_cases('hfirst',2)+_parts('hfirst_witness_witness',3)+_cases('hsecond',2)+_parts('hsecond_witness_witness',3)
    decode_functional_script+=('have hcodes : x = x2 /\\ x1 = x3',)+_call('pair_code_injective','z','x','x1','x2','x3')+('exact hfirst_witness_witness_left','exact hsecond_witness_witness_left','cases hcodes')
    decode_functional_script+=('rewrite hcodes_left at hfirst_witness_witness_right_left',)*2+('rewrite hcodes_right at hfirst_witness_witness_right_right',)*2
    decode_functional_script+=('have hreal : a = e /\\ b = f',)+_call('signed_decode_functional','x2',*A[:2],*B[:2])+('exact hfirst_witness_witness_right_left','exact hsecond_witness_witness_right_left','cases hreal')
    decode_functional_script+=('have himaginary : c = g /\\ d = h',)+_call('signed_decode_functional','x3',*A[2:],*B[2:])+('exact hfirst_witness_witness_right_right','exact hsecond_witness_witness_right_right','cases himaginary','split','exact hreal_left','split','exact hreal_right','split','exact himaginary_left','exact himaginary_right')
    representation_equal_script=_intro('z',*A,*B,'hfirst','hsecond')+_cases('hfirst',2)+_parts('hfirst_witness_witness',3)+_cases('hsecond',2)+_parts('hsecond_witness_witness',3)
    representation_equal_script+=('have hcodes : x = x2 /\\ x1 = x3',)+_call('pair_code_injective','z','x','x1','x2','x3')+('exact hfirst_witness_witness_left','exact hsecond_witness_witness_left','cases hcodes')
    representation_equal_script+=('rewrite hcodes_left at hfirst_witness_witness_right_left',)*2+('rewrite hcodes_right at hfirst_witness_witness_right_right',)*2+('split',)
    representation_equal_script+=_call('gaussian_signed_balance_same_code','x2',*A[:2],*B[:2])+('exact hfirst_witness_witness_right_left','exact hsecond_witness_witness_right_left')
    representation_equal_script+=_call('gaussian_signed_balance_same_code','x3',*A[2:],*B[2:])+('exact hfirst_witness_witness_right_right','exact hsecond_witness_witness_right_right')
    representation_decode_script=_intro('z',*A,'hrepresentation')+_cases('hrepresentation',2)+_parts('hrepresentation_witness_witness',3)
    representation_decode_script+=_cases('hrepresentation_witness_witness_right_left',2)+('cases hrepresentation_witness_witness_right_left_witness_witness',)
    representation_decode_script+=_cases('hrepresentation_witness_witness_right_right',2)+('cases hrepresentation_witness_witness_right_right_witness_witness',)
    representation_decode_script+=_exists('x2','x3','x4','x5')+('split',)+_exists('x','x1')+('split','exact hrepresentation_witness_witness_left','split','exact hrepresentation_witness_witness_right_left_witness_witness_left','exact hrepresentation_witness_witness_right_right_witness_witness_left','split','trans b + x2','exact hrepresentation_witness_witness_right_left_witness_witness_right','apply add_comm','trans d + x4','exact hrepresentation_witness_witness_right_right_witness_witness_right','apply add_comm')
    return (
        spec('gaussian_signed_balance_integer_transport',
             f"forall code p n q m. ({_equal('p','n','q','m')}) -> ({_balance('code','p','n','balance_source')}) -> ({_balance('code','q','m','balance_target')})",
             ('integer_span_pair_equal_transitive','add_comm'),
             _intro('code','p','n','q','m','hequal','hbalance')+_cases('hbalance',2)+('cases hbalance_witness_witness',)
             +('have htransport : q + x1 = x + m',)+_call('integer_span_pair_equal_transitive','q','m','p','n','x','x1')+('symm','exact hequal','trans n + x','exact hbalance_witness_witness_right','apply add_comm')
             +_exists('x','x1')+('split','exact hbalance_witness_witness_left','trans x + m','exact htransport','apply add_comm'),
             'The unchanged canonical signed code continues to represent every equal signed difference.'),
        spec('gaussian_signed_balance_same_code',
             f"forall code p n q m. ({_balance('code','p','n','same_code_first')}) -> ({_balance('code','q','m','same_code_second')}) -> ({_equal('p','n','q','m')})",
             ('signed_decode_functional','add_cross_sum_chain','add_comm'),same_script,
             'Two signed pairs represented by the same historic canonical integer code are genuinely equal integers.'),
        spec('gaussian_decode_from_signed_codes',
             f"forall rc ic {' '.join(A)}. ({_sd('rc',*A[:2],'from_signed_real')}) -> ({_sd('ic',*A[2:],'from_signed_imaginary')}) -> exists z. ({_decode('z',*A,'from_signed_codes')})",
             (),_intro('rc','ic',*A,'hreal','himaginary')+_exists(_pair('rc','ic'),'rc','ic')+('split','refl','split','exact hreal','exact himaginary'),
             'Pair two actual normalized signed-integer codes into their genuine canonical natural Gaussian coordinate code.'),
        spec('gaussian_decode_functional',
             f"forall z {' '.join((*A,*B))}. ({_decode('z',*A,'decode_first')}) -> ({_decode('z',*B,'decode_second')}) -> ({_components(A,B)})",
             ('pair_code_injective','signed_decode_functional'),decode_functional_script,
             'A canonical Gaussian coordinate code has exactly one normalized four-component signed decoding.'),
        spec('gaussian_representation_exists',f"forall {' '.join(A)}. exists z. ({_rep('z',*A,'representation_total')})",
             ('signed_balance_total',),_intro(*A)+(f"have hreal : exists rc. ({_balance('rc',*A[:2],'representation_real_exists')})",)+_call('signed_balance_total',*A[:2])+('cases hreal',)
             +(f"have himaginary : exists ic. ({_balance('ic',*A[2:],'representation_imaginary_exists')})",)+_call('signed_balance_total',*A[2:])+('cases himaginary',)
             +_exists(_pair('x','x1'),'x','x1')+('split','refl','split','exact hreal_witness','exact himaginary_witness'),
             'Every pair of arbitrary represented integers has an actually constructed canonical natural Gaussian code.'),
        spec('gaussian_representation_functional',
             f"forall z w {' '.join(A)}. ({_rep('z',*A,'representation_first')}) -> ({_rep('w',*A,'representation_second')}) -> z = w",
             ('signed_balance_functional',),representation_functional_script,
             'The canonical Gaussian natural code representing two specified integer differences is unique.'),
        spec('gaussian_representation_integer_transport',
             f"forall z {' '.join((*A,*B))}. ({_complex_equal(A,B)}) -> ({_rep('z',*A,'representation_transport_source')}) -> ({_rep('z',*B,'representation_transport_target')})",
             ('gaussian_signed_balance_integer_transport',),_intro('z',*A,*B,'hequal','hrepresentation')+('cases hequal',)+_cases('hrepresentation',2)+_parts('hrepresentation_witness_witness',3)+_exists('x','x1')+('split','exact hrepresentation_witness_witness_left','split')
             +_call('gaussian_signed_balance_integer_transport','x',*A[:2],*B[:2])+('exact hequal_left','exact hrepresentation_witness_witness_right_left')
             +_call('gaussian_signed_balance_integer_transport','x1',*A[2:],*B[2:])+('exact hequal_right','exact hrepresentation_witness_witness_right_right'),
             'A canonical Gaussian coordinate code is invariant under arbitrary equal signed representatives.'),
        spec('gaussian_representation_equal',
             f"forall z {' '.join((*A,*B))}. ({_rep('z',*A,'same_gaussian_code_first')}) -> ({_rep('z',*B,'same_gaussian_code_second')}) -> ({_complex_equal(A,B)})",
             ('pair_code_injective','gaussian_signed_balance_same_code'),representation_equal_script,
             'Any two signed representatives of the same canonical Gaussian natural code denote the same Gaussian integer.'),
        spec('gaussian_representation_decode',
             f"forall z {' '.join(A)}. ({_rep('z',*A,'normalization_source')}) -> exists {' '.join(B)}. ({_and(_decode('z',*B,'normalization_decode'),_complex_equal(A,B))})",
             ('add_comm',),representation_decode_script,
             'Every possibly overlapping signed representation yields actual unique normalized decoder coordinates of the same canonical code.'),
        spec('gaussian_decode_representation',
             f"forall z {' '.join(A)}. ({_decode('z',*A,'decoded_representation')}) -> ({_rep('z',*A,'decoded_representation_target')})",
             ('signed_decode_to_balance',),_intro('z',*A,'hdecode')+_cases('hdecode',2)+_parts('hdecode_witness_witness',3)+_exists('x','x1')+('split','exact hdecode_witness_witness_left','split')
             +_call('signed_decode_to_balance','x',*A[:2])+('exact hdecode_witness_witness_right_left',)+_call('signed_decode_to_balance','x1',*A[2:])+('exact hdecode_witness_witness_right_right',),
             'Every normalized Gaussian decoding also represents its two actual integer coordinates.'),
        spec('gaussian_representation_is_gaussian',
             f"forall z {' '.join(A)}. ({_rep('z',*A,'valid_representation')}) -> ({_gaussian('z','valid_gaussian')})",
             ('gaussian_representation_decode',),_intro('z',*A,'hrepresentation')+(f"have hdecode : exists {' '.join(B)}. ({_and(_decode('z',*B,'valid_normalized_decode'),_complex_equal(A,B))})",)
             +_call('gaussian_representation_decode','z',*A)+('exact hrepresentation',)+_cases('hdecode',4)+('cases hdecode_witness_witness_witness_witness',)+_exists('x','x1','x2','x3')+('exact hdecode_witness_witness_witness_witness_left',),
             'A genuinely represented pair always belongs to the canonical signed-coordinate Gaussian carrier.'),
    )


def _zero_and_signed_bridge_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A=('a','b','c','d')
    zeroscript=_intro('z',*A,'hrep')+_cases('hrep',2)+_parts('hrep_witness_witness',3)
    zeroscript+=('have hreal : (x = 0 -> a = b) /\\ (a = b -> x = 0)',)+_call('signed_balance_zero_iff','x','a','b')+('exact hrep_witness_witness_right_left','cases hreal')
    zeroscript+=('have himaginary : (x1 = 0 -> c = d) /\\ (c = d -> x1 = 0)',)+_call('signed_balance_zero_iff','x1','c','d')+('exact hrep_witness_witness_right_right','cases himaginary','split','intro hzero','have hcodes : x = 0 /\\ x1 = 0')
    zeroscript+=_call('gaussian_pair_zero_codes','z','x','x1')+('exact hrep_witness_witness_left','exact hzero','cases hcodes','split','apply hreal_left','exact hcodes_left','apply himaginary_left','exact hcodes_right','intro hequal','cases hequal','have hrealzero : x = 0','apply hreal_right','exact hequal_left','have himaginaryzero : x1 = 0','apply himaginary_right','exact hequal_right',f'trans {_pair("x","x1")}','exact hrep_witness_witness_left')+_simp('hrealzero','himaginaryzero','mul_zero_left','zero_add')
    rows=[
        spec('gaussian_pair_zero_codes',f"forall z rc ic. z = {_pair('rc','ic')} -> z = 0 -> rc = 0 /\\ ic = 0",
             ('pair_code_injective','mul_zero_left','zero_add'),_intro('z','rc','ic','hpair','hzero')+_call('pair_code_injective','z','rc','ic','0','0')+('exact hpair','rewrite hzero')+_simp('mul_zero_left','zero_add'),
             'The zero canonical pair code has exactly zero real and imaginary signed codes.'),
        spec('gaussian_representation_zero_iff',f"forall z {' '.join(A)}. ({_rep('z',*A,'representation_zero')}) -> ((z = 0 -> (a = b /\\ c = d)) /\\ ((a = b /\\ c = d) -> z = 0))",
             ('signed_balance_zero_iff','gaussian_pair_zero_codes','mul_zero_left','zero_add'),zeroscript,
             'A canonical signed-coordinate pair is zero exactly when both represented integer differences vanish, even for overlapping raw representatives.'),
        spec('gaussian_decode_zero_iff',f"forall z {' '.join(A)}. ({_decode('z',*A,'decode_zero')}) -> ((z = 0 -> (a = b /\\ c = d)) /\\ ((a = b /\\ c = d) -> z = 0))",
             ('gaussian_decode_representation','gaussian_representation_zero_iff'),_intro('z',*A,'hdecode')+_call('gaussian_representation_zero_iff','z',*A)+_call('gaussian_decode_representation','z',*A)+('exact hdecode',),
             'The unchanged normalized signed-coordinate decoding detects the zero pair code in both directions.'),
    ]
    for operation,graph,congruence in (('add',signed_add,'integer_span_pair_add_congruence'),('mul',signed_mul,'matrix_integer_pair_product_balance')):
        raw=(_add('p','q'),_add('n','m')) if operation=='add' else _product('p','n','q','m')
        normalized=(_add('x','x2'),_add('x1','x3')) if operation=='add' else _product('x','x1','x2','x3')
        congruence_args=('p','n','q','m','x','x1','x2','x3') if operation=='add' else ('p','n','x','x1','q','m','x2','x3')
        script=_intro('ac','bc','cc','p','n','q','m','hfirst','hsecond','houtput')+_cases('hfirst',2)+('cases hfirst_witness_witness',)+_cases('hsecond',2)+('cases hsecond_witness_witness',)
        script+=(f"have hequal : {_equal(*raw,*normalized)}",)+_call(congruence,*congruence_args)+('trans n + x','exact hfirst_witness_witness_right','apply add_comm','trans m + x2','exact hsecond_witness_witness_right','apply add_comm')
        script+=(f"have hnormalized : {_balance('cc',*normalized,'signed_bridge_normalized_'+operation)}",)+_call('gaussian_signed_balance_integer_transport','cc',*raw,*normalized)+('exact hequal','exact houtput')+_cases('hnormalized',2)+('cases hnormalized_witness_witness',)
        script+=_call('signed_'+operation+'_of_decoded_equation','ac','bc','cc','x','x1','x2','x3','x4','x5')+('exact hfirst_witness_witness_left','exact hsecond_witness_witness_left','exact hnormalized_witness_witness_left','exact hnormalized_witness_witness_right')
        rows.append(spec('gaussian_signed_'+operation+'_of_balances',
                         f"forall ac bc cc p n q m. ({_balance('ac','p','n','bridge_first_'+operation)}) -> ({_balance('bc','q','m','bridge_second_'+operation)}) -> ({_balance('cc',*raw,'bridge_output_'+operation)}) -> ({graph('ac','bc','cc',tag='gaussian_bridge_'+operation)})",
                         (congruence,'gaussian_signed_balance_integer_transport','signed_'+operation+'_of_decoded_equation','add_comm'),script,
                         'Actual arbitrary signed-pair '+operation+' contribution balances construct the unchanged historic canonical signed-'+operation+' graph.'))
        elimination=_intro('ac','bc','cc','p','n','q','m','hfirst','hsecond','hoperation')+(f"have houtput : exists output. ({_balance('output',*raw,'signed_bridge_construct_'+operation)})",)+_call('signed_balance_total',*raw)+('cases houtput','have hequal : cc = x')
        elimination+=_call('signed_'+operation+'_functional','ac','bc','cc','x')+('exact hoperation',)+_call('gaussian_signed_'+operation+'_of_balances','ac','bc','x','p','n','q','m')+('exact hfirst','exact hsecond','exact houtput_witness')
        elimination+=_rewrite('hequal','cc',_balance('cc',*raw,'signed_bridge_elimination_'+operation))+('exact houtput_witness',)
        rows.append(spec('gaussian_signed_'+operation+'_to_balance',
                         f"forall ac bc cc p n q m. ({_balance('ac','p','n','bridge_elim_first_'+operation)}) -> ({_balance('bc','q','m','bridge_elim_second_'+operation)}) -> ({graph('ac','bc','cc',tag='gaussian_bridge_elim_'+operation)}) -> ({_balance('cc',*raw,'signed_bridge_elimination_'+operation)})",
                         ('signed_balance_total','signed_'+operation+'_functional','gaussian_signed_'+operation+'_of_balances'),elimination,
                         'The unchanged historic signed-'+operation+' graph has the exact arbitrary-representative contribution balance; this proves the converse rather than an unproved notation alias.'))
    return tuple(rows)


def _coded_arithmetic_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B=('a','b','c','d'),('e','f','g','h')
    X,Y=('x','x1','x2','x3'),('x4','x5','x6','x7')
    norm_for_rep=_intro('z',*A,'N','hrep','hnorm')+_cases('hnorm',4)+('cases hnorm_witness_witness_witness_witness',)
    norm_for_rep+=_call('gaussian_signed_norm_integer_transport',*X,*A,'N')+_call('gaussian_representation_equal','z',*X,*A)+('exact hnorm_witness_witness_witness_witness_left','exact hrep','exact hnorm_witness_witness_witness_witness_right')
    norm_exists=_intro('z','hvalid')+_cases('hvalid',4)+(f"have hnorm : exists N. ({_norm(*X,'N','code_norm_construct')})",)+_call('gaussian_signed_norm_exists',*X)+('cases hnorm','exists x4')
    norm_exists+=_call('gaussian_norm_of_representation','z',*X,'x4')+_call('gaussian_decode_representation','z',*X)+('exact hvalid_witness_witness_witness_witness','exact hnorm_witness')
    norm_unique=_intro('z','N','M','hfirst','hsecond')+_cases('hfirst',4)+('cases hfirst_witness_witness_witness_witness',)
    norm_unique+=_call('gaussian_signed_norm_functional',*X,'N','M')+('exact hfirst_witness_witness_witness_witness_right',)+_call('gaussian_norm_for_representation','z',*X,'M')+('exact hfirst_witness_witness_witness_witness_left','exact hsecond')
    C,D=('i','j','k','l'),('o','p','q','r')
    add_congruence=_intro(*A,*B,*C,*D,'hfirst','hsecond')+('cases hfirst','cases hsecond','split')
    for offset in (0,2):
        side='left' if offset==0 else 'right'
        add_congruence+=_call('integer_span_pair_add_congruence',*A[offset:offset+2],*B[offset:offset+2],*C[offset:offset+2],*D[offset:offset+2])+(f'exact hfirst_{side}',f'exact hsecond_{side}')
    unique_norm=_and(_code_norm('z','N','norm_total_unique_witness'),f"forall M. ({_code_norm('z','M','norm_total_unique_compare')}) -> M = N")
    rows=[
        spec('gaussian_norm_of_representation',f"forall z {' '.join(A)} N. ({_rep('z',*A,'norm_intro_rep')}) -> ({_norm(*A,'N','norm_intro_raw')}) -> ({_code_norm('z','N','norm_intro_code')})",
             (),_intro('z',*A,'N','hrep','hnorm')+_exists(*A)+('split','exact hrep','exact hnorm'),
             'An actual represented pair and its actual squared modulus construct the canonical Gaussian norm graph.'),
        spec('gaussian_norm_for_representation',f"forall z {' '.join(A)} N. ({_rep('z',*A,'norm_fixed_rep')}) -> ({_code_norm('z','N','norm_fixed_code')}) -> ({_norm(*A,'N','norm_fixed_raw')})",
             ('gaussian_signed_norm_integer_transport','gaussian_representation_equal'),norm_for_rep,
             'The canonical norm is the actual squared modulus of every equal signed representative, not merely its selected witness.'),
        spec('gaussian_norm_exists',f"forall z. ({_gaussian('z','norm_exists_input')}) -> exists N. ({_code_norm('z','N','norm_exists_output')})",
             ('gaussian_signed_norm_exists','gaussian_norm_of_representation','gaussian_decode_representation'),norm_exists,
             'Construct the actual natural squared norm of every canonical Gaussian integer, with zero and units included.'),
        spec('gaussian_norm_functional',f"forall z N M. ({_code_norm('z','N','norm_unique_first')}) -> ({_code_norm('z','M','norm_unique_second')}) -> N = M",
             ('gaussian_signed_norm_functional','gaussian_norm_for_representation'),norm_unique,
             'The actual canonical Gaussian squared norm is unique across all arbitrary signed representatives.'),
        spec('gaussian_norm_exists_unique',f"forall z. ({_gaussian('z','norm_total_unique_input')}) -> exists N. ({unique_norm})",
             ('gaussian_norm_exists','gaussian_norm_functional'),_intro('z','hvalid')+(f"have hnorm : exists N. ({_code_norm('z','N','norm_total_unique_construct')})",)+_call('gaussian_norm_exists','z')+('exact hvalid','cases hnorm','exists x','split','exact hnorm_witness','intro M','intro hother')+_call('gaussian_norm_functional','z','M','x')+('exact hother','exact hnorm_witness'),
             'Every canonical Gaussian integer has one genuinely constructed and uniquely determined natural squared norm.'),
        spec('gaussian_sum_integer_congruence',f"forall {' '.join((*A,*B,*C,*D))}. ({_complex_equal(A,C)}) -> ({_complex_equal(B,D)}) -> ({_complex_equal(_complex_add(A,B),_complex_add(C,D))})",
             ('integer_span_pair_add_congruence',),add_congruence,
             'Actual complex addition respects represented integer equality in both coordinates and both inputs.'),
    ]
    for label,graph,operation,congruence in (
        ('add',_code_add,_complex_add,'gaussian_sum_integer_congruence'),
        ('multiply',_code_mul,_complex_product,'gaussian_product_integer_congruence'),
    ):
        output=operation(A,B)
        raw_output=operation(X,Y)
        intro_name='gaussian_'+label+'_of_representations'
        fixed_name='gaussian_'+label+'_for_representations'
        fixed_script=_intro('ac','bc','cc',*A,*B,'hfirst','hsecond','hoperation')+_cases('hoperation',8)+_parts('hoperation'+'_witness'*8,3)
        congruence_arguments=(*X,*Y,*A,*B) if label=='add' else (*X,*A,*Y,*B)
        fixed_script+=_call('gaussian_representation_integer_transport','cc',*raw_output,*output)+_call(congruence,*congruence_arguments)
        fixed_script+=_call('gaussian_representation_equal','ac',*X,*A)+(f"exact {_part('hoperation'+'_witness'*8,3,0)}",'exact hfirst')
        fixed_script+=_call('gaussian_representation_equal','bc',*Y,*B)+(f"exact {_part('hoperation'+'_witness'*8,3,1)}",'exact hsecond',f"exact {_part('hoperation'+'_witness'*8,3,2)}")
        exists_script=_intro('ac','bc','hfirst','hsecond')+_cases('hfirst',4)+_cases('hsecond',4)
        exists_script+=(f"have houtput : exists cc. ({_rep('cc',*raw_output,label+'_construct_output')})",)+_call('gaussian_representation_exists',*raw_output)+('cases houtput','exists x8')
        exists_script+=_call(intro_name,'ac','bc','x8',*X,*Y)+_call('gaussian_decode_representation','ac',*X)+('exact hfirst_witness_witness_witness_witness',)+_call('gaussian_decode_representation','bc',*Y)+('exact hsecond_witness_witness_witness_witness','exact houtput_witness')
        functional_script=_intro('ac','bc','cc','dd','hfirst','hsecond')+_cases('hfirst',8)+_parts('hfirst'+'_witness'*8,3)
        functional_script+=_call('gaussian_representation_functional','cc','dd',*raw_output)+(f"exact {_part('hfirst'+'_witness'*8,3,2)}",)+_call(fixed_name,'ac','bc','dd',*X,*Y)+(f"exact {_part('hfirst'+'_witness'*8,3,0)}",f"exact {_part('hfirst'+'_witness'*8,3,1)}",'exact hsecond')
        rows.extend((
            spec(intro_name,f"forall ac bc cc {' '.join((*A,*B))}. ({_rep('ac',*A,label+'_intro_first')}) -> ({_rep('bc',*B,label+'_intro_second')}) -> ({_rep('cc',*output,label+'_intro_output')}) -> ({graph('ac','bc','cc',label+'_intro_graph')})",
                 (),_intro('ac','bc','cc',*A,*B,'hfirst','hsecond','houtput')+_exists(*A,*B)+('split','exact hfirst','split','exact hsecond','exact houtput'),
                 'Actual signed-coordinate '+label+' representatives construct the canonical Gaussian operation graph.'),
            spec(fixed_name,f"forall ac bc cc {' '.join((*A,*B))}. ({_rep('ac',*A,label+'_fixed_first')}) -> ({_rep('bc',*B,label+'_fixed_second')}) -> ({graph('ac','bc','cc',label+'_fixed_graph')}) -> ({_rep('cc',*output,label+'_fixed_output')})",
                 ('gaussian_representation_integer_transport',congruence,'gaussian_representation_equal'),fixed_script,
                 'The canonical Gaussian '+label+' graph agrees with actual arithmetic on every chosen integer representative.'),
            spec('gaussian_'+label+'_exists',f"forall ac bc. ({_gaussian('ac',label+'_total_first')}) -> ({_gaussian('bc',label+'_total_second')}) -> exists cc. ({graph('ac','bc','cc',label+'_total_output')})",
                 ('gaussian_representation_exists',intro_name,'gaussian_decode_representation'),exists_script,
                 'Construct an actual canonical Gaussian '+label+' output for every pair of valid canonical Gaussian inputs.'),
            spec('gaussian_'+label+'_functional',f"forall ac bc cc dd. ({graph('ac','bc','cc',label+'_unique_first')}) -> ({graph('ac','bc','dd',label+'_unique_second')}) -> cc = dd",
                 ('gaussian_representation_functional',fixed_name),functional_script,
                 'Actual Gaussian '+label+' has one literal canonical natural output code, independent of all representative choices.'),
        ))
    norm_multiply=_intro('ac','bc','cc','N','M','hfirst','hsecond','hproduct')+_cases('hproduct',8)+_parts('hproduct'+'_witness'*8,3)
    norm_multiply+=_call('gaussian_norm_of_representation','cc',*_complex_product(X,Y),'N * M')+(f"exact {_part('hproduct'+'_witness'*8,3,2)}",)
    norm_multiply+=_call('gaussian_signed_norm_product',*X,*Y,'N','M')+_call('gaussian_norm_for_representation','ac',*X,'N')+(f"exact {_part('hproduct'+'_witness'*8,3,0)}",'exact hfirst')+_call('gaussian_norm_for_representation','bc',*Y,'M')+(f"exact {_part('hproduct'+'_witness'*8,3,1)}",'exact hsecond')
    rows.append(spec('gaussian_norm_multiply',f"forall ac bc cc N M. ({_code_norm('ac','N','norm_product_first')}) -> ({_code_norm('bc','M','norm_product_second')}) -> ({_code_mul('ac','bc','cc','norm_product_operation')}) -> ({_code_norm('cc','N * M','norm_product_output')})",
                     ('gaussian_norm_of_representation','gaussian_signed_norm_product','gaussian_norm_for_representation'),norm_multiply,
                     'The actual squared norm of a canonical Gaussian product equals the product of its actual natural squared norms.'))
    return tuple(rows)


def _coded_division_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B,Q,R=('a','b','c','d'),('e','f','g','h'),('i','j','k','l'),('o','p','s','t')
    product=_complex_product(B,Q)
    reconstruction=_complex_add(product,R)
    reconstruction_script=_intro('ac','bc','qc','rc',*A,*B,*Q,*R,'hfirst','hsecond','hquotient','hremainder','hequation')
    reconstruction_script+=(f"have hproduct : exists pc. ({_rep('pc',*product,'division_product_construct')})",)+_call('gaussian_representation_exists',*product)+('cases hproduct','exists x','split')
    reconstruction_script+=_call('gaussian_multiply_of_representations','bc','qc','x',*B,*Q)+('exact hsecond','exact hquotient','exact hproduct_witness')
    reconstruction_script+=_call('gaussian_add_of_representations','x','rc','ac',*product,*R)+('exact hproduct_witness','exact hremainder')
    reconstruction_script+=_call('gaussian_representation_integer_transport','ac',*A,*reconstruction)+_call('gaussian_equal_symmetric',*reconstruction,*A)+('exact hequation','exact hfirst')
    X,Y=('x','x1','x2','x3'),('x4','x5','x6','x7')
    quotient,remainder=('x8','x9','x10','x11'),('x12','x13','x14','x15')
    raw_name='hdivision'+'_witness'*10
    script=_intro('ac','bc','hfirst','hsecond','hnonzero')+_cases('hfirst',4)+_cases('hsecond',4)
    script+=(f"have hA : {_rep('ac',*X,'euclidean_dividend_rep')}",)+_call('gaussian_decode_representation','ac',*X)+('exact hfirst_witness_witness_witness_witness',)
    script+=(f"have hB : {_rep('bc',*Y,'euclidean_divisor_rep')}",)+_call('gaussian_decode_representation','bc',*Y)+('exact hsecond_witness_witness_witness_witness',)
    script+=('have hzero : (bc = 0 -> (x4 = x5 /\\ x6 = x7)) /\\ ((x4 = x5 /\\ x6 = x7) -> bc = 0)',)+_call('gaussian_representation_zero_iff','bc',*Y)+('exact hB','cases hzero','have hraw_nonzero : ~(x4 = x5 /\\ x6 = x7)','intro hvanishing','apply hnonzero','apply hzero_right','exact hvanishing')
    script+=(f"have hdivision : exists {' '.join((*Q,*R,'U','V'))}. ({_raw_division(X,Y,Q,R,'U','V','euclidean_raw_construct')})",)+_call('gaussian_signed_euclidean_division_exists',*X,*Y)+('exact hraw_nonzero',)+_cases('hdivision',10)+_parts(raw_name,4)
    script+=(f"have hQ : exists qc. ({_rep('qc',*quotient,'euclidean_quotient_construct')})",)+_call('gaussian_representation_exists',*quotient)+('cases hQ',)
    script+=(f"have hR : exists rc. ({_rep('rc',*remainder,'euclidean_remainder_construct')})",)+_call('gaussian_representation_exists',*remainder)+('cases hR',)
    script+=_exists('x18','x19','x16','x17')+('split',)+_call('gaussian_representation_is_gaussian','x18',*quotient)+('exact hQ_witness','split')+_call('gaussian_representation_is_gaussian','x19',*remainder)+('exact hR_witness','split')
    script+=_call('gaussian_division_remainder_of_representations','ac','bc','x18','x19',*X,*Y,*quotient,*remainder)+('exact hA','exact hB','exact hQ_witness','exact hR_witness',f'exact {_part(raw_name,4,0)}','split')
    script+=_call('gaussian_norm_of_representation','x19',*remainder,'x16')+('exact hR_witness',f'exact {_part(raw_name,4,1)}','split')
    script+=_call('gaussian_norm_of_representation','bc',*Y,'x17')+('exact hB',f'exact {_part(raw_name,4,2)}',f'exact {_part(raw_name,4,3)}')
    return (
        spec('gaussian_division_remainder_of_representations',f"forall ac bc qc rc {' '.join((*A,*B,*Q,*R))}. ({_rep('ac',*A,'equation_first_rep')}) -> ({_rep('bc',*B,'equation_second_rep')}) -> ({_rep('qc',*Q,'equation_quotient_rep')}) -> ({_rep('rc',*R,'equation_remainder_rep')}) -> ({_complex_equal(reconstruction,A)}) -> ({_code_divrem('ac','bc','qc','rc','equation_code_graph')})",
             ('gaussian_representation_exists','gaussian_multiply_of_representations','gaussian_add_of_representations','gaussian_representation_integer_transport','gaussian_equal_symmetric'),reconstruction_script,
             'The actual arbitrary signed-coordinate equation a=bq+r yields the genuine canonical Gaussian multiplication-and-addition graph.'),
        spec('gaussian_euclidean_division_exists',f"forall ac bc. ({_gaussian('ac','euclidean_input_dividend')}) -> ({_gaussian('bc','euclidean_input_divisor')}) -> ~(bc = 0) -> exists qc rc U V. ({_code_euclidean('ac','bc','qc','rc','U','V','euclidean_canonical_output')})",
             ('gaussian_decode_representation','gaussian_representation_zero_iff','gaussian_signed_euclidean_division_exists','gaussian_representation_exists','gaussian_representation_is_gaussian','gaussian_division_remainder_of_representations','gaussian_norm_of_representation'),script,
             'Full constructive Gaussian Euclidean division: every canonical dividend and nonzero canonical divisor produce actual canonical quotient and remainder codes satisfying a=bq+r and strict decrease of their actual squared norms.'),
    )


__all__ = [
    "signed_difference_square_relation", "gaussian_signed_norm_relation",
    "gaussian_decode_relation", "gaussian_integer_relation",
    "gaussian_rounded_signed_division_relation",
    "gaussian_signed_division_remainder_relation",
    "gaussian_representation_relation",
    "gaussian_norm_relation", "gaussian_add_relation", "gaussian_multiply_relation",
    "gaussian_division_remainder_relation", "gaussian_euclidean_division_relation",
    "make_gaussian_euclidean_candidate_theorems",
]
