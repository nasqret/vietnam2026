"""Actual Gaussian Euclidean gcd, Bézout coefficients and prime divisors.

Every arithmetic relation expands to the already checked canonical signed-pair
graphs.  The gcd is specified by actual divisibility, and is unique only up to
a witnessed Gaussian unit.  The construction uses ordinary HA induction on
an explicit natural norm bound, not a termination or gcd oracle.
"""

from __future__ import annotations

from typing import Any,Callable

from .gaussian_ring_candidate import _call,_intro,_exists,_cases,_parts,_part,_and,_dvd,_unit,_associate,_irreducible,_prime,_valid,_mul,_add,_norm,_names,_definition
from . import gaussian_euclidean_candidate as ge


_divrem=ge._code_divrem
_euclidean=ge._code_euclidean
_le=ge._le
_lt=ge._lt


def _bezout(g: str, a: str, b: str, u: str, v: str, tag: str) -> str:
    p,q=_names(tag,'first_product','second_product')
    return f"exists {p} {q}. " + _and(_mul(a,u,p,tag+'first'),_mul(b,v,q,tag+'second'),_add(p,q,g,tag+'sum'))


def _gcd(g: str, a: str, b: str, tag: str) -> str:
    d,=_names(tag,'common_divisor')
    return _and(_dvd(g,a,tag+'first'),_dvd(g,b,tag+'second'),
                f"forall {d}. ({_dvd(d,a,tag+'common_first')}) -> ({_dvd(d,b,tag+'common_second')}) -> ({_dvd(d,g,tag+'greatest')})")


def _completion(a: str, b: str, tag: str) -> str:
    g,u,v=_names(tag,'gcd','first_coefficient','second_coefficient')
    return f"exists {g} {u} {v}. " + _and(_gcd(g,a,b,tag+'gcd'),_bezout(g,a,b,u,v,tag+'bezout'))


def gaussian_bezout_relation(gcd: str, first: str, second: str, first_coefficient: str, second_coefficient: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Actual signed Gaussian products and their actual sum equal the gcd code."""
    return _definition(_bezout,(gcd,first,second,first_coefficient,second_coefficient),tag=tag,variables=variables)


def gaussian_gcd_relation(gcd: str, first: str, second: str, *, tag: str, variables: tuple[str,...]) -> str:
    """A common Gaussian divisor divisible by every other actual common divisor."""
    return _definition(_gcd,(gcd,first,second),tag=tag,variables=variables)


def _base_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_gcd_bezout_zero_right',f"forall a. ({_valid('a','gcd_zero_domain')}) -> "
            +_and(_gcd('a','a','0','gcd_zero'),_bezout('a','a','0','6','0','bezout_zero')),
            ('gaussian_divides_reflexive','gaussian_divides_zero','gaussian_multiply_one_right','gaussian_multiply_zero_right','gaussian_zero_valid','gaussian_add_zero_right'),
            _intro('a','ha')+('split','split')+_call('gaussian_divides_reflexive','a')+('exact ha','split')+_call('gaussian_divides_zero','a')+('exact ha',)
            +_intro('d','hd','hzero')+('exact hd',)+_exists('a','0')+('split',)+_call('gaussian_multiply_one_right','a')+('exact ha','split')
            +_call('gaussian_multiply_zero_right','0')+('exact gaussian_zero_valid',)+_call('gaussian_add_zero_right','a')+('exact ha',),
            'The zero-right Gaussian gcd is the first input, with actual Bézout coefficients six and zero, including the all-zero pair.',
        ),
        spec(
            'gaussian_gcd_bezout_zero_case',f"forall a b. ({_valid('a','gcd_zero_case_first')}) -> ({_valid('b','gcd_zero_case_second')}) -> b=0 -> ({_completion('a','b','gcd_zero_case')})",
            ('gaussian_divides_reflexive','gaussian_divides_zero','gaussian_multiply_one_right','gaussian_multiply_zero_right','gaussian_add_zero_right'),
            _intro('a','b','ha','hb','hzero')+_exists('a','6','0')+('split','split')+_call('gaussian_divides_reflexive','a')+('exact ha','split','rewrite hzero')
            +_call('gaussian_divides_zero','a')+('exact ha',)+_intro('d','hda','hdb')+('exact hda',)+_exists('a','0')+('split',)+_call('gaussian_multiply_one_right','a')+('exact ha','split')
            +_call('gaussian_multiply_zero_right','b')+('exact hb',)+_call('gaussian_add_zero_right','a')+('exact ha',),
            'A proved zero second code yields genuine gcd and Bézout witnesses without rewriting or assuming arbitrary carrier validity.',
        ),
        spec(
            'gaussian_common_divisor_of_bezout',f"forall d g a b u v. ({_dvd('d','a','bezout_divisor_first')}) -> ({_dvd('d','b','bezout_divisor_second')}) -> ({_bezout('g','a','b','u','v','bezout_divisor_equation')}) -> ({_dvd('d','g','bezout_divisor_result')})",
            ('gaussian_common_divisor_add','gaussian_divides_product_left'),
            _intro('d','g','a','b','u','v','ha','hb','hbez')+_cases('hbez',2)+_parts('hbez_witness_witness',3)+_call('gaussian_common_divisor_add','d','x','x1','g')
            +_call('gaussian_divides_product_left','d','a','u','x')+('exact ha',f"exact {_part('hbez_witness_witness',3,0)}")
            +_call('gaussian_divides_product_left','d','b','v','x1')+('exact hb',f"exact {_part('hbez_witness_witness',3,1)}",f"exact {_part('hbez_witness_witness',3,2)}"),
            'Every actual common Gaussian divisor divides an actual Bézout combination.',
        ),
        spec(
            'gaussian_gcd_euclidean_backward',f"forall g a b q r. ({_divrem('a','b','q','r','gcd_euclidean_equation')}) -> ({_gcd('g','b','r','gcd_remainder')}) -> ({_gcd('g','a','b','gcd_dividend')})",
            ('gaussian_common_divisor_euclidean_forward','gaussian_common_divisor_euclidean_backward'),
            _intro('g','a','b','q','r','heq','hgcd')+_parts('hgcd',3)+('split',)+_call('gaussian_common_divisor_euclidean_forward','g','a','b','q','r')
            +('exact heq',f"exact {_part('hgcd',3,0)}",f"exact {_part('hgcd',3,1)}",'split',f"exact {_part('hgcd',3,0)}")+_intro('d','hda','hdb')
            +_call(_part('hgcd',3,2),'d')+('exact hdb',)+_call('gaussian_common_divisor_euclidean_backward','d','a','b','q','r')+('exact heq','exact hda','exact hdb'),
            'Transport the actual greatest-common-divisor property backwards through a proved Gaussian Euclidean equation.',
        ),
    )


def _bezout_step_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    fields=tuple(_part('hbez_witness_witness',3,i) for i in range(3))
    script=_intro('g','a','b','q','r','u','v','heq','hbez')+('cases heq','cases heq_witness')+_cases('hbez',2)+_parts('hbez_witness_witness',3)
    script+=(f"have hqv : exists w. ({_mul('q','v','w','bezout_qv')})",)+_call('gaussian_multiply_exists','q','v')
    script+=_call('gaussian_multiply_input_right_valid','b','q','x')+('exact heq_witness_left',)+_call('gaussian_multiply_input_right_valid','r','v','x2')+(f'exact {fields[1]}','cases hqv')
    script+=(f"have hw : exists w. ({_add('w','x3','u','bezout_new_coefficient')})",)+_call('gaussian_subtract_exists','u','x3')
    script+=_call('gaussian_multiply_input_right_valid','b','u','x1')+(f'exact {fields[0]}',)+_call('gaussian_multiply_output_valid','q','v','x3')+('exact hqv_witness','cases hw')
    script+=(f"have hPv : exists w. ({_mul('x','v','w','bezout_Pv')})",)+_call('gaussian_multiply_exists','x','v')
    script+=_call('gaussian_multiply_output_valid','b','q','x')+('exact heq_witness_left',)+_call('gaussian_multiply_input_right_valid','r','v','x2')+(f'exact {fields[1]}','cases hPv')
    script+=(f"have hAv : exists w. ({_mul('a','v','w','bezout_Av')})",)+_call('gaussian_multiply_exists','a','v')
    script+=_call('gaussian_add_output_valid','x','r','a')+('exact heq_witness_right',)+_call('gaussian_multiply_input_right_valid','r','v','x2')+(f'exact {fields[1]}','cases hAv')
    script+=(f"have hBw : exists w. ({_mul('b','x4','w','bezout_Bw')})",)+_call('gaussian_multiply_exists','b','x4')
    script+=_call('gaussian_multiply_input_left_valid','b','q','x')+('exact heq_witness_left',)+_call('gaussian_add_input_left_valid','x4','x3','u')+('exact hw_witness','cases hBw')
    script+=(f"have hBqv : {_mul('b','x3','x5','bezout_Bqv')}",)+_call('gaussian_multiply_associative','b','q','v','x','x3','x5')+('exact heq_witness_left','exact hPv_witness','exact hqv_witness')
    script+=(f"have hfirstsum : {_add('x5','x2','x6','bezout_dividend_expansion')}",)+_call('gaussian_multiply_add_distribute_right','v','x','r','a','x5','x2','x6')+('exact heq_witness_right','exact hPv_witness',f'exact {fields[1]}','exact hAv_witness')
    script+=(f"have hsecondsum : {_add('x7','x5','x1','bezout_coefficient_expansion')}",)+_call('gaussian_multiply_add_distribute','b','x4','x3','u','x7','x5','x1')+('exact hw_witness','exact hBw_witness','exact hBqv',f'exact {fields[0]}')
    script+=_exists('x4')+_exists('x6','x7')+('split','exact hAv_witness','split','exact hBw_witness')+_call('gaussian_add_commutative','x7','x6','g')
    script+=_call('gaussian_add_associative','x7','x5','x2','x1','x6','g')+('exact hsecondsum',f'exact {fields[2]}','exact hfirstsum')
    return (spec(
        'gaussian_bezout_euclidean_backward',f"forall g a b q r u v. ({_divrem('a','b','q','r','bezout_euclidean_equation')}) -> ({_bezout('g','b','r','u','v','bezout_remainder')}) -> exists w. ({_bezout('g','a','b','v','w','bezout_dividend')})",
        ('gaussian_multiply_exists','gaussian_multiply_input_right_valid','gaussian_multiply_output_valid','gaussian_subtract_exists','gaussian_add_output_valid','gaussian_multiply_input_left_valid','gaussian_add_input_left_valid','gaussian_multiply_associative','gaussian_multiply_add_distribute_right','gaussian_multiply_add_distribute','gaussian_add_commutative','gaussian_add_associative'),
        script,
        'Construct the coefficient u-qv and verify the complete Gaussian Bézout back-substitution using actual products, differences, distribution and addition.',
    ),)


def _existence_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    fields=tuple(_part('hdivision'+'_witness'*4,6,i) for i in range(6))
    script=_intro('k')+('induction k',)+_intro('a','b','N','ha','hb','hn','hbound')
    script+=_call('gaussian_gcd_bezout_zero_case','a','b')+('exact ha','exact hb')+_call('gaussian_norm_zero_implies_code_zero','b')+_call('gaussian_norm_value_transport','b','N','0')+_call('le_zero','N')+('exact hbound','exact hn')
    script+=_intro('a','b','N','ha','hb','hn','hbound')+('have hzero : b=0 \\/ ~(b=0)',)+_call('eq_decidable','b','0')+('cases hzero',)
    script+=_call('gaussian_gcd_bezout_zero_case','a','b')+('exact ha','exact hb','exact hzero_left')
    script+=(f"have hdivision : exists q r U V. ({_euclidean('a','b','q','r','U','V','gcd_actual_division')})",)+_call('gaussian_euclidean_division_exists','a','b')+('exact ha','exact hb','exact hzero_right')+_cases('hdivision',4)+_parts('hdivision'+'_witness'*4,6)
    script+=('have hnorm : x3=N',)+_call('gaussian_norm_functional','b','x3','N')+(f'exact {fields[4]}','exact hn',f"have hsmall : {_le('x2','k','gcd_smaller_bound')}")
    script+=_call('le_of_succ_le_succ','x2','k')+_call('lt_of_lt_of_le','x2','N','S k')+(f'rewrite hnorm at {fields[5]}',f'exact {fields[5]}','exact hbound')
    script+=(f"have hrecursive : {_completion('b','x1','gcd_recursive')}",)+_call('IH','b','x1','x2')+('exact hb',f'exact {fields[1]}',f'exact {fields[3]}','exact hsmall')+_cases('hrecursive',3)+('cases hrecursive_witness_witness_witness',)
    script+=(f"have hcoeff : exists w. ({_bezout('x4','a','b','x6','w','gcd_lifted_coefficients')})",)+_call('gaussian_bezout_euclidean_backward','x4','a','b','x','x1','x5','x6')+(f'exact {fields[2]}','exact hrecursive_witness_witness_witness_right','cases hcoeff')
    script+=_exists('x4','x6','x7')+('split',)+_call('gaussian_gcd_euclidean_backward','x4','a','b','x','x1')+(f'exact {fields[2]}','exact hrecursive_witness_witness_witness_left','exact hcoeff_witness')
    return (
        spec(
            'gaussian_gcd_bezout_bounded_exists',f"forall k a b N. ({_valid('a','gcd_bounded_first')}) -> ({_valid('b','gcd_bounded_second')}) -> ({_norm('b','N','gcd_bounded_norm')}) -> ({_le('N','k','gcd_bounded_bound')}) -> ({_completion('a','b','gcd_bounded_result')})",
            ('gaussian_gcd_bezout_zero_case','gaussian_norm_zero_implies_code_zero','gaussian_norm_value_transport','le_zero','eq_decidable','gaussian_euclidean_division_exists','gaussian_norm_functional','le_of_succ_le_succ','lt_of_lt_of_le','gaussian_bezout_euclidean_backward','gaussian_gcd_euclidean_backward'),
            script,
            'Ordinary natural induction constructs Gaussian gcd and genuine signed Bézout coefficients for every valid pair; each actual Euclidean remainder strictly decreases the norm bound.',
        ),
        spec(
            'gaussian_gcd_bezout_exists',f"forall a b. ({_valid('a','gcd_exists_first')}) -> ({_valid('b','gcd_exists_second')}) -> ({_completion('a','b','gcd_exists_result')})",
            ('gaussian_norm_exists','gaussian_gcd_bezout_bounded_exists','le_refl'),
            _intro('a','b','ha','hb')+(f"have hn : exists N. ({_norm('b','N','gcd_initial_norm')})",)+_call('gaussian_norm_exists','b')+('exact hb','cases hn')
            +_call('gaussian_gcd_bezout_bounded_exists','x','a','b','x')+('exact ha','exact hb','exact hn_witness')+_call('le_refl','x'),
            'Every pair of actual Gaussian integers has a constructed gcd with actual Gaussian Bézout coefficients, without a supplied norm, trace or positivity premise.',
        ),
        spec(
            'gaussian_gcd_unique_up_to_associate',f"forall g h a b. ({_gcd('g','a','b','gcd_unique_first')}) -> ({_gcd('h','a','b','gcd_unique_second')}) -> ({_associate('g','h','gcd_unique_unit')})",
            ('gaussian_mutual_divisibility_associate',),
            _intro('g','h','a','b','hg','hh')+_parts('hg',3)+_parts('hh',3)+_call('gaussian_mutual_divisibility_associate','g','h')
            +_call(_part('hh',3,2),'g')+(f"exact {_part('hg',3,0)}",f"exact {_part('hg',3,1)}")+_call(_part('hg',3,2),'h')+(f"exact {_part('hh',3,0)}",f"exact {_part('hh',3,1)}"),
            'Actual Gaussian gcd values are unique up to a witnessed unit, not falsely unique as canonical natural codes.',
        ),
    )


def _prime_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    fields=tuple(_part('hbez_witness_witness',3,i) for i in range(3))
    script=_intro('p','a','b','c','g','u','v','hprod','hdiv','hbez','hunit')+_cases('hbez',2)+_parts('hbez_witness_witness',3)
    script+=(f"have hinverse : exists w. {_and(_unit('w','gauss_inverse_unit'),_mul('g','w','6','gauss_inverse_right'),_mul('w','g','6','gauss_inverse_left'))}",)
    script+=_call('gaussian_unit_inverse','g')+('exact hunit','cases hinverse')+_parts('hinverse_witness',3)
    script+=(f"have hP : exists P. ({_mul('x','b','P','gauss_first_scaled')})",)+_call('gaussian_multiply_exists','x','b')
    script+=_call('gaussian_multiply_output_valid','p','u','x')+(f'exact {fields[0]}',)+_call('gaussian_multiply_input_right_valid','a','b','c')+('exact hprod','cases hP')
    script+=(f"have hQ : exists Q. ({_mul('x1','b','Q','gauss_second_scaled')})",)+_call('gaussian_multiply_exists','x1','b')
    script+=_call('gaussian_multiply_output_valid','a','v','x1')+(f'exact {fields[1]}',)+_call('gaussian_multiply_input_right_valid','a','b','c')+('exact hprod','cases hQ')
    script+=(f"have hT : exists T. ({_mul('g','b','T','gauss_total_scaled')})",)+_call('gaussian_multiply_exists','g','b')
    script+=_call('gaussian_unit_valid','g')+('exact hunit',)+_call('gaussian_multiply_input_right_valid','a','b','c')+('exact hprod','cases hT')
    script+=(f"have hcv : {_mul('c','v','x4','gauss_product_reordered')}",)+_call('gaussian_multiply_swap_tail','a','v','b','x1','c','x4')+(f'exact {fields[1]}','exact hQ_witness','exact hprod')
    script+=(f"have htotal : {_dvd('p','x5','gauss_total_divisible')}",)+_call('gaussian_common_divisor_add','p','x3','x4','x5')
    script+=_call('gaussian_divides_product_left','p','x','b','x3')+_exists('u')+(f'exact {fields[0]}','exact hP_witness')
    script+=_call('gaussian_divides_product_left','p','c','v','x4')+('exact hdiv','exact hcv')
    script+=_call('gaussian_multiply_add_distribute_right','b','x','x1','g','x3','x4','x5')+(f'exact {fields[2]}','exact hP_witness','exact hQ_witness','exact hT_witness')
    script+=_call('gaussian_divides_transitive','p','x5','b')+('exact htotal',)+_exists('x2')+_call('gaussian_multiply_commutative','x2','x5','b')
    script+=_call('gaussian_multiply_associative','x2','g','b','6','x5','b')+(f"exact {_part('hinverse_witness',3,2)}",)+_call('gaussian_multiply_one_left','b')
    script+=_call('gaussian_multiply_input_right_valid','a','b','c')+('exact hprod','exact hT_witness')
    rows=[spec(
        'gaussian_bezout_unit_divisor_cancel',f"forall p a b c g u v. ({_mul('a','b','c','gauss_given_product')}) -> ({_dvd('p','c','gauss_given_divisor')}) -> ({_bezout('g','p','a','u','v','gauss_given_bezout')}) -> ({_unit('g','gauss_given_unit')}) -> ({_dvd('p','b','gauss_result')})",
        ('gaussian_unit_inverse','gaussian_multiply_exists','gaussian_multiply_output_valid','gaussian_multiply_input_right_valid','gaussian_unit_valid','gaussian_multiply_swap_tail','gaussian_common_divisor_add','gaussian_divides_product_left','gaussian_multiply_add_distribute_right','gaussian_divides_transitive','gaussian_multiply_commutative','gaussian_multiply_associative','gaussian_multiply_one_left'),
        script,
        'An actual unit-valued Gaussian Bézout combination proves Euclid cancellation for actual divisors, by constructing every multiplied term and the genuine unit inverse.',
    )]
    rows.append(spec(
        'gaussian_nonzero_product_divisor_unit_cofactor',f"forall p a b. ~(p=0) -> ({_mul('a','b','p','cofactor_product')}) -> ({_dvd('p','a','cofactor_reverse_divisor')}) -> ({_unit('b','cofactor_unit')})",
        ('gaussian_multiply_exists','gaussian_multiply_input_right_valid','gaussian_multiply_input_left_valid','gaussian_multiply_associative','gaussian_multiply_cancel_left','gaussian_multiply_one_right','gaussian_multiply_output_transport','gaussian_multiply_commutative'),
        _intro('p','a','b','hn','hprod','hdiv')+('cases hdiv',f"have hq : exists q. ({_mul('x','b','q','cofactor_inverse_product')})")
        +_call('gaussian_multiply_exists','x','b')+_call('gaussian_multiply_input_right_valid','p','x','a')+('exact hdiv_witness',)+_call('gaussian_multiply_input_right_valid','a','b','p')+('exact hprod','cases hq',f"have hself : {_mul('p','x1','p','cofactor_self')}")
        +_call('gaussian_multiply_associative','p','x','b','a','x1','p')+('exact hdiv_witness','exact hprod','exact hq_witness','have heq : x1=6')
        +_call('gaussian_multiply_cancel_left','p','x1','6','p')+('exact hn','exact hself')+_call('gaussian_multiply_one_right','p')+_call('gaussian_multiply_input_left_valid','p','x','a')+('exact hdiv_witness',)
        +_exists('x')+_call('gaussian_multiply_commutative','x','b','6')+_call('gaussian_multiply_output_transport','x','b','x1','6')+('exact heq','exact hq_witness'),
        'If a nonzero actual Gaussian product divides one factor, its other factor has a constructed inverse; no abstract domain axiom is assumed.',
    ))
    irredfields=tuple(_part('hirred',4,i) for i in range(4))
    gcdfields=tuple(_part('hcomplete_witness_witness_witness_left',3,i) for i in range(3))
    script=_intro('p','a','b','c','hirred','hprod','hdiv')+_parts('hirred',4)
    script+=(f"have hcomplete : {_completion('p','a','prime_actual_gcd')}",)+_call('gaussian_gcd_bezout_exists','p','a')+(f'exact {irredfields[0]}',)
    script+=_call('gaussian_multiply_input_left_valid','a','b','c')+('exact hprod',)+_cases('hcomplete',3)+('cases hcomplete_witness_witness_witness',)+_parts('hcomplete_witness_witness_witness_left',3)
    script+=(f'cases {gcdfields[0]}',f"have hcases : ({_unit('x','prime_gcd_unit')}) \\/ ({_unit('x3','prime_cofactor_unit')})")+_call(irredfields[3],'x','x3')+(f'exact {gcdfields[0]}_witness','cases hcases','right')
    script+=_call('gaussian_bezout_unit_divisor_cancel','p','a','b','c','x','x1','x2')+('exact hprod','exact hdiv','exact hcomplete_witness_witness_witness_right','exact hcases_left','left')
    script+=_call('gaussian_divides_transitive','p','x','a')+_call('gaussian_associate_divides','p','x')+_call('gaussian_associate_symmetric','x','p')
    script+=_call('gaussian_associate_of_unit_cofactor','x','x3','p')+('exact hcases_right',f'exact {gcdfields[0]}_witness',f'exact {gcdfields[1]}')
    rows.append(spec(
        'gaussian_irreducible_dvd_product',f"forall p a b c. ({_irreducible('p','prime_irreducible')}) -> ({_mul('a','b','c','prime_product')}) -> ({_dvd('p','c','prime_divisor')}) -> ({_dvd('p','a','prime_first')}) \\/ ({_dvd('p','b','prime_second')})",
        ('gaussian_gcd_bezout_exists','gaussian_multiply_input_left_valid','gaussian_bezout_unit_divisor_cancel','gaussian_divides_transitive','gaussian_associate_divides','gaussian_associate_symmetric','gaussian_associate_of_unit_cofactor'),
        script,
        'Every Gaussian irreducible is an actual prime divisor, proved constructively from the computed gcd and Bézout coefficients rather than assumed as a factorization axiom.',
    ))
    rows.append(spec(
        'gaussian_irreducible_is_prime',f"forall p. ({_irreducible('p','irreducible_prime_source')}) -> ({_prime('p','irreducible_prime_result')})",
        ('gaussian_irreducible_dvd_product',),
        _intro('p','h')+_parts('h',4)+('split',f"exact {_part('h',4,0)}",'split',f"exact {_part('h',4,1)}",'split',f"exact {_part('h',4,2)}")+_intro('a','b','c','hprod','hdiv')
        +_call('gaussian_irreducible_dvd_product','p','a','b','c')+('split',f"exact {_part('h',4,0)}",'split',f"exact {_part('h',4,1)}",'split',f"exact {_part('h',4,2)}",f"exact {_part('h',4,3)}",'exact hprod','exact hdiv'),
        'The actual irreducibility graph implies the full RingPrime divisor graph, retaining all carrier, nonzero and nonunit clauses.',
    ))
    rows.append(spec(
        'gaussian_prime_is_irreducible',f"forall p. ({_prime('p','prime_irreducible_source')}) -> ({_irreducible('p','prime_irreducible_result')})",
        ('gaussian_divides_reflexive','gaussian_nonzero_product_divisor_unit_cofactor','gaussian_multiply_commutative'),
        _intro('p','h')+_parts('h',4)+('split',f"exact {_part('h',4,0)}",'split',f"exact {_part('h',4,1)}",'split',f"exact {_part('h',4,2)}")+_intro('a','b','hprod')
        +(f"have hcases : ({_dvd('p','a','prime_factor_first')}) \\/ ({_dvd('p','b','prime_factor_second')})",)+_call(_part('h',4,3),'a','b','p')+('exact hprod',)+_call('gaussian_divides_reflexive','p')+(f"exact {_part('h',4,0)}",'cases hcases','right')
        +_call('gaussian_nonzero_product_divisor_unit_cofactor','p','a','b')+(f"exact {_part('h',4,1)}",'exact hprod','exact hcases_left','left')
        +_call('gaussian_nonzero_product_divisor_unit_cofactor','p','b','a')+(f"exact {_part('h',4,1)}",)+_call('gaussian_multiply_commutative','a','b','p')+('exact hprod','exact hcases_right'),
        'The full Gaussian prime-divisor graph implies genuine factor irreducibility by constructing the inverse of a cofactor of every nonzero factorization.',
    ))
    rows.append(spec(
        'gaussian_irreducible_iff_prime',f"forall p. (({_irreducible('p','iff_irreducible_first')}) -> ({_prime('p','iff_prime_first')})) /\\ (({_prime('p','iff_prime_second')}) -> ({_irreducible('p','iff_irreducible_second')}))",
        ('gaussian_irreducible_is_prime','gaussian_prime_is_irreducible'),
        _intro('p')+('split','intro h')+_call('gaussian_irreducible_is_prime','p')+('exact h','intro h')+_call('gaussian_prime_is_irreducible','p')+('exact h',),
        'Gaussian irreducibles and actual prime divisors coincide constructively, through proved arithmetic graph bridges in both directions.',
    ))
    return tuple(rows)


def make_gaussian_gcd_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (*_base_rows(spec),*_bezout_step_rows(spec),*_existence_rows(spec),*_prime_rows(spec))


__all__=['gaussian_bezout_relation','gaussian_gcd_relation','make_gaussian_gcd_candidate_theorems']
