"""Actual Gaussian divisibility, Euclidean decisions and unit associates.

The divisor graph constructs a genuine Gaussian quotient.  Its decision
procedure uses the already proved Euclidean division and strict norm bound;
it is not a supplied divisibility oracle or an extra algebraic axiom.
"""

from __future__ import annotations

from typing import Any,Callable

from .gaussian_ring_candidate import _call,_intro,_exists,_cases,_parts,_part,_and,_dvd,_unit,_associate,_irreducible,_valid,_mul,_add,_norm
from . import gaussian_euclidean_candidate as ge


_divrem=ge._code_divrem
_euclidean=ge._code_euclidean
_lt=ge._lt
_le=ge._le


def _basic_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_divides_input_valid',f"forall d z. ({_dvd('d','z','divisor_domain')}) -> ({_valid('d','divisor_valid')})",
            ('gaussian_multiply_input_left_valid',),_intro('d','z','h')+('cases h',)+_call('gaussian_multiply_input_left_valid','d','x','z')+('exact h_witness',),
            'A witnessed Gaussian divisor belongs to the actual canonical Gaussian carrier.',
        ),
        spec(
            'gaussian_divides_value_valid',f"forall d z. ({_dvd('d','z','dividend_domain')}) -> ({_valid('z','dividend_valid')})",
            ('gaussian_multiply_output_valid',),_intro('d','z','h')+('cases h',)+_call('gaussian_multiply_output_valid','d','x','z')+('exact h_witness',),
            'An actually divisible Gaussian value has a valid canonical carrier code.',
        ),
        spec(
            'gaussian_divides_reflexive',f"forall z. ({_valid('z','reflexive_domain')}) -> ({_dvd('z','z','reflexive_division')})",
            ('gaussian_multiply_one_right',),_intro('z','h')+_exists('6')+_call('gaussian_multiply_one_right','z')+('exact h',),
            'Each actual Gaussian integer divides itself with canonical quotient six, the Gaussian identity.',
        ),
        spec(
            'gaussian_divides_zero',f"forall z. ({_valid('z','divides_zero_domain')}) -> ({_dvd('z','0','divides_zero')})",
            ('gaussian_multiply_zero_right',),_intro('z','h')+_exists('0')+_call('gaussian_multiply_zero_right','z')+('exact h',),
            'Each actual Gaussian integer divides zero with its actual zero quotient.',
        ),
        spec(
            'gaussian_one_divides',f"forall z. ({_valid('z','one_divides_domain')}) -> ({_dvd('6','z','one_divides')})",
            ('gaussian_multiply_one_left',),_intro('z','h')+_exists('z')+_call('gaussian_multiply_one_left','z')+('exact h',),
            'The actual Gaussian identity divides every valid Gaussian integer.',
        ),
        spec(
            'gaussian_zero_divides_only_zero',f"forall z. ({_dvd('0','z','zero_divisor')}) -> z=0",
            ('gaussian_multiply_functional','gaussian_multiply_zero_left','gaussian_multiply_input_right_valid'),
            _intro('z','h')+('cases h',)+_call('gaussian_multiply_functional','0','x','z','0')+('exact h_witness',)+_call('gaussian_multiply_zero_left','x')+_call('gaussian_multiply_input_right_valid','0','x','z')+('exact h_witness',),
            'A zero Gaussian divisor can divide only the actual zero code.',
        ),
        spec(
            'gaussian_divides_transitive',f"forall d a z. ({_dvd('d','a','transitive_first')}) -> ({_dvd('a','z','transitive_second')}) -> ({_dvd('d','z','transitive_result')})",
            ('gaussian_multiply_exists','gaussian_multiply_input_right_valid','gaussian_multiply_associative'),
            _intro('d','a','z','hA','hZ')+('cases hA','cases hZ',f"have hq : exists q. ({_mul('x','x1','q','transitive_quotient')})")
            +_call('gaussian_multiply_exists','x','x1')+_call('gaussian_multiply_input_right_valid','d','x','a')+('exact hA_witness',)+_call('gaussian_multiply_input_right_valid','a','x1','z')+('exact hZ_witness','cases hq')
            +_exists('x2')+_call('gaussian_multiply_associative','d','x','x1','a','x2','z')+('exact hA_witness','exact hZ_witness','exact hq_witness'),
            'Compose actual Gaussian quotient witnesses using the proved canonical multiplication law.',
        ),
        spec(
            'gaussian_divides_product_left',f"forall d a b c. ({_dvd('d','a','product_divisor')}) -> ({_mul('a','b','c','product_multiple')}) -> ({_dvd('d','c','product_divides')})",
            ('gaussian_divides_transitive',),_intro('d','a','b','c','hd','hprod')+_call('gaussian_divides_transitive','d','a','c')+('exact hd',)+_exists('b')+('exact hprod',),
            'An actual divisor of the first factor divides the actual Gaussian product.',
        ),
        spec(
            'gaussian_divides_product_right',f"forall d a b c. ({_dvd('d','b','product_right_divisor')}) -> ({_mul('a','b','c','product_right_multiple')}) -> ({_dvd('d','c','product_right_divides')})",
            ('gaussian_divides_product_left','gaussian_multiply_commutative'),_intro('d','a','b','c','hd','hprod')+_call('gaussian_divides_product_left','d','b','a','c')+('exact hd',)+_call('gaussian_multiply_commutative','a','b','c')+('exact hprod',),
            'An actual divisor of the second factor also divides the actual Gaussian product.',
        ),
        spec(
            'gaussian_common_divisor_add',f"forall d a b c. ({_dvd('d','a','sum_first_divisor')}) -> ({_dvd('d','b','sum_second_divisor')}) -> ({_add('a','b','c','sum_given')}) -> ({_dvd('d','c','sum_result')})",
            ('gaussian_add_exists','gaussian_multiply_input_right_valid','gaussian_multiply_add_compose'),
            _intro('d','a','b','c','hA','hB','hsum')+('cases hA','cases hB',f"have hq : exists q. ({_add('x','x1','q','sum_quotient')})")
            +_call('gaussian_add_exists','x','x1')+_call('gaussian_multiply_input_right_valid','d','x','a')+('exact hA_witness',)+_call('gaussian_multiply_input_right_valid','d','x1','b')+('exact hB_witness','cases hq')
            +_exists('x2')+_call('gaussian_multiply_add_compose','d','x','x1','x2','a','b','c')+('exact hq_witness','exact hA_witness','exact hB_witness','exact hsum'),
            'A common Gaussian divisor divides the actual sum, with the sum of quotient codes genuinely constructed.',
        ),
        spec(
            'gaussian_common_divisor_subtract',f"forall d a b c. ({_dvd('d','a','difference_first_divisor')}) -> ({_dvd('d','b','difference_second_divisor')}) -> ({_add('c','b','a','difference_equation')}) -> ({_dvd('d','c','difference_result')})",
            ('gaussian_subtract_exists','gaussian_multiply_input_right_valid','gaussian_multiply_input_left_valid','gaussian_add_input_left_valid','gaussian_multiply_exists','gaussian_multiply_add_distribute','gaussian_add_cancel_right','gaussian_multiply_output_transport'),
            _intro('d','a','b','c','hA','hB','hdifference')+('cases hA','cases hB',f"have hq : exists q. ({_add('q','x1','x','difference_quotient')})")
            +_call('gaussian_subtract_exists','x','x1')+_call('gaussian_multiply_input_right_valid','d','x','a')+('exact hA_witness',)+_call('gaussian_multiply_input_right_valid','d','x1','b')+('exact hB_witness','cases hq',f"have hprod : exists p. ({_mul('d','x2','p','difference_constructed')})")
            +_call('gaussian_multiply_exists','d','x2')+_call('gaussian_multiply_input_left_valid','d','x','a')+('exact hA_witness',)+_call('gaussian_add_input_left_valid','x2','x1','x')+('exact hq_witness','cases hprod')
            +(f"have hsum : {_add('x3','b','a','difference_reconstructed')}",)+_call('gaussian_multiply_add_distribute','d','x2','x1','x','x3','b','a')+('exact hq_witness','exact hprod_witness','exact hB_witness','exact hA_witness','have heq : x3=c')
            +_call('gaussian_add_cancel_right','x3','c','b','a')+('exact hsum','exact hdifference')+_exists('x2')+_call('gaussian_multiply_output_transport','d','x2','x3','c')+('exact heq','exact hprod_witness'),
            'A common Gaussian divisor divides an actual difference; quotient subtraction is constructed and verified in the real ring graph.',
        ),
        spec(
            'gaussian_unit_divides',f"forall u z. ({_unit('u','unit_divisor')}) -> ({_valid('z','unit_multiple_domain')}) -> ({_dvd('u','z','unit_divides')})",
            ('gaussian_divides_transitive','gaussian_one_divides'),_intro('u','z','hu','hz')+_call('gaussian_divides_transitive','u','6','z')+('exact hu',)+_call('gaussian_one_divides','z')+('exact hz',),
            'An actual unit divides every valid Gaussian value via its inverse witness and the identity.',
        ),
        spec(
            'gaussian_divisor_of_unit_is_unit',f"forall d u. ({_dvd('d','u','unit_divides_given')}) -> ({_unit('u','unit_dividend')}) -> ({_unit('d','unit_divisor_result')})",
            ('gaussian_unit_factor_left',),_intro('d','u','hd','hu')+('cases hd',)+_call('gaussian_unit_factor_left','d','x','u')+('exact hd_witness','exact hu'),
            'Every actual Gaussian divisor of a unit is itself a unit.',
        ),
    )


def _euclidean_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_common_divisor_euclidean_forward',f"forall d a b q r. ({_divrem('a','b','q','r','euclid_forward_equation')}) -> ({_dvd('d','b','euclid_forward_divisor')}) -> ({_dvd('d','r','euclid_forward_remainder')}) -> ({_dvd('d','a','euclid_forward_result')})",
            ('gaussian_common_divisor_add','gaussian_divides_product_left'),
            _intro('d','a','b','q','r','heq','hb','hr')+('cases heq','cases heq_witness')+_call('gaussian_common_divisor_add','d','x','r','a')
            +_call('gaussian_divides_product_left','d','b','q','x')+('exact hb','exact heq_witness_left','exact hr','exact heq_witness_right'),
            'Every common divisor of the divisor and remainder divides the actual Gaussian dividend.',
        ),
        spec(
            'gaussian_common_divisor_euclidean_backward',f"forall d a b q r. ({_divrem('a','b','q','r','euclid_backward_equation')}) -> ({_dvd('d','a','euclid_backward_dividend')}) -> ({_dvd('d','b','euclid_backward_divisor')}) -> ({_dvd('d','r','euclid_backward_result')})",
            ('gaussian_common_divisor_subtract','gaussian_divides_product_left','gaussian_add_commutative'),
            _intro('d','a','b','q','r','heq','ha','hb')+('cases heq','cases heq_witness')+_call('gaussian_common_divisor_subtract','d','a','x','r')+('exact ha',)
            +_call('gaussian_divides_product_left','d','b','q','x')+('exact hb','exact heq_witness_left')+_call('gaussian_add_commutative','x','r','a')+('exact heq_witness_right',),
            'Every common divisor of the actual Gaussian dividend and divisor also divides the actual remainder.',
        ),
        spec(
            'gaussian_division_zero_remainder_divides',f"forall a b q r. ({_divrem('a','b','q','r','zero_remainder_equation')}) -> r=0 -> ({_dvd('b','a','zero_remainder_divides')})",
            ('gaussian_add_functional','gaussian_add_zero_right','gaussian_multiply_output_valid','gaussian_multiply_output_transport'),
            _intro('a','b','q','r','heq','hr')+('cases heq','cases heq_witness','rewrite hr at heq_witness_right','have houtput : a=x')
            +_call('gaussian_add_functional','x','0','a','x')+('exact heq_witness_right',)+_call('gaussian_add_zero_right','x')+_call('gaussian_multiply_output_valid','b','q','x')+('exact heq_witness_left',)
            +_exists('q')+_call('gaussian_multiply_output_transport','b','q','x','a')+('symm','exact houtput','exact heq_witness_left'),
            'An actual Gaussian zero remainder gives an actual quotient witnessing divisibility.',
        ),
        spec(
            'gaussian_division_divisible_remainder_zero',f"forall a b q r U V. ({_divrem('a','b','q','r','divisible_equation')}) -> ({_norm('r','U','divisible_remainder_norm')}) -> ({_norm('b','V','divisible_divisor_norm')}) -> "
            f"({_lt('U','V','divisible_strict')}) -> ({_dvd('b','a','divisible_given')}) -> r=0",
            ('gaussian_common_divisor_euclidean_backward','gaussian_divides_reflexive','gaussian_norm_input_valid','gaussian_norm_exists','gaussian_multiply_input_right_valid','gaussian_norm_functional','gaussian_norm_multiply','four_square_bounded_multiple_is_zero','gaussian_norm_zero_implies_code_zero','gaussian_norm_value_transport'),
            _intro('a','b','q','r','U','V','heq','hr','hb','hlt','hdiv')+(f"have hrem : {_dvd('b','r','divisible_remainder')}",)
            +_call('gaussian_common_divisor_euclidean_backward','b','a','b','q','r')+('exact heq','exact hdiv')+_call('gaussian_divides_reflexive','b')+_call('gaussian_norm_input_valid','b','V')+('exact hb','cases hrem')
            +(f"have hM : exists M. ({_norm('x','M','divisible_quotient_norm')})",)+_call('gaussian_norm_exists','x')+_call('gaussian_multiply_input_right_valid','b','x','r')+('exact hrem_witness','cases hM','have hvalue : U=V*x1')
            +_call('gaussian_norm_functional','r','U','V*x1')+('exact hr',)+_call('gaussian_norm_multiply','b','x','r','V','x1')+('exact hb','exact hM_witness','exact hrem_witness','have hzero : U=0')
            +_call('four_square_bounded_multiple_is_zero','V','U')+('exact hlt',)+_exists('x1')+('exact hvalue',)+_call('gaussian_norm_zero_implies_code_zero','r')+_call('gaussian_norm_value_transport','r','U','0')+('exact hzero','exact hr'),
            'A strictly norm-bounded Gaussian remainder must vanish when the original divisor actually divides the dividend.',
        ),
        spec(
            'gaussian_divides_decidable',f"forall d z. ({_valid('d','decision_divisor')}) -> ({_valid('z','decision_dividend')}) -> ({_dvd('d','z','decision_yes')}) \\/ ~({_dvd('d','z','decision_no')})",
            ('eq_decidable','gaussian_multiply_zero_right','gaussian_zero_valid','gaussian_zero_divides_only_zero','gaussian_euclidean_division_exists','gaussian_division_zero_remainder_divides','gaussian_division_divisible_remainder_zero'),
            _intro('d','z','hd','hz')+('have hdc : d=0 \\/ ~(d=0)',)+_call('eq_decidable','d','0')+('cases hdc','have hzc : z=0 \\/ ~(z=0)')+_call('eq_decidable','z','0')
            +('cases hzc','left')+_exists('0')+('rewrite hdc_left','rewrite hzc_left')+_call('gaussian_multiply_zero_right','0')+('exact gaussian_zero_valid','right','intro hdiv','apply hzc_right')
            +_call('gaussian_zero_divides_only_zero','z')+('rewrite hdc_left at hdiv','exact hdiv',f"have hex : exists q r U V. ({_euclidean('z','d','q','r','U','V','decision_actual_division')})")
            +_call('gaussian_euclidean_division_exists','z','d')+('exact hz','exact hd','exact hdc_right')+_cases('hex',4)+_parts('hex'+'_witness'*4,6)
            +('have hrc : x1=0 \\/ ~(x1=0)',)+_call('eq_decidable','x1','0')+('cases hrc','left')+_call('gaussian_division_zero_remainder_divides','z','d','x','x1')
            +(f"exact {_part('hex'+'_witness'*4,6,2)}",'exact hrc_left','right','intro hdiv','apply hrc_right')+_call('gaussian_division_divisible_remainder_zero','z','d','x','x1','x2','x3')
            +tuple(f"exact {_part('hex'+'_witness'*4,6,i)}" for i in (2,3,4,5))+('exact hdiv',),
            'Constructively decide actual Gaussian divisibility by computing Euclidean quotient/remainder data; handle a zero divisor explicitly.',
        ),
    )


def _associate_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_associate_reflexive',f"forall a. ({_valid('a','associate_refl_domain')}) -> ({_associate('a','a','associate_refl')})",
            ('gaussian_one_unit','gaussian_multiply_one_left'),
            _intro('a','h')+_exists('6')+('split','exact gaussian_one_unit')+_call('gaussian_multiply_one_left','a')+('exact h',),
            'Every Gaussian integer is associated to itself by the actual unit code six.',
        ),
        spec(
            'gaussian_associate_symmetric',f"forall a b. ({_associate('a','b','associate_forward')}) -> ({_associate('b','a','associate_reverse')})",
            ('gaussian_unit_inverse','gaussian_multiply_associative','gaussian_multiply_one_left','gaussian_multiply_input_right_valid'),
            _intro('a','b','h')+('cases h','cases h_witness',f"have hinverse : exists v. {_and(_unit('v','associate_inverse_unit'),_mul('x','v','6','associate_inverse_first'),_mul('v','x','6','associate_inverse_second'))}")
            +_call('gaussian_unit_inverse','x')+('exact h_witness_left','cases hinverse')+_parts('hinverse_witness',3)
            +_exists('x1')+('split',f"exact {_part('hinverse_witness',3,0)}")+_call('gaussian_multiply_associative','x1','x','a','6','b','a')
            +(f"exact {_part('hinverse_witness',3,2)}",)+_call('gaussian_multiply_one_left','a')+_call('gaussian_multiply_input_right_valid','x','a','b')+('exact h_witness_right','exact h_witness_right'),
            'Invert the actual unit witness to reverse Gaussian association, including the zero boundary.',
        ),
        spec(
            'gaussian_associate_transitive',f"forall a b c. ({_associate('a','b','associate_first')}) -> ({_associate('b','c','associate_second')}) -> ({_associate('a','c','associate_composite')})",
            ('gaussian_multiply_exists','gaussian_unit_valid','gaussian_unit_product','gaussian_multiply_associative_reverse'),
            _intro('a','b','c','hA','hB')+('cases hA','cases hA_witness','cases hB','cases hB_witness',f"have hproduct : exists u. ({_mul('x1','x','u','associate_product')})")
            +_call('gaussian_multiply_exists','x1','x')+_call('gaussian_unit_valid','x1')+('exact hB_witness_left',)+_call('gaussian_unit_valid','x')+('exact hA_witness_left','cases hproduct')
            +_exists('x2')+('split',)+_call('gaussian_unit_product','x1','x','x2')+('exact hproduct_witness','exact hB_witness_left','exact hA_witness_left')
            +_call('gaussian_multiply_associative_reverse','x1','x','a','x2','b','c')+('exact hproduct_witness','exact hA_witness_right','exact hB_witness_right'),
            'Compose actual unit witnesses and their canonical products to prove transitive Gaussian association.',
        ),
        spec(
            'gaussian_associate_of_unit_cofactor',f"forall a u b. ({_unit('u','associate_cofactor_unit')}) -> ({_mul('a','u','b','associate_cofactor_product')}) -> ({_associate('a','b','associate_cofactor')})",
            ('gaussian_multiply_commutative',),
            _intro('a','u','b','hu','hprod')+_exists('u')+('split','exact hu')+_call('gaussian_multiply_commutative','a','u','b')+('exact hprod',),
            'A genuinely unit cofactor supplies the witnessed association relation.',
        ),
        spec(
            'gaussian_associate_divides',f"forall a b. ({_associate('a','b','associate_division')}) -> ({_dvd('a','b','associate_divides')})",
            ('gaussian_multiply_commutative',),
            _intro('a','b','h')+('cases h','cases h_witness')+_exists('x')+_call('gaussian_multiply_commutative','x','a','b')+('exact h_witness_right',),
            'Associated Gaussian integers are actually divisible, using the given unit as quotient.',
        ),
        spec(
            'gaussian_associate_norm',f"forall a b N. ({_associate('a','b','associate_norm_given')}) -> ({_norm('a','N','associate_norm_first')}) -> ({_norm('b','N','associate_norm_second')})",
            ('gaussian_norm_value_transport','one_mul','gaussian_norm_multiply','gaussian_unit_has_norm_one'),
            _intro('a','b','N','h','hn')+('cases h','cases h_witness')+_call('gaussian_norm_value_transport','b','1*N','N')+_call('one_mul','N')
            +_call('gaussian_norm_multiply','x','a','b','1','N')+_call('gaussian_unit_has_norm_one','x')+('exact h_witness_left','exact hn','exact h_witness_right'),
            'A witnessed Gaussian unit association preserves the actual squared norm.',
        ),
        spec(
            'gaussian_mutual_divisibility_associate',f"forall a b. ({_dvd('a','b','mutual_first')}) -> ({_dvd('b','a','mutual_second')}) -> ({_associate('a','b','mutual_association')})",
            ('eq_decidable','gaussian_zero_divides_only_zero','gaussian_one_unit','gaussian_multiply_one_left','gaussian_zero_valid','gaussian_multiply_exists','gaussian_multiply_input_right_valid','gaussian_multiply_input_left_valid','gaussian_multiply_associative','gaussian_multiply_cancel_left','gaussian_multiply_one_right','gaussian_multiply_output_transport','gaussian_multiply_commutative'),
            _intro('a','b','hA','hB')+('have ha : a=0 \\/ ~(a=0)',)+_call('eq_decidable','a','0')+('cases ha','have hb : b=0')
            +_call('gaussian_zero_divides_only_zero','b')+('rewrite ha_left at hA','exact hA')+_exists('6')+('split','exact gaussian_one_unit','rewrite ha_left','rewrite hb')
            +_call('gaussian_multiply_one_left','0')+('exact gaussian_zero_valid','cases hA','cases hB',f"have hq : exists q. ({_mul('x','x1','q','mutual_quotient_product')})")
            +_call('gaussian_multiply_exists','x','x1')+_call('gaussian_multiply_input_right_valid','a','x','b')+('exact hA_witness',)+_call('gaussian_multiply_input_right_valid','b','x1','a')+('exact hB_witness','cases hq',f"have hself : {_mul('a','x2','a','mutual_self')}")
            +_call('gaussian_multiply_associative','a','x','x1','b','x2','a')+('exact hA_witness','exact hB_witness','exact hq_witness','have heq : x2=6')
            +_call('gaussian_multiply_cancel_left','a','x2','6','a')+('exact ha_right','exact hself')+_call('gaussian_multiply_one_right','a')+_call('gaussian_multiply_input_left_valid','a','x','b')+('exact hA_witness',)
            +_exists('x')+('split',)+_exists('x1')+_call('gaussian_multiply_output_transport','x','x1','x2','6')+('exact heq','exact hq_witness')+_call('gaussian_multiply_commutative','a','x','b')+('exact hA_witness',),
            'Mutual actual divisibility is witnessed association, with the all-zero case handled explicitly and the nonzero case using real multiplication cancellation.',
        ),
    )


def _norm_irreducible_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_divisor_norm_factor',f"forall d z D N. ({_dvd('d','z','norm_factor_divisor')}) -> ({_norm('d','D','norm_factor_first')}) -> ({_norm('z','N','norm_factor_total')}) -> exists q Q. "
            +_and(_mul('d','q','z','norm_factor_product'),_norm('q','Q','norm_factor_quotient'),'N=D*Q'),
            ('gaussian_norm_exists','gaussian_multiply_input_right_valid','gaussian_norm_functional','gaussian_norm_multiply'),
            _intro('d','z','D','N','hdiv','hd','hz')+('cases hdiv',f"have hn : exists Q. ({_norm('x','Q','norm_factor_constructed')})")
            +_call('gaussian_norm_exists','x')+_call('gaussian_multiply_input_right_valid','d','x','z')+('exact hdiv_witness','cases hn')+_exists('x','x1')+('split','exact hdiv_witness','split','exact hn_witness')
            +_call('gaussian_norm_functional','z','N','D*x1')+('exact hz',)+_call('gaussian_norm_multiply','d','x','z','D','x1')+('exact hd','exact hn_witness','exact hdiv_witness'),
            'An actual Gaussian divisor has a constructed quotient norm, and the ordinary natural norms factor exactly.',
        ),
        spec(
            'gaussian_divisor_norm_bound',f"forall d z D N. ({_dvd('d','z','norm_bound_divisor')}) -> ({_norm('d','D','norm_bound_first')}) -> ({_norm('z','N','norm_bound_total')}) -> ~(z=0) -> ({_le('D','N','norm_bound')})",
            ('gaussian_divisor_norm_factor','gaussian_norm_nonzero','nonzero_is_succ'),
            _intro('d','z','D','N','hdiv','hd','hz','hnz')+(f"have hfactor : exists q Q. {_and(_mul('d','q','z','norm_bound_product'),_norm('q','Q','norm_bound_quotient'),'N=D*Q')}",)
            +_call('gaussian_divisor_norm_factor','d','z','D','N')+('exact hdiv','exact hd','exact hz')+_cases('hfactor',2)+_parts('hfactor_witness_witness',3)
            +('have hpositive : ~(x1=0)','intro hzero')+_call('gaussian_norm_nonzero','z','N')+('exact hz','exact hnz',f"rewrite hzero at {_part('hfactor_witness_witness',3,2)}",'trans D*0',f"exact {_part('hfactor_witness_witness',3,2)}",'simp','have hsucc : exists h. x1=S h')
            +_call('nonzero_is_succ','x1')+('exact hpositive','cases hsucc')+_exists('D*x2')+(f"rewrite hsucc_witness at {_part('hfactor_witness_witness',3,2)}",f"rewrite {_part('hfactor_witness_witness',3,2)}",'simp'),
            'Every actual divisor of a nonzero Gaussian value has norm at most the value norm; the positive quotient-norm gap is constructed explicitly.',
        ),
        spec(
            'gaussian_nonunit_divisor_of_irreducible_is_associate',f"forall p q. ~({_unit('p','irreducible_divisor_nonunit')}) -> ({_irreducible('q','irreducible_dividend')}) -> ({_dvd('p','q','irreducible_divisor')}) -> ({_associate('p','q','irreducible_divisor_associate')})",
            ('gaussian_associate_of_unit_cofactor',),
            _intro('p','q','hp','hq','hdiv')+_parts('hq',4)+('cases hdiv',f"specialize {_part('hq',4,3)} p",f"specialize {_part('hq',4,3)} x",f"have hcases : ({_unit('p','irreducible_first_case')}) \\/ ({_unit('x','irreducible_second_case')})",f"apply {_part('hq',4,3)}",'exact hdiv_witness','cases hcases','exfalso','apply hp','exact hcases_left')
            +_call('gaussian_associate_of_unit_cofactor','p','x','q')+('exact hcases_right','exact hdiv_witness'),
            'An actual nonunit divisor of an irreducible Gaussian integer differs from it by a constructed unit, not merely a norm equality.',
        ),
        spec(
            'gaussian_irreducible_divides_irreducible_associate',f"forall p q. ({_irreducible('p','irreducible_first')}) -> ({_irreducible('q','irreducible_second')}) -> ({_dvd('p','q','irreducible_divides')}) -> ({_associate('p','q','irreducible_associate')})",
            ('gaussian_nonunit_divisor_of_irreducible_is_associate',),
            _intro('p','q','hp','hq','hdiv')+_parts('hp',4)+_call('gaussian_nonunit_divisor_of_irreducible_is_associate','p','q')+(f"exact {_part('hp',4,2)}",'exact hq','exact hdiv'),
            'Two irreducible Gaussian factors with actual divisibility are associated by a witnessed unit.',
        ),
    )


def make_gaussian_divisibility_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (*_basic_rows(spec),*_euclidean_rows(spec),*_associate_rows(spec),*_norm_irreducible_rows(spec))


__all__=['make_gaussian_divisibility_candidate_theorems']
