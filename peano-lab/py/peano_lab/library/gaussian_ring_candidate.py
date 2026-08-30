"""Additive Gaussian ring, unit and divisibility proofs over frozen G081.

The carrier and arithmetic are the actual canonical signed-pair graphs.
The multiplicative identity is code 6, representing 1+0i; natural code 1
is not a Gaussian integer.  All definitions below are conservative graphs.
This file is an authoring candidate, not an Alpha admission certificate.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from ..kernel.formulas import parse_formula_in_context
from ..kernel.terms import parse_term_in_context, pretty_term
from .finite_fold_surface import _identifier
from . import gaussian_euclidean_candidate as ge


_mul=ge._code_mul
_add=ge._code_add
_valid=ge._gaussian
_norm=ge._code_norm
_rep=ge._rep
_parts=ge._parts
_part=ge._part
_cases=ge._cases
_and=ge._and


def _call(name: str, *arguments: str) -> tuple[str,...]:
    return (*(f"specialize {name} ({argument})" for argument in arguments),f"apply {name}")


def _intro(*names: str) -> tuple[str,...]:
    return tuple(f"intro {name}" for name in names)


def _exists(*terms: str) -> tuple[str,...]:
    return tuple(f"exists ({term})" for term in terms)


def _names(tag: str, *roles: str) -> tuple[str,...]:
    _identifier(tag,"Gaussian ring definition tag")
    return tuple(f"gr_{role}_{tag}" for role in roles)


def _dvd(divisor: str, value: str, tag: str) -> str:
    q,=_names(tag,"quotient")
    return f"exists {q}. ({_mul(divisor,q,value,tag+'product')})"


def _unit(value: str, tag: str) -> str:
    inverse,=_names(tag,"inverse")
    return f"exists {inverse}. ({_mul(value,inverse,'6',tag+'identity')})"


def _associate(first: str, second: str, tag: str) -> str:
    unit,=_names(tag,"unit")
    return f"exists {unit}. " + _and(_unit(unit,tag+'unit'),_mul(unit,first,second,tag+'transport'))


def _irreducible(value: str, tag: str) -> str:
    a,b=_names(tag,"first_factor","second_factor")
    return _and(_valid(value,tag+'carrier'),f"~(({value})=0)",f"~({_unit(value,tag+'nonunit')})",
                f"forall {a} {b}. ({_mul(a,b,value,tag+'factorization')}) -> ({_unit(a,tag+'first_unit')}) \\/ ({_unit(b,tag+'second_unit')})")


def _prime(value: str, tag: str) -> str:
    a,b,c=_names(tag,"first_factor","second_factor","product")
    return _and(_valid(value,tag+'carrier'),f"~(({value})=0)",f"~({_unit(value,tag+'nonunit')})",
                f"forall {a} {b} {c}. ({_mul(a,b,c,tag+'product')}) -> ({_dvd(value,c,tag+'divisor')}) -> ({_dvd(value,a,tag+'first_divisor')}) \\/ ({_dvd(value,b,tag+'second_divisor')})")


def _definition(builder: Callable[...,str], arguments: tuple[str,...], *, tag: str, variables: tuple[str,...]) -> str:
    if not isinstance(variables,tuple) or not variables:
        raise ValueError("Gaussian ring context must be a nonempty tuple")
    context=tuple(_identifier(name,"Gaussian ring context variable") for name in variables)
    if len(set(context))!=len(context):
        raise ValueError("Gaussian ring context variables must be distinct")
    terms=tuple(parse_term_in_context(argument,list(context)) for argument in arguments)
    sources=tuple("("+pretty_term(term,list(context)).replace("·","*")+")" for term in terms)
    formula=builder(*sources,_identifier(tag,"Gaussian ring definition tag"))
    binders={name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.",formula) for name in clause.split()}
    if binders.intersection(context):
        raise ValueError("Gaussian ring definition binder captures a context variable")
    parse_formula_in_context(formula,list(context))
    return formula


def gaussian_divides_relation(divisor: str, value: str, *, tag: str, variables: tuple[str,...]) -> str:
    """An actual Gaussian quotient multiplies the divisor to the value."""
    return _definition(_dvd,(divisor,value),tag=tag,variables=variables)


def gaussian_unit_relation(value: str, *, tag: str, variables: tuple[str,...]) -> str:
    """An actual Gaussian multiplicative inverse yields canonical identity code 6."""
    return _definition(_unit,(value,),tag=tag,variables=variables)


def gaussian_associate_relation(first: str, second: str, *, tag: str, variables: tuple[str,...]) -> str:
    """A witnessed actual Gaussian unit transports first to second."""
    return _definition(_associate,(first,second),tag=tag,variables=variables)


def gaussian_irreducible_relation(value: str, *, tag: str, variables: tuple[str,...]) -> str:
    """A valid nonzero nonunit with a unit factor in every actual factorization."""
    return _definition(_irreducible,(value,),tag=tag,variables=variables)


def gaussian_prime_relation(value: str, *, tag: str, variables: tuple[str,...]) -> str:
    """A valid nonzero nonunit satisfying the actual Gaussian prime-divisor property."""
    return _definition(_prime,(value,),tag=tag,variables=variables)


def _carrier_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    X,Y=('x','x1','x2','x3'),('x4','x5','x6','x7')
    A=('ap','an','bp','bn')
    rows=[
        spec(
            "gaussian_valid_has_representation",
            f"forall z. ({_valid('z','ring_valid')}) -> exists ap an bp bn. ({_rep('z',*A,'ring_representation')})",
            ("gaussian_decode_representation",),
            _intro('z','h')+_cases('h',4)+_exists(*X)+_call('gaussian_decode_representation','z',*X)+('exact h_witness_witness_witness_witness',),
            "Every valid canonical Gaussian code has actual signed-coordinate representatives.",
        ),
        spec(
            "gaussian_code_representation_transport",
            f"forall z w {' '.join(A)}. z=w -> ({_rep('z',*A,'ring_old_code')}) -> ({_rep('w',*A,'ring_new_code')})",
            (),
            _intro('z','w',*A,'heq','h')+('rewrite heq at h','exact h'),
            "Proved equality of canonical natural codes preserves the actual signed representation.",
        ),
        spec(
            "gaussian_norm_input_valid",
            f"forall z N. ({_norm('z','N','ring_norm')}) -> ({_valid('z','ring_norm_domain')})",
            ("gaussian_representation_is_gaussian",),
            _intro('z','N','h')+_cases('h',4)+('cases h_witness_witness_witness_witness',)+_call('gaussian_representation_is_gaussian','z',*X)+('exact h_witness_witness_witness_witness_left',),
            "An actual norm witness certifies membership in the Gaussian carrier.",
        ),
    ]
    for label,graph,operation in (('add',_add,ge._complex_add),('multiply',_mul,ge._complex_product)):
        for role,index,code,coordinates in (('input_left',0,'a',X),('input_right',1,'b',Y),('output',2,'c',operation(X,Y))):
            rows.append(spec(
                f"gaussian_{label}_{role}_valid",
                f"forall a b c. ({graph('a','b','c','ring_'+label+'_'+role)}) -> ({_valid(code,'ring_'+label+'_'+role+'_domain')})",
                ('gaussian_representation_is_gaussian',),
                _intro('a','b','c','h')+_cases('h',8)+_parts('h'+'_witness'*8,3)+_call('gaussian_representation_is_gaussian',code,*coordinates)+(f"exact {_part('h'+'_witness'*8,3,index)}",),
                "Actual Gaussian "+label+" certifies the "+role.replace('_',' ')+" carrier, without treating every natural code as valid.",
            ))
    return tuple(rows)


def _identity_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    real_code=ge._pair('2*k','0')
    rows=[
        spec(
            "gaussian_natural_real_representation",
            f"forall k. ({_rep(real_code,'k','0','0','0','ring_natural_real')})",
            ('zero_add',),
            _intro('k')+_exists('2*k','0')+('split','refl','split')+_exists('k','0')+('split','left','split','refl','refl','simp [zero_add]')
            +_exists('0','0')+('split','left','split','simp','refl','simp'),
            "Embed a natural real coordinate using its actual even signed code and the unchanged Gaussian pair encoding.",
        ),
    ]
    for name,n,code in (('zero','0','0'),('one','1','6')):
        pair=ge._pair('2*'+n,'0')
        rows.append(spec(
            f'gaussian_{name}_representation', _rep(code,n,'0','0','0','ring_'+name+'_representation'),
            ('gaussian_code_representation_transport','gaussian_natural_real_representation'),
            _call('gaussian_code_representation_transport',pair,code,n,'0','0','0')+('norm_num',)+_call('gaussian_natural_real_representation',n),
            'The actual canonical Gaussian '+name+' code is '+code+', with its signed coordinates proved rather than asserted.',
        ))
        rows.append(spec(
            f'gaussian_{name}_valid',_valid(code,'ring_'+name+'_valid'),
            (f'gaussian_{name}_representation','gaussian_representation_is_gaussian'),
            _call('gaussian_representation_is_gaussian',code,n,'0','0','0')+(f'exact gaussian_{name}_representation',),
            'The canonical Gaussian '+name+' belongs to the actual signed-pair carrier.',
        ))
        rows.append(spec(
            f'gaussian_{name}_norm',_norm(code,n,'ring_'+name+'_norm'),
            (f'gaussian_{name}_representation','gaussian_norm_of_representation'),
            _call('gaussian_norm_of_representation',code,n,'0','0','0',n)+(f'exact gaussian_{name}_representation',)+_exists(n,'0')+('split','norm_num','split','norm_num','norm_num'),
            'The actual squared Gaussian norm of '+name+' is '+n+'.',
        ))
    return tuple(rows)


def _commutative_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B=('ap','an','bp','bn'),('cp','cn','dp','dn')
    X,Y=('x','x1','x2','x3'),('x4','x5','x6','x7')
    rows=[]
    for label,graph,operation,dependencies in (
        ('add',_add,ge._complex_add,('add_comm',)),
        ('multiply',_mul,ge._complex_product,('mul_comm','add_comm')),
    ):
        raw_name='gaussian_ring_raw_'+label+'_commutative'
        simp='simp ['+', '.join(dependencies)+']'
        rows.append(spec(
            raw_name,f"forall {' '.join((*A,*B))}. ({ge._complex_equal(operation(A,B),operation(B,A))})",
            dependencies,_intro(*A,*B)+('split',simp,simp),
            'Actual signed-coordinate Gaussian '+label+' is commutative by ordinary natural identities.',
        ))
        rows.append(spec(
            'gaussian_'+label+'_commutative',f"forall a b c. ({graph('a','b','c','commutative_given_'+label)}) -> ({graph('b','a','c','commutative_result_'+label)})",
            (raw_name,'gaussian_'+label+'_of_representations','gaussian_representation_integer_transport'),
            _intro('a','b','c','h')+_cases('h',8)+_parts('h'+'_witness'*8,3)
            +_call('gaussian_'+label+'_of_representations','b','a','c',*Y,*X)+(f"exact {_part('h'+'_witness'*8,3,1)}",f"exact {_part('h'+'_witness'*8,3,0)}")
            +_call('gaussian_representation_integer_transport','c',*operation(X,Y),*operation(Y,X))+_call(raw_name,*X,*Y)+(f"exact {_part('h'+'_witness'*8,3,2)}",),
            'The actual canonical Gaussian '+label+' graph is commutative; output code equality is not assumed.',
        ))
    return tuple(rows)


def _norm_unit_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    X=('x','x1','x2','x3')
    conjugate=ge._conjugate(X)
    conjugate_product=ge._complex_product(conjugate,X)
    return (
        spec(
            'gaussian_norm_value_transport',f"forall z N M. N=M -> ({_norm('z','N','norm_old_value')}) -> ({_norm('z','M','norm_new_value')})",
            (),_intro('z','N','M','heq','h')+('rewrite heq at h','exact h'),
            'Equality transports the uniquely defined actual Gaussian norm value.',
        ),
        spec(
            'gaussian_norm_nonzero',f"forall z N. ({_norm('z','N','norm_positive')}) -> ~(z=0) -> ~(N=0)",
            ('gaussian_representation_zero_iff','gaussian_signed_norm_nonzero'),
            _intro('z','N','hnorm','hz','hN')+_cases('hnorm',4)+('cases hnorm_witness_witness_witness_witness',)
            +('have hzero : (z=0 -> (x=x1 /\\ x2=x3)) /\\ ((x=x1 /\\ x2=x3) -> z=0)',)
            +_call('gaussian_representation_zero_iff','z',*X)+('exact hnorm_witness_witness_witness_witness_left','cases hzero')
            +_call('gaussian_signed_norm_nonzero',*X,'N')+('exact hnorm_witness_witness_witness_witness_right','intro hvanish','apply hz','apply hzero_right','exact hvanish','exact hN'),
            'A nonzero actual Gaussian integer has nonzero squared norm.',
        ),
        spec(
            'gaussian_norm_zero_implies_code_zero',f"forall z. ({_norm('z','0','norm_zero_given')}) -> z=0",
            ('eq_decidable','gaussian_norm_nonzero'),
            _intro('z','h')+('have hz : z=0 \\/ ~(z=0)',)+_call('eq_decidable','z','0')+('cases hz','exact hz_left','exfalso')
            +_call('gaussian_norm_nonzero','z','0')+('exact h','exact hz_right','refl'),
            'Zero actual Gaussian norm forces literal zero canonical code, by constructive equality decision.',
        ),
        spec(
            'gaussian_code_zero_implies_norm_zero',f"forall z N. ({_norm('z','N','code_zero_norm')}) -> z=0 -> N=0",
            ('gaussian_norm_functional','gaussian_zero_norm'),
            _intro('z','N','h','hz')+('rewrite hz at h',)+_call('gaussian_norm_functional','0','N','0')+('exact h','exact gaussian_zero_norm'),
            'The actual norm of the zero canonical code is zero, not a positive auxiliary value.',
        ),
        spec(
            'gaussian_unit_has_norm_one',f"forall z. ({_unit('z','unit_norm_given')}) -> ({_norm('z','1','unit_norm_value')})",
            ('gaussian_norm_exists','gaussian_multiply_input_left_valid','gaussian_multiply_input_right_valid','gaussian_norm_multiply','gaussian_norm_functional','gaussian_one_norm','divisor_one','gaussian_norm_value_transport'),
            _intro('z','hu')+('cases hu',f"have hN : exists N. ({_norm('z','N','unit_first_norm')})")
            +_call('gaussian_norm_exists','z')+_call('gaussian_multiply_input_left_valid','z','x','6')+('exact hu_witness','cases hN',f"have hM : exists M. ({_norm('x','M','unit_inverse_norm')})")
            +_call('gaussian_norm_exists','x')+_call('gaussian_multiply_input_right_valid','z','x','6')+('exact hu_witness','cases hM','have hproduct : x1*x2=1')
            +_call('gaussian_norm_functional','6','x1*x2','1')+_call('gaussian_norm_multiply','z','x','6','x1','x2')+('exact hN_witness','exact hM_witness','exact hu_witness','exact gaussian_one_norm','have hone : x1=1')
            +_call('divisor_one','x1')+_exists('x2')+('symm','exact hproduct')+_call('gaussian_norm_value_transport','z','x1','1')+('exact hone','exact hN_witness'),
            'An actual inverse multiplies norms to one, forcing the unit norm to equal one.',
        ),
        spec(
            'gaussian_norm_one_is_unit',f"forall z. ({_norm('z','1','norm_unit_given')}) -> ({_unit('z','norm_unit_result')})",
            ('gaussian_representation_exists','gaussian_conjugate_product_is_norm','gaussian_representation_integer_transport','gaussian_equal_symmetric','gaussian_one_representation','gaussian_multiply_of_representations','gaussian_multiply_commutative'),
            _intro('z','h')+_cases('h',4)+('cases h_witness_witness_witness_witness',f"have hinverse : exists u. ({_rep('u',*conjugate,'norm_unit_inverse')})")
            +_call('gaussian_representation_exists',*conjugate)+('cases hinverse',f"have hone : ({_rep('6',*conjugate_product,'norm_unit_product')})")
            +_call('gaussian_representation_integer_transport','6','1','0','0','0',*conjugate_product)
            +_call('gaussian_equal_symmetric',*conjugate_product,'1','0','0','0')+_call('gaussian_conjugate_product_is_norm',*X,'1')
            +('exact h_witness_witness_witness_witness_right','exact gaussian_one_representation')+_exists('x4')
            +_call('gaussian_multiply_commutative','x4','z','6')+_call('gaussian_multiply_of_representations','x4','z','6',*conjugate,*X)
            +('exact hinverse_witness','exact h_witness_witness_witness_witness_left','exact hone'),
            'Norm one constructs an actual inverse: the canonical conjugate multiplies the value to Gaussian identity code six.',
        ),
        spec(
            'gaussian_unit_iff_norm_one',f"forall z N. ({_norm('z','N','unit_iff_norm')}) -> ((({_unit('z','unit_iff_forward')}) -> N=1) /\\ (N=1 -> ({_unit('z','unit_iff_backward')})))",
            ('gaussian_unit_has_norm_one','gaussian_norm_one_is_unit','gaussian_norm_functional','gaussian_norm_value_transport'),
            _intro('z','N','hnorm')+('split','intro hu')+_call('gaussian_norm_functional','z','N','1')+('exact hnorm',)+_call('gaussian_unit_has_norm_one','z')+('exact hu','intro heq')
            +_call('gaussian_norm_one_is_unit','z')+_call('gaussian_norm_value_transport','z','N','1')+('exact heq','exact hnorm'),
            'The inverse-witness definition of Gaussian unit is equivalent to the independently defined squared norm being one.',
        ),
        spec(
            'gaussian_unit_decidable',f"forall z. ({_valid('z','unit_decidable_domain')}) -> ({_unit('z','unit_decidable_yes')}) \\/ ~({_unit('z','unit_decidable_no')})",
            ('gaussian_norm_exists','eq_decidable','gaussian_norm_one_is_unit','gaussian_norm_value_transport','gaussian_unit_has_norm_one','gaussian_norm_functional'),
            _intro('z','hv')+(f"have hn : exists N. ({_norm('z','N','unit_decidable_value')})",)+_call('gaussian_norm_exists','z')+('exact hv','cases hn','have hcases : x=1 \\/ ~(x=1)')
            +_call('eq_decidable','x','1')+('cases hcases','left')+_call('gaussian_norm_one_is_unit','z')+_call('gaussian_norm_value_transport','z','x','1')+('exact hcases_left','exact hn_witness','right','intro hu','apply hcases_right')
            +_call('gaussian_norm_functional','z','x','1')+('exact hn_witness',)+_call('gaussian_unit_has_norm_one','z')+('exact hu',),
            'Actual Gaussian units are constructively decidable by computing the actual norm and deciding equality with one.',
        ),
        spec(
            'gaussian_unit_nonzero',f"forall z. ({_unit('z','unit_nonzero')}) -> ~(z=0)",
            ('gaussian_unit_has_norm_one','gaussian_code_zero_implies_norm_zero'),
            _intro('z','hu','hz')+('have hbad : 1=0',)+_call('gaussian_code_zero_implies_norm_zero','z','1')+_call('gaussian_unit_has_norm_one','z')+('exact hu','exact hz','apply PA1','exact hbad'),
            'A Gaussian multiplicative unit cannot have zero canonical code.',
        ),
        spec(
            'gaussian_unit_valid',f"forall z. ({_unit('z','unit_valid')}) -> ({_valid('z','unit_valid_carrier')})",
            ('gaussian_multiply_input_left_valid',),_intro('z','hu')+('cases hu',)+_call('gaussian_multiply_input_left_valid','z','x','6')+('exact hu_witness',),
            'The inverse-witness unit definition enforces the actual Gaussian carrier.',
        ),
        spec(
            'gaussian_multiply_zero_implies_zero_factor',f"forall a b. ({_mul('a','b','0','zero_product')}) -> a=0 \\/ b=0",
            ('gaussian_norm_exists','gaussian_multiply_input_left_valid','gaussian_multiply_input_right_valid','gaussian_norm_functional','gaussian_norm_multiply','gaussian_zero_norm','mul_eq_zero','gaussian_norm_zero_implies_code_zero','gaussian_norm_value_transport'),
            _intro('a','b','h')+(f"have hA : exists N. ({_norm('a','N','zero_product_first')})",)+_call('gaussian_norm_exists','a')+_call('gaussian_multiply_input_left_valid','a','b','0')+('exact h','cases hA',f"have hB : exists M. ({_norm('b','M','zero_product_second')})")
            +_call('gaussian_norm_exists','b')+_call('gaussian_multiply_input_right_valid','a','b','0')+('exact h','cases hB','have hp : x*x1=0')
            +_call('gaussian_norm_functional','0','x*x1','0')+_call('gaussian_norm_multiply','a','b','0','x','x1')+('exact hA_witness','exact hB_witness','exact h','exact gaussian_zero_norm','have hcases : x=0 \\/ x1=0')
            +_call('mul_eq_zero','x','x1')+('exact hp','cases hcases','left')+_call('gaussian_norm_zero_implies_code_zero','a')+_call('gaussian_norm_value_transport','a','x','0')+('exact hcases_left','exact hA_witness','right')
            +_call('gaussian_norm_zero_implies_code_zero','b')+_call('gaussian_norm_value_transport','b','x1','0')+('exact hcases_right','exact hB_witness'),
            'The actual Gaussian ring has no zero divisors, proved from multiplicative norms and natural multiplication.',
        ),
    )


_AC=('add_assoc','add_comm','four_square_add_swap_right_tail')


def _have_rep(name: str, code: str, valid_proof: tuple[str,...]) -> tuple[str,...]:
    return (f"have {name} : exists rp rn ip inn. ({_rep(code,'rp','rn','ip','inn','chosen_'+name)})",)+_call('gaussian_valid_has_representation',code)+valid_proof+_cases(name,4)


def _law_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B,C=('ap','an','bp','bn'),('cp','cn','dp','dn'),('ep','en','fp','fn')
    X,Y,Z=('x','x1','x2','x3'),('x4','x5','x6','x7'),('x8','x9','x10','x11')
    add=ge._complex_add
    multiply=ge._complex_product
    rows=[
        spec(
            'gaussian_codes_equal_of_representations',f"forall z w {' '.join((*A,*B))}. ({_rep('z',*A,'equal_code_first')}) -> ({_rep('w',*B,'equal_code_second')}) -> ({ge._complex_equal(A,B)}) -> z=w",
            ('gaussian_representation_functional','gaussian_representation_integer_transport','gaussian_equal_symmetric'),
            _intro('z','w',*A,*B,'hz','hw','heq')+_call('gaussian_representation_functional','z','w',*A)+('exact hz',)
            +_call('gaussian_representation_integer_transport','w',*B,*A)+_call('gaussian_equal_symmetric',*A,*B)+('exact heq','exact hw'),
            'Equal represented Gaussian integers have literally equal canonical natural codes.',
        ),
        spec(
            'gaussian_ring_raw_add_associative',f"forall {' '.join((*A,*B,*C))}. ({ge._complex_equal(add(add(A,B),C),add(A,add(B,C)))})",
            ('add_assoc',),_intro(*A,*B,*C)+('split','simp [add_assoc]','simp [add_assoc]'),
            'Actual signed-coordinate Gaussian sums associate by proved natural addition identities.',
        ),
        spec(
            'gaussian_ring_pair_sum_cancel',"forall a b c d e f. (a+c)+(b+f)=(a+e)+(b+d) -> c+f=e+d",
            ('add_left_cancel',*_AC),
            _intro('a','b','c','d','e','f','h')+_call('add_left_cancel','a+b','c+f','e+d')+('trans (a+c)+(b+f)','simp ['+', '.join(_AC)+']','trans (a+e)+(b+d)','exact h','simp ['+', '.join(_AC)+']'),
            'Cancel a common represented integer summand using ordinary natural addition cancellation.',
        ),
        spec(
            'gaussian_ring_raw_add_cancel_left',f"forall {' '.join((*A,*B,*C))}. ({ge._complex_equal(add(A,B),add(A,C))}) -> ({ge._complex_equal(B,C)})",
            ('gaussian_ring_pair_sum_cancel',),
            _intro(*A,*B,*C,'h')+('cases h','split')+_call('gaussian_ring_pair_sum_cancel',*A[:2],*B[:2],*C[:2])+('exact h_left',)
            +_call('gaussian_ring_pair_sum_cancel',*A[2:],*B[2:],*C[2:])+('exact h_right',),
            'A common Gaussian summand cancels in both actual represented integer coordinates.',
        ),
    ]
    for label,graph,operation,raw_associative in (
        ('add',_add,add,'gaussian_ring_raw_add_associative'),
        ('multiply',_mul,multiply,'gaussian_product_associate'),
    ):
        intro_name='gaussian_'+label+'_of_representations'
        eliminate='gaussian_'+label+'_for_representations'
        left_valid='gaussian_'+label+'_input_left_valid'
        right_valid='gaussian_'+label+'_input_right_valid'
        proof=_intro('a','b','c','ab','bc','t','hAB','hABC','hBC')
        proof+=_have_rep('hA','a',_call(left_valid,'a','b','ab')+('exact hAB',))
        proof+=_have_rep('hB','b',_call(right_valid,'a','b','ab')+('exact hAB',))
        proof+=_have_rep('hC','c',_call(right_valid,'ab','c','t')+('exact hABC',))
        proof+=(f"have hab : {_rep('ab',*operation(X,Y),'associate_ab_'+label)}",)+_call(eliminate,'a','b','ab',*X,*Y)+('exact hA_witness_witness_witness_witness','exact hB_witness_witness_witness_witness','exact hAB')
        proof+=(f"have hbc : {_rep('bc',*operation(Y,Z),'associate_bc_'+label)}",)+_call(eliminate,'b','c','bc',*Y,*Z)+('exact hB_witness_witness_witness_witness','exact hC_witness_witness_witness_witness','exact hBC')
        proof+=(f"have ht : {_rep('t',*operation(operation(X,Y),Z),'associate_t_'+label)}",)+_call(eliminate,'ab','c','t',*operation(X,Y),*Z)+('exact hab','exact hC_witness_witness_witness_witness','exact hABC')
        proof+=_call(intro_name,'a','bc','t',*X,*operation(Y,Z))+('exact hA_witness_witness_witness_witness','exact hbc')
        proof+=_call('gaussian_representation_integer_transport','t',*operation(operation(X,Y),Z),*operation(X,operation(Y,Z)))+_call(raw_associative,*X,*Y,*Z)+('exact ht',)
        rows.append(spec(
            'gaussian_'+label+'_associative',f"forall a b c ab bc t. ({graph('a','b','ab','associate_first_'+label)}) -> ({graph('ab','c','t','associate_second_'+label)}) -> "
            f"({graph('b','c','bc','associate_third_'+label)}) -> ({graph('a','bc','t','associate_output_'+label)})",
            ('gaussian_valid_has_representation',left_valid,right_valid,eliminate,intro_name,'gaussian_representation_integer_transport',raw_associative),proof,
            'The actual canonical Gaussian '+label+' graph associates, with all intermediate product/sum codes witnessed.',
        ))
    for label,graph,operation,identity,identity_coordinates,output,output_coordinates,representation,extra in (
        ('add_zero',_add,add,'0',('0','0','0','0'),'a',X,'gaussian_zero_representation',()),
        ('multiply_one',_mul,multiply,'6',('1','0','0','0'),'a',X,'gaussian_one_representation',('zero_add',)),
        ('multiply_zero',_mul,multiply,'0',('0','0','0','0'),'0',('0','0','0','0'),'gaussian_zero_representation',()),
    ):
        op_label='add' if label.startswith('add') else 'multiply'
        proof=_intro('a','hv')+_have_rep('hA','a',('exact hv',))
        proof+=_call('gaussian_'+op_label+'_of_representations','a',identity,output,*X,*identity_coordinates)+('exact hA_witness_witness_witness_witness',f'exact {representation}')
        proof+=_call('gaussian_representation_integer_transport',output,*output_coordinates,*operation(X,identity_coordinates))+('split',)
        simp='simp'+(' ['+', '.join(extra)+']' if extra else '')
        proof+=(simp,simp)+(('exact hA_witness_witness_witness_witness',) if output=='a' else ('exact gaussian_zero_representation',))
        right_name='gaussian_'+label+'_right'
        rows.append(spec(right_name,f"forall a. ({_valid('a',label+'_domain')}) -> ({graph('a',identity,output,label+'_right')})",
                         ('gaussian_valid_has_representation','gaussian_'+op_label+'_of_representations','gaussian_representation_integer_transport',representation,*extra),proof,
                         'The actual canonical Gaussian '+label.replace('_',' ')+' identity holds on the entire valid carrier.'))
        rows.append(spec('gaussian_'+label+'_left',f"forall a. ({_valid('a',label+'_left_domain')}) -> ({graph(identity,'a',output,label+'_left')})",
                         (right_name,'gaussian_'+op_label+'_commutative'),_intro('a','hv')+_call('gaussian_'+op_label+'_commutative','a',identity,output)+_call(right_name,'a')+('exact hv',),
                         'Commutativity supplies the actual left '+label.replace('_',' ')+' identity.'))
    difference=ge._complex_difference(X,Y)
    rows.append(spec(
        'gaussian_subtract_exists',f"forall a b. ({_valid('a','subtract_first')}) -> ({_valid('b','subtract_second')}) -> exists c. ({_add('c','b','a','subtract_equation')})",
        ('gaussian_valid_has_representation','gaussian_representation_exists','gaussian_add_commutative','gaussian_add_of_representations','gaussian_representation_integer_transport','gaussian_equal_symmetric','gaussian_difference_reconstructs_dividend'),
        _intro('a','b','ha','hb')+_have_rep('hA','a',('exact ha',))+_have_rep('hB','b',('exact hb',))
        +(f"have hC : exists c. ({_rep('c',*difference,'subtract_constructed')})",)+_call('gaussian_representation_exists',*difference)+('cases hC',)+_exists('x8')
        +_call('gaussian_add_commutative','b','x8','a')+_call('gaussian_add_of_representations','b','x8','a',*Y,*difference)
        +('exact hB_witness_witness_witness_witness','exact hC_witness')+_call('gaussian_representation_integer_transport','a',*X,*add(Y,difference))
        +_call('gaussian_equal_symmetric',*add(Y,difference),*X)+_call('gaussian_difference_reconstructs_dividend',*X,*Y)+('exact hA_witness_witness_witness_witness',),
        'Every actual Gaussian difference has a constructed canonical code solving c+b=a, without assuming a subtraction oracle.',
    ))
    cancellation=_intro('a','b','c','t','hAB','hAC')
    cancellation+=_have_rep('hA','a',_call('gaussian_add_input_left_valid','a','b','t')+('exact hAB',))
    cancellation+=_have_rep('hB','b',_call('gaussian_add_input_right_valid','a','b','t')+('exact hAB',))
    cancellation+=_have_rep('hC','c',_call('gaussian_add_input_right_valid','a','c','t')+('exact hAC',))
    cancellation+=(f"have hleft : {_rep('t',*add(X,Y),'cancel_sum_left')}",)+_call('gaussian_add_for_representations','a','b','t',*X,*Y)+('exact hA_witness_witness_witness_witness','exact hB_witness_witness_witness_witness','exact hAB')
    cancellation+=(f"have hright : {_rep('t',*add(X,Z),'cancel_sum_right')}",)+_call('gaussian_add_for_representations','a','c','t',*X,*Z)+('exact hA_witness_witness_witness_witness','exact hC_witness_witness_witness_witness','exact hAC')
    cancellation+=_call('gaussian_codes_equal_of_representations','b','c',*Y,*Z)+('exact hB_witness_witness_witness_witness','exact hC_witness_witness_witness_witness')
    cancellation+=_call('gaussian_ring_raw_add_cancel_left',*X,*Y,*Z)+_call('gaussian_representation_equal','t',*add(X,Y),*add(X,Z))+('exact hleft','exact hright')
    rows.append(spec('gaussian_add_cancel_left',f"forall a b c t. ({_add('a','b','t','cancel_first')}) -> ({_add('a','c','t','cancel_second')}) -> b=c",
                     ('gaussian_valid_has_representation','gaussian_add_input_left_valid','gaussian_add_input_right_valid','gaussian_add_for_representations','gaussian_codes_equal_of_representations','gaussian_ring_raw_add_cancel_left','gaussian_representation_equal'),cancellation,
                     'The actual canonical Gaussian additive operation is cancellative, proved in both signed coordinates.'))
    return tuple(rows)


def _distribution_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    A,B,C=('ap','an','bp','bn'),('cp','cn','dp','dn'),('ep','en','fp','fn')
    X,Y,Z=('x','x1','x2','x3'),('x4','x5','x6','x7'),('x8','x9','x10','x11')
    add,multiply=ge._complex_add,ge._complex_product
    rows=[]
    for label,graph in (('add',_add),('multiply',_mul)):
        rows.append(spec(
            'gaussian_'+label+'_output_transport',f"forall a b c d. c=d -> ({graph('a','b','c','output_old_'+label)}) -> ({graph('a','b','d','output_new_'+label)})",
            (),_intro('a','b','c','d','heq','h')+('rewrite heq at h','exact h'),
            'A proved equal output code preserves the actual Gaussian '+label+' graph.',
        ))
    rows.append(spec(
        'gaussian_multiply_associative_reverse',f"forall a b c ab bc t. ({_mul('a','b','ab','reverse_assoc_first')}) -> ({_mul('b','c','bc','reverse_assoc_second')}) -> ({_mul('a','bc','t','reverse_assoc_third')}) -> ({_mul('ab','c','t','reverse_assoc_result')})",
        ('gaussian_multiply_exists','gaussian_multiply_output_valid','gaussian_multiply_input_right_valid','gaussian_multiply_associative','gaussian_multiply_functional','gaussian_multiply_output_transport'),
        _intro('a','b','c','ab','bc','t','hAB','hBC','hT')+(f"have hproduct : exists u. ({_mul('ab','c','u','reverse_assoc_construct')})",)
        +_call('gaussian_multiply_exists','ab','c')+_call('gaussian_multiply_output_valid','a','b','ab')+('exact hAB',)+_call('gaussian_multiply_input_right_valid','b','c','bc')+('exact hBC','cases hproduct','have heq : x=t')
        +_call('gaussian_multiply_functional','a','bc','x','t')+_call('gaussian_multiply_associative','a','b','c','ab','bc','x')+('exact hAB','exact hproduct_witness','exact hBC','exact hT')
        +_call('gaussian_multiply_output_transport','ab','c','x','t')+('exact heq','exact hproduct_witness'),
        'Actual Gaussian products can be reassociated in the reverse direction without assuming the unknown intermediate result.',
    ))
    rows.append(spec(
        'gaussian_multiply_swap_tail',f"forall a b c ab ac t. ({_mul('a','b','ab','swap_first')}) -> ({_mul('ab','c','t','swap_second')}) -> ({_mul('a','c','ac','swap_third')}) -> ({_mul('ac','b','t','swap_result')})",
        ('gaussian_multiply_exists','gaussian_multiply_input_right_valid','gaussian_multiply_associative','gaussian_multiply_associative_reverse','gaussian_multiply_commutative'),
        _intro('a','b','c','ab','ac','t','hAB','hABC','hAC')+(f"have hBC : exists u. ({_mul('b','c','u','swap_bc')})",)
        +_call('gaussian_multiply_exists','b','c')+_call('gaussian_multiply_input_right_valid','a','b','ab')+('exact hAB',)+_call('gaussian_multiply_input_right_valid','ab','c','t')+('exact hABC','cases hBC')
        +(f"have hT : {_mul('a','x','t','swap_matched')}",)+_call('gaussian_multiply_associative','a','b','c','ab','x','t')+('exact hAB','exact hABC','exact hBC_witness')
        +_call('gaussian_multiply_associative_reverse','a','c','b','ac','x','t')+('exact hAC',)+_call('gaussian_multiply_commutative','b','c','x')+('exact hBC_witness','exact hT'),
        'Interchange the two tail factors of an actual Gaussian triple product while retaining its literal output code.',
    ))
    distributed_left,distributed_right=multiply(A,add(B,C)),add(multiply(A,B),multiply(A,C))
    component_names=[]
    for index,label in enumerate(('real_positive','real_negative','imaginary_positive','imaginary_negative')):
        name='gaussian_ring_multiply_add_'+label
        component_names.append(name)
        guide=tuple(command.replace('simp [add_mul, mul_add, mul_assoc, add_assoc]','simp [mul_add, add_assoc]') for command in ge._ordered_expansion_identity(distributed_left[index],distributed_right[index]))
        rows.append(spec(name,f"forall {' '.join((*A,*B,*C))}. {distributed_left[index]}={distributed_right[index]}",
                         ('mul_add',*_AC),_intro(*A,*B,*C)+guide,
                         'Guided ordinary-HA distributivity for the actual Gaussian '+label.replace('_',' ')+' component; no AC search or new tactic.'))
    rows.append(spec(
        'gaussian_ring_raw_multiply_add_distributive',f"forall {' '.join((*A,*B,*C))}. ({ge._complex_equal(multiply(A,add(B,C)),add(multiply(A,B),multiply(A,C)))})",
        tuple(component_names),_intro(*A,*B,*C)+('split','congr','apply '+component_names[0],'symm','apply '+component_names[1],'congr','apply '+component_names[2],'symm','apply '+component_names[3]),
        'Actual Gaussian multiplication distributes over addition in both signed integer coordinates.',
    ))
    proof=_intro('a','b','c','s','p','q','t','hBC','hAB','hAC','hPQ')
    proof+=_have_rep('hA','a',_call('gaussian_multiply_input_left_valid','a','b','p')+('exact hAB',))
    proof+=_have_rep('hB','b',_call('gaussian_multiply_input_right_valid','a','b','p')+('exact hAB',))
    proof+=_have_rep('hC','c',_call('gaussian_multiply_input_right_valid','a','c','q')+('exact hAC',))
    proof+=(f"have hp : {_rep('p',*multiply(X,Y),'distribute_p')}",)+_call('gaussian_multiply_for_representations','a','b','p',*X,*Y)+('exact hA_witness_witness_witness_witness','exact hB_witness_witness_witness_witness','exact hAB')
    proof+=(f"have hq : {_rep('q',*multiply(X,Z),'distribute_q')}",)+_call('gaussian_multiply_for_representations','a','c','q',*X,*Z)+('exact hA_witness_witness_witness_witness','exact hC_witness_witness_witness_witness','exact hAC')
    proof+=(f"have hs : {_rep('s',*add(Y,Z),'distribute_s')}",)+_call('gaussian_add_for_representations','b','c','s',*Y,*Z)+('exact hB_witness_witness_witness_witness','exact hC_witness_witness_witness_witness','exact hBC')
    proof+=(f"have ht : {_rep('t',*add(multiply(X,Y),multiply(X,Z)),'distribute_t')}",)+_call('gaussian_add_for_representations','p','q','t',*multiply(X,Y),*multiply(X,Z))+('exact hp','exact hq','exact hPQ')
    proof+=_call('gaussian_multiply_of_representations','a','s','t',*X,*add(Y,Z))+('exact hA_witness_witness_witness_witness','exact hs')
    proof+=_call('gaussian_representation_integer_transport','t',*add(multiply(X,Y),multiply(X,Z)),*multiply(X,add(Y,Z)))
    proof+=_call('gaussian_equal_symmetric',*multiply(X,add(Y,Z)),*add(multiply(X,Y),multiply(X,Z)))+_call('gaussian_ring_raw_multiply_add_distributive',*X,*Y,*Z)+('exact ht',)
    rows.append(spec(
        'gaussian_multiply_add_compose',f"forall a b c s p q t. ({_add('b','c','s','distribute_sum')}) -> ({_mul('a','b','p','distribute_first')}) -> ({_mul('a','c','q','distribute_second')}) -> ({_add('p','q','t','distribute_total')}) -> ({_mul('a','s','t','distribute_product')})",
        ('gaussian_valid_has_representation','gaussian_multiply_input_left_valid','gaussian_multiply_input_right_valid','gaussian_multiply_for_representations','gaussian_add_for_representations','gaussian_multiply_of_representations','gaussian_representation_integer_transport','gaussian_equal_symmetric','gaussian_ring_raw_multiply_add_distributive'),proof,
        'The sum of two actual Gaussian products is the product with their actual summed second factors.',
    ))
    rows.append(spec(
        'gaussian_multiply_add_distribute',f"forall a b c s p q t. ({_add('b','c','s','expand_sum')}) -> ({_mul('a','b','p','expand_first')}) -> ({_mul('a','c','q','expand_second')}) -> ({_mul('a','s','t','expand_product')}) -> ({_add('p','q','t','expand_result')})",
        ('gaussian_add_exists','gaussian_multiply_output_valid','gaussian_multiply_add_compose','gaussian_multiply_functional','gaussian_add_output_transport'),
        _intro('a','b','c','s','p','q','t','hBC','hAB','hAC','hAS')+(f"have htotal : exists u. ({_add('p','q','u','expand_actual_sum')})",)
        +_call('gaussian_add_exists','p','q')+_call('gaussian_multiply_output_valid','a','b','p')+('exact hAB',)+_call('gaussian_multiply_output_valid','a','c','q')+('exact hAC','cases htotal','have heq : x=t')
        +_call('gaussian_multiply_functional','a','s','x','t')+_call('gaussian_multiply_add_compose','a','b','c','s','p','q','x')+('exact hBC','exact hAB','exact hAC','exact htotal_witness','exact hAS')
        +_call('gaussian_add_output_transport','p','q','x','t')+('exact heq','exact htotal_witness'),
        'An actual Gaussian product of a sum equals the actual sum of the two given products.',
    ))
    rows.append(spec(
        'gaussian_multiply_add_distribute_right',f"forall a b c s p q t. ({_add('b','c','s','expand_right_sum')}) -> ({_mul('b','a','p','expand_right_first')}) -> ({_mul('c','a','q','expand_right_second')}) -> ({_mul('s','a','t','expand_right_product')}) -> ({_add('p','q','t','expand_right_result')})",
        ('gaussian_multiply_add_distribute','gaussian_multiply_commutative'),
        _intro('a','b','c','s','p','q','t','hBC','hBA','hCA','hSA')+_call('gaussian_multiply_add_distribute','a','b','c','s','p','q','t')+('exact hBC',)
        +_call('gaussian_multiply_commutative','b','a','p')+('exact hBA',)+_call('gaussian_multiply_commutative','c','a','q')+('exact hCA',)+_call('gaussian_multiply_commutative','s','a','t')+('exact hSA',),
        'Actual Gaussian multiplication also distributes when the common factor is on the right.',
    ))
    rows.append(spec(
        'gaussian_add_cancel_right',f"forall a b c t. ({_add('a','c','t','cancel_right_first')}) -> ({_add('b','c','t','cancel_right_second')}) -> a=b",
        ('gaussian_add_cancel_left','gaussian_add_commutative'),
        _intro('a','b','c','t','hA','hB')+_call('gaussian_add_cancel_left','c','a','b','t')+_call('gaussian_add_commutative','a','c','t')+('exact hA',)+_call('gaussian_add_commutative','b','c','t')+('exact hB',),
        'A common right summand cancels in the actual canonical Gaussian additive graph.',
    ))
    return tuple(rows)


def _unit_cancellation_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_multiply_cancel_left',f"forall a b c t. ~(a=0) -> ({_mul('a','b','t','cancel_product_first')}) -> ({_mul('a','c','t','cancel_product_second')}) -> b=c",
            ('gaussian_subtract_exists','gaussian_multiply_input_left_valid','gaussian_multiply_input_right_valid','gaussian_multiply_output_valid','gaussian_add_input_left_valid','gaussian_multiply_exists',
             'gaussian_multiply_add_distribute','gaussian_add_zero_left','gaussian_add_cancel_right','gaussian_multiply_output_transport','gaussian_multiply_zero_implies_zero_factor','gaussian_add_functional'),
            _intro('a','b','c','t','hn','hB','hC')+(f"have hd : exists d. ({_add('d','c','b','cancel_product_difference')})",)
            +_call('gaussian_subtract_exists','b','c')+_call('gaussian_multiply_input_right_valid','a','b','t')+('exact hB',)+_call('gaussian_multiply_input_right_valid','a','c','t')+('exact hC','cases hd',f"have hproduct : exists u. ({_mul('a','x','u','cancel_product_construct')})")
            +_call('gaussian_multiply_exists','a','x')+_call('gaussian_multiply_input_left_valid','a','b','t')+('exact hB',)+_call('gaussian_add_input_left_valid','x','c','b')+('exact hd_witness','cases hproduct')
            +(f"have hsum : {_add('x1','t','t','cancel_product_sum')}",)+_call('gaussian_multiply_add_distribute','a','x','c','b','x1','t','t')+('exact hd_witness','exact hproduct_witness','exact hC','exact hB','have hzero : x1=0')
            +_call('gaussian_add_cancel_right','x1','0','t','t')+('exact hsum',)+_call('gaussian_add_zero_left','t')+_call('gaussian_multiply_output_valid','a','b','t')+('exact hB','have hcases : a=0 \\/ x=0')
            +_call('gaussian_multiply_zero_implies_zero_factor','a','x')+_call('gaussian_multiply_output_transport','a','x','x1','0')+('exact hzero','exact hproduct_witness','cases hcases','exfalso','apply hn','exact hcases_left','rewrite hcases_right at hd_witness')
            +_call('gaussian_add_functional','0','c','b','c')+('exact hd_witness',)+_call('gaussian_add_zero_left','c')+_call('gaussian_multiply_input_right_valid','a','c','t')+('exact hC',),
            'A nonzero Gaussian factor cancels, using an actually constructed difference, distributivity and the proved absence of zero divisors.',
        ),
        spec(
            'gaussian_multiply_cancel_right',f"forall a b c t. ~(c=0) -> ({_mul('a','c','t','cancel_right_product_first')}) -> ({_mul('b','c','t','cancel_right_product_second')}) -> a=b",
            ('gaussian_multiply_cancel_left','gaussian_multiply_commutative'),
            _intro('a','b','c','t','hc','hA','hB')+_call('gaussian_multiply_cancel_left','c','a','b','t')+('exact hc',)+_call('gaussian_multiply_commutative','a','c','t')+('exact hA',)+_call('gaussian_multiply_commutative','b','c','t')+('exact hB',),
            'A nonzero common right Gaussian factor cancels in the actual canonical multiplication graph.',
        ),
        spec(
            'gaussian_one_unit',_unit('6','one_unit'),
            ('gaussian_multiply_one_right','gaussian_one_valid'),_exists('6')+_call('gaussian_multiply_one_right','6')+('exact gaussian_one_valid',),
            'The actual canonical Gaussian identity code six is a unit with itself as inverse.',
        ),
        spec(
            'gaussian_unit_inverse',f"forall u. ({_unit('u','inverse_given')}) -> exists v. ({_unit('v','inverse_unit')}) /\\ (({_mul('u','v','6','inverse_first')}) /\\ ({_mul('v','u','6','inverse_second')}))",
            ('gaussian_multiply_commutative',),
            _intro('u','h')+('cases h',)+_exists('x')+('split',)+_exists('u')+_call('gaussian_multiply_commutative','u','x','6')+('exact h_witness','split','exact h_witness')+_call('gaussian_multiply_commutative','u','x','6')+('exact h_witness',),
            'Every inverse witness is itself an actual unit and is a two-sided inverse.',
        ),
        spec(
            'gaussian_unit_product',f"forall u v w. ({_mul('u','v','w','unit_product')}) -> ({_unit('u','unit_product_first')}) -> ({_unit('v','unit_product_second')}) -> ({_unit('w','unit_product_result')})",
            ('gaussian_norm_one_is_unit','gaussian_norm_value_transport','gaussian_norm_multiply','gaussian_unit_has_norm_one'),
            _intro('u','v','w','hprod','hu','hv')+_call('gaussian_norm_one_is_unit','w')+_call('gaussian_norm_value_transport','w','1*1','1')+('norm_num',)
            +_call('gaussian_norm_multiply','u','v','w','1','1')+_call('gaussian_unit_has_norm_one','u')+('exact hu',)+_call('gaussian_unit_has_norm_one','v')+('exact hv','exact hprod'),
            'An actual product of Gaussian units is a unit, by norm multiplicativity and the proved inverse construction at norm one.',
        ),
        spec(
            'gaussian_unit_factor_left',f"forall a b c. ({_mul('a','b','c','unit_factor_product')}) -> ({_unit('c','unit_factor_whole')}) -> ({_unit('a','unit_factor_first')})",
            ('gaussian_multiply_exists','gaussian_multiply_input_right_valid','gaussian_multiply_associative'),
            _intro('a','b','c','hprod','hu')+('cases hu',f"have hinverse : exists v. ({_mul('b','x','v','unit_factor_inverse')})")
            +_call('gaussian_multiply_exists','b','x')+_call('gaussian_multiply_input_right_valid','a','b','c')+('exact hprod',)+_call('gaussian_multiply_input_right_valid','c','x','6')+('exact hu_witness','cases hinverse')
            +_exists('x1')+_call('gaussian_multiply_associative','a','b','x','c','x1','6')+('exact hprod','exact hu_witness','exact hinverse_witness'),
            'Every actual left factor of a Gaussian unit has a constructed inverse, without an irreducibility assumption.',
        ),
        spec(
            'gaussian_unit_factor_right',f"forall a b c. ({_mul('a','b','c','unit_factor_right_product')}) -> ({_unit('c','unit_factor_right_whole')}) -> ({_unit('b','unit_factor_second')})",
            ('gaussian_unit_factor_left','gaussian_multiply_commutative'),
            _intro('a','b','c','hprod','hu')+_call('gaussian_unit_factor_left','b','a','c')+_call('gaussian_multiply_commutative','a','b','c')+('exact hprod','exact hu'),
            'Every actual right factor of a Gaussian unit is also a genuine unit.',
        ),
    )


def make_gaussian_ring_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (*_carrier_rows(spec),*_identity_rows(spec),*_commutative_rows(spec),*_norm_unit_rows(spec),*_law_rows(spec),*_distribution_rows(spec),*_unit_cancellation_rows(spec))


__all__=['gaussian_divides_relation','gaussian_unit_relation','gaussian_associate_relation','gaussian_irreducible_relation','gaussian_prime_relation','make_gaussian_ring_candidate_theorems']
