"""Constructive finite Gaussian factor search over the unchanged G081 carrier.

The search enumerates actual pairs of canonical signed-coordinate codes.
It does not assume that every natural number is a valid Gaussian code, and
it does not turn a negated universal factorization claim into a witness by
classical logic.  These are unsealed authoring candidates, not admission.
"""

from __future__ import annotations

from typing import Any, Callable

from . import gaussian_euclidean_candidate as ge
from . import gaussian_ring_candidate as gr


_and=gr._and
_call=gr._call
_intro=gr._intro
_exists=gr._exists
_cases=gr._cases
_parts=gr._parts
_part=gr._part
_norm=gr._norm
_valid=gr._valid
_mul=gr._mul
_unit=gr._unit
_dvd=gr._dvd
_irreducible=gr._irreducible
_le=ge._le
_lt=ge._lt
_pair=ge._pair


def _bounded_coordinates(z: str,N: str,tag: str) -> str:
    rc,ic=gr._names(tag,'search_real','search_imaginary')
    return f"exists {rc} {ic}. "+_and(f"({z})={_pair(rc,ic)}",_le(rc,f'2*({N})',tag+'real_bound'),_le(ic,f'2*({N})',tag+'imaginary_bound'))


def gaussian_norm_bounded_coordinates_relation(z: str,N: str,*,tag: str,variables: tuple[str,...]) -> str:
    """Actual canonical pair coordinates bounded by twice the given norm."""
    return gr._definition(_bounded_coordinates,(z,N),tag=tag,variables=variables)


def _proper(d: str,z: str,N: str,tag: str) -> str:
    D,=gr._names(tag,'proper_divisor_norm')
    return _and(f"~({_unit(d,tag+'nonunit')})",_dvd(d,z,tag+'quotient'),f"exists {D}. "+_and(_norm(d,D,tag+'norm'),_lt(D,N,tag+'strict')))


def gaussian_proper_norm_divisor_relation(d: str,z: str,N: str,*,tag: str,variables: tuple[str,...]) -> str:
    """An actual nonunit divisor with actual norm strictly below the bound N."""
    return gr._definition(_proper,(d,z,N),tag=tag,variables=variables)


def _row_search(z: str,N: str,rc: str,k: str,tag: str) -> str:
    ic,=gr._names(tag,'row_coordinate')
    yes=f"exists {ic}. "+_and(_lt(ic,k,tag+'found_index'),_proper(_pair(rc,ic),z,N,tag+'found'))
    no=f"forall {ic}. ({_lt(ic,k,tag+'absent_index')}) -> ~({_proper(_pair(rc,ic),z,N,tag+'absent')})"
    return f"({yes}) \\/ ({no})"


def _rectangle_search(z: str,N: str,h: str,k: str,tag: str) -> str:
    rc,ic=gr._names(tag,'rectangle_real','rectangle_imaginary')
    yes=f"exists {rc} {ic}. "+_and(_lt(rc,h,tag+'found_real'),_lt(ic,k,tag+'found_imaginary'),_proper(_pair(rc,ic),z,N,tag+'found'))
    no=f"forall {rc} {ic}. ({_lt(rc,h,tag+'absent_real')}) -> ({_lt(ic,k,tag+'absent_imaginary')}) -> ~({_proper(_pair(rc,ic),z,N,tag+'absent')})"
    return f"({yes}) \\/ ({no})"


def _split_factorization(z: str,N: str,a: str,b: str,A: str,B: str,tag: str) -> str:
    return _and(_mul(a,b,z,tag+'product'),_norm(a,A,tag+'first_norm'),_norm(b,B,tag+'second_norm'),
                f"~({_unit(a,tag+'first_nonunit')})",f"~({_unit(b,tag+'second_nonunit')})",
                _lt(A,N,tag+'first_strict'),_lt(B,N,tag+'second_strict'))


def gaussian_strict_nonunit_factorization_relation(z: str,N: str,a: str,b: str,A: str,B: str,*,tag: str,variables: tuple[str,...]) -> str:
    """Actual product of two nonunits with their actual, strictly smaller norms."""
    return gr._definition(_split_factorization,(z,N,a,b,A,B),tag=tag,variables=variables)


def _complete_search(z: str,N: str,tag: str) -> str:
    d,=gr._names(tag,'complete_divisor')
    return f"(exists {d}. ({_proper(d,z,N,tag+'found')})) \\/ (forall {d}. ~({_proper(d,z,N,tag+'absent')}))"


def _irreducible_or_split(z: str,N: str,tag: str) -> str:
    a,b,A,B=gr._names(tag,'split_first','split_second','split_first_norm','split_second_norm')
    return f"({_irreducible(z,tag+'irreducible')}) \\/ (exists {a} {b} {A} {B}. ({_split_factorization(z,N,a,b,A,B,tag+'split')}))"


def _coordinate_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_search_natural_le_square',f"forall n. ({_le('n','n*n','natural_square')})",
            ('eq_decidable','le_scaled_nonzero'),
            _intro('n')+('have hn : n=0 \\/ ~(n=0)',)+_call('eq_decidable','n','0')+('cases hn','exists 0','simp [hn_left]')
            +_call('le_scaled_nonzero','n','n')+('exact hn_right',),
            'Every natural is at most its square, including zero, by constructive equality decision.',
        ),
        spec(
            'gaussian_search_signed_code_bound',
            f"forall code p n R N. ({ge._sd('code','p','n','search_signed_decode')}) -> ({ge._square('p','n','R')}) -> ({_le('R','N','search_square_bound')}) -> ({_le('code','2*N','search_code_bound')})",
            ('gaussian_search_natural_le_square','le_trans','mul_le_mul_left','add_succ_left','zero_add','mul_zero_left'),
            _intro('code','p','n','R','N','hsigned','hsquare','hbound')+('cases hsigned','cases hsigned_left',
                'have heq : p*p=R','trans p*p+n*n','simp [hsigned_left_right]','trans R+(p*n+n*p)','exact hsquare',
                'simp [hsigned_left_right, zero_add, mul_zero_left]','rewrite hsigned_left_left')
            +_call('mul_le_mul_left','p','N','2')+_call('le_trans','p','p*p','N')+_call('gaussian_search_natural_le_square','p')
            +('rewrite heq','exact hbound','cases hsigned_right','cases hsigned_right_witness','cases hsigned_right_witness_left',
              'have heq : S x*S x=R','trans p*p+n*n','simp [hsigned_right_witness_left_right, hsigned_right_witness_right, zero_add]',
              'trans R+(p*n+n*p)','exact hsquare','simp [hsigned_right_witness_left_right, mul_zero_left]',
              f"have hsmall : ({_le('S x','N','negative_magnitude_bound')})")
            +_call('le_trans','S x','S x*S x','N')+_call('gaussian_search_natural_le_square','S x')+('rewrite heq','exact hbound',
              'rewrite hsigned_right_witness_left_left')
            +_call('le_trans','2*x+1','2*S x','2*N')+('exists 1','simp [add_succ_left, zero_add]')
            +_call('mul_le_mul_left','S x','N','2')+('exact hsmall',),
            'A canonical signed code for an integer whose square is bounded by N is at most 2N, for both signs and zero.',
        ),
        spec(
            'gaussian_search_pair_valid',f"forall rc ic. ({_valid(_pair('rc','ic'),'search_pair_carrier')})",
            ('signed_decode_total',),
            _intro('rc','ic')+(f"have hr : exists p n. ({ge._sd('rc','p','n','search_real_total')})",)+_call('signed_decode_total','rc')+_cases('hr',2)
            +(f"have hi : exists p n. ({ge._sd('ic','p','n','search_imaginary_total')})",)+_call('signed_decode_total','ic')+_cases('hi',2)
            +_exists('x','x1','x2','x3','rc','ic')+('split','refl','split','exact hr_witness_witness','exact hi_witness_witness'),
            'Every pair of canonical signed-coordinate codes constructs a valid Gaussian code; arbitrary natural codes are not presumed valid.',
        ),
        spec(
            'gaussian_norm_bounded_coordinates',f"forall z N. ({_norm('z','N','search_given_norm')}) -> ({_bounded_coordinates('z','N','search_bounded_coordinates')})",
            ('gaussian_norm_input_valid','gaussian_decode_representation','gaussian_norm_for_representation','gaussian_search_signed_code_bound','add_comm'),
            _intro('z','N','hnorm')+(f"have hvalid : ({_valid('z','search_norm_valid')})",)+_call('gaussian_norm_input_valid','z','N')+('exact hnorm',)+_cases('hvalid',4)
            +(f"have hraw : ({ge._norm('x','x1','x2','x3','N','search_canonical_norm')})",)
            +_call('gaussian_norm_for_representation','z','x','x1','x2','x3','N')+_call('gaussian_decode_representation','z','x','x1','x2','x3')
            +('exact hvalid_witness_witness_witness_witness','exact hnorm')+_cases('hvalid_witness_witness_witness_witness',2)+_parts('hvalid'+'_witness'*6,3)
            +_cases('hraw',2)+_parts('hraw_witness_witness',3)+_exists('x4','x5')+('split',f"exact {_part('hvalid'+'_witness'*6,3,0)}",'split')
            +_call('gaussian_search_signed_code_bound','x4','x','x1','x6','N')+(f"exact {_part('hvalid'+'_witness'*6,3,1)}",f"exact {_part('hraw_witness_witness',3,0)}",'exists x7','rewrite hraw_witness_witness_right_right','apply add_comm')
            +_call('gaussian_search_signed_code_bound','x5','x2','x3','x7','N')+(f"exact {_part('hvalid'+'_witness'*6,3,2)}",f"exact {_part('hraw_witness_witness',3,1)}",'exists x6','symm','exact hraw_witness_witness_right_right'),
            'An actual Gaussian norm bounds both canonical signed-coordinate codes; arbitrary non-normal representatives are never bounded.',
        ),
    )


def _decision_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_search_no_index_below_zero',f"forall i. ~({_lt('i','0','empty_search')})",
            ('succ_ne_zero',),_intro('i','h')+('cases h',)+_call('succ_ne_zero','x+i')+('trans x+S i','symm','apply PA4','exact h_witness'),
            'The empty search interval has no index, proved in the original natural arithmetic.',
        ),
        spec(
            'gaussian_search_two_le_nonzero_not_one',f"forall n. ~(n=0) -> ~(n=1) -> ({_le('2','n','nonunit_norm_two')})",
            ('nonzero_is_succ','one_le_of_ne_zero','succ_le_succ'),
            _intro('n','hzero','hone')+('have hs : exists k. n=S k',)+_call('nonzero_is_succ','n')+('exact hzero','cases hs','have hx : ~(x=0)','intro hxzero','apply hone','trans S x','exact hs_witness','rewrite hxzero','refl','rewrite hs_witness')
            +_call('succ_le_succ','1','x')+_call('one_le_of_ne_zero','x')+('exact hx',),
            'A nonzero natural different from one is at least two, with both small boundaries explicit.',
        ),
        spec(
            'gaussian_search_proper_divisor_code_transport',f"forall d e z N. d=e -> ({_proper('d','z','N','proper_source')}) -> ({_proper('e','z','N','proper_target')})",
            (),_intro('d','e','z','N','heq','h')+('rewrite heq at h',)*3+('exact h',),
            'Equality of actual Gaussian natural codes preserves the witnessed proper-norm-divisor graph.',
        ),
        spec(
            'gaussian_proper_norm_divisor_decidable',f"forall d z N. ({_valid('d','proper_candidate_valid')}) -> ({_valid('z','proper_target_valid')}) -> ({_proper('d','z','N','proper_decision_yes')}) \\/ ~({_proper('d','z','N','proper_decision_no')})",
            ('gaussian_unit_decidable','gaussian_divides_decidable','gaussian_norm_exists','le_or_lt','gaussian_norm_functional','lt_not_le'),
            _intro('d','z','N','hd','hz')+(f"have hu : ({_unit('d','proper_unit_yes')}) \\/ ~({_unit('d','proper_unit_no')})",)+_call('gaussian_unit_decidable','d')+('exact hd','cases hu','right','intro hp','cases hp','apply hp_left','exact hu_left',
              f"have hv : ({_dvd('d','z','proper_dvd_yes')}) \\/ ~({_dvd('d','z','proper_dvd_no')})")
            +_call('gaussian_divides_decidable','d','z')+('exact hd','exact hz','cases hv',f"have hn : exists D. ({_norm('d','D','proper_actual_norm')})")
            +_call('gaussian_norm_exists','d')+('exact hd','cases hn',f"have hb : ({_le('N','x','proper_bound_no')}) \\/ ({_lt('x','N','proper_bound_yes')})")
            +_call('le_or_lt','N','x')+('cases hb','right','intro hp')+_parts('hp',3)+('cases hp_right_right','cases hp_right_right_witness','have heq : x1=x')
            +_call('gaussian_norm_functional','d','x1','x')+('exact hp_right_right_witness_left','exact hn_witness','rewrite heq at hp_right_right_witness_right')
            +_call('lt_not_le','x','N')+('exact hp_right_right_witness_right','exact hb_left','left','split','exact hu_right','split','exact hv_left')+_exists('x')+('split','exact hn_witness','exact hb_right','right','intro hp')+_parts('hp',3)+('apply hv_right','exact hp_right_left'),
            'Decide a genuine nonunit divisor and strict actual norm bound using G081 division, norm functionality and natural order decision.',
        ),
        spec(
            'gaussian_factor_search_coordinate_row',f"forall k z N rc. ({_valid('z','row_target')}) -> ({_row_search('z','N','rc','k','row_scan')})",
            ('gaussian_search_no_index_below_zero','gaussian_proper_norm_divisor_decidable','gaussian_search_pair_valid','finite_lt_succ_eq_or_lt','lt_of_lt_of_le','le_succ_self','zero_add','gaussian_search_proper_divisor_code_transport'),
            ('induction k',)+_intro('z','N','rc','hz')+('right',)+_intro('ic','hi','hp')+_call('gaussian_search_no_index_below_zero','ic')+('exact hi',)
            +_intro('z','N','rc','hz')+(f"have hprevious : ({_row_search('z','N','rc','k','row_previous')})",)+_call('IH','z','N','rc')+('exact hz','cases hprevious','cases hprevious_left','cases hprevious_left_witness','left')+_exists('x')+('split',)
            +_call('lt_of_lt_of_le','x','k','S k')+('exact hprevious_left_witness_left',)+_call('le_succ_self','k')+('exact hprevious_left_witness_right',
              f"have hlast : ({_proper(_pair('rc','k'),'z','N','row_last_yes')}) \\/ ~({_proper(_pair('rc','k'),'z','N','row_last_no')})")
            +_call('gaussian_proper_norm_divisor_decidable',_pair('rc','k'),'z','N')+_call('gaussian_search_pair_valid','rc','k')+('exact hz','cases hlast','left')+_exists('k')+('split','exists 0','apply zero_add','exact hlast_left','right')
            +_intro('ic','hi','hp')+(f"have hc : ic=k \\/ ({_lt('ic','k','row_previous_index')})",)+_call('finite_lt_succ_eq_or_lt','k','ic')+('exact hi','cases hc','apply hlast_right')
            +_call('gaussian_search_proper_divisor_code_transport',_pair('rc','ic'),_pair('rc','k'),'z','N')+('rewrite hc_left',)*4+('refl','exact hp')
            +_call('hprevious_right','ic')+('exact hc_right','exact hp'),
            'Finite induction checks every imaginary coordinate below k, returning an actual proper divisor or a proof that none is present.',
        ),
        spec(
            'gaussian_factor_search_coordinate_rectangle',f"forall h z N k. ({_valid('z','rectangle_target')}) -> ({_rectangle_search('z','N','h','k','rectangle_scan')})",
            ('gaussian_search_no_index_below_zero','gaussian_factor_search_coordinate_row','finite_lt_succ_eq_or_lt','lt_of_lt_of_le','le_succ_self','zero_add','gaussian_search_proper_divisor_code_transport'),
            ('induction h',)+_intro('z','N','k','hz')+('right',)+_intro('rc','ic','hr','hi','hp')+_call('gaussian_search_no_index_below_zero','rc')+('exact hr',)
            +_intro('z','N','k','hz')+(f"have hprevious : ({_rectangle_search('z','N','h','k','rectangle_previous')})",)+_call('IH','z','N','k')+('exact hz','cases hprevious')+_cases('hprevious_left',2)+_parts('hprevious_left_witness_witness',3)+('left',)+_exists('x','x1')+('split',)
            +_call('lt_of_lt_of_le','x','h','S h')+('exact hprevious_left_witness_witness_left',)+_call('le_succ_self','h')+('split','exact hprevious_left_witness_witness_right_left','exact hprevious_left_witness_witness_right_right',
              f"have hlast : ({_row_search('z','N','h','k','rectangle_last_row')})")
            +_call('gaussian_factor_search_coordinate_row','k','z','N','h')+('exact hz','cases hlast','cases hlast_left','cases hlast_left_witness','left')+_exists('h','x')+('split','exists 0','apply zero_add','split','exact hlast_left_witness_left','exact hlast_left_witness_right','right')
            +_intro('rc','ic','hr','hi','hp')+(f"have hc : rc=h \\/ ({_lt('rc','h','rectangle_previous_index')})",)+_call('finite_lt_succ_eq_or_lt','h','rc')+('exact hr','cases hc')
            +_call('hlast_right','ic')+('exact hi',)+_call('gaussian_search_proper_divisor_code_transport',_pair('rc','ic'),_pair('h','ic'),'z','N')+('rewrite hc_left',)*2+('refl','exact hp')
            +_call('hprevious_right','rc','ic')+('exact hc_right','exact hi','exact hp'),
            'Two ordinary finite inductions exhaust the actual signed-coordinate rectangle, with a witness or an explicit absence theorem.',
        ),
    )


def _complete_search_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_search_bounded_coordinates_monotone',f"forall z D N. ({_bounded_coordinates('z','D','coordinates_old')}) -> ({_le('D','N','coordinates_bound_order')}) -> ({_bounded_coordinates('z','N','coordinates_new')})",
            ('mul_le_mul_left','le_trans'),
            _intro('z','D','N','hc','hb')+_cases('hc',2)+_parts('hc_witness_witness',3)
            +(f"have hscale : ({_le('2*D','2*N','coordinates_scaled_order')})",)+_call('mul_le_mul_left','D','N','2')+('exact hb',)+_exists('x','x1')+('split','exact hc_witness_witness_left','split')
            +_call('le_trans','x','2*D','2*N')+('exact hc_witness_witness_right_left','exact hscale')
            +_call('le_trans','x1','2*D','2*N')+('exact hc_witness_witness_right_right','exact hscale'),
            'A larger norm bound preserves the two actual finite signed-coordinate bounds.',
        ),
        spec(
            'gaussian_factor_search_complete',f"forall z N. ({_norm('z','N','complete_search_norm')}) -> ({_complete_search('z','N','complete_search')})",
            ('gaussian_norm_input_valid','gaussian_factor_search_coordinate_rectangle','gaussian_norm_bounded_coordinates','gaussian_search_bounded_coordinates_monotone','lt_to_le','succ_le_succ','gaussian_search_proper_divisor_code_transport'),
            _intro('z','N','hn')+(f"have hscan : ({_rectangle_search('z','N','S (2*N)','S (2*N)','complete_rectangle')})",)
            +_call('gaussian_factor_search_coordinate_rectangle','S (2*N)','z','N','S (2*N)')+_call('gaussian_norm_input_valid','z','N')+('exact hn','cases hscan')+_cases('hscan_left',2)+_parts('hscan_left_witness_witness',3)
            +('left',)+_exists(_pair('x','x1'))+('exact hscan_left_witness_witness_right_right','right')+_intro('d','hd')+_parts('hd',3)+('cases hd_right_right','cases hd_right_right_witness',
              f"have hc : ({_bounded_coordinates('d','N','complete_candidate_coordinates')})")
            +_call('gaussian_search_bounded_coordinates_monotone','d','x','N')+_call('gaussian_norm_bounded_coordinates','d','x')+('exact hd_right_right_witness_left',)+_call('lt_to_le','x','N')+('exact hd_right_right_witness_right',)
            +_cases('hc',2)+_parts('hc_witness_witness',3)+_call('hscan_right','x1','x2')
            +_call('succ_le_succ','x1','2*N')+('exact hc_witness_witness_right_left',)+_call('succ_le_succ','x2','2*N')+('exact hc_witness_witness_right_right',)
            +_call('gaussian_search_proper_divisor_code_transport','d',_pair('x1','x2'),'z','N')+('exact hc_witness_witness_left','exact hd'),
            'A finite (2N+1)-by-(2N+1) coordinate search decides whether any actual Gaussian proper-norm divisor exists, with no validity oracle.',
        ),
        spec(
            'gaussian_search_nonunit_norm_two',f"forall z N. ({_norm('z','N','nonunit_actual_norm')}) -> ~(N=0) -> ~({_unit('z','nonunit_given')}) -> ({_le('2','N','nonunit_norm_lower')})",
            ('gaussian_search_two_le_nonzero_not_one','gaussian_norm_one_is_unit','gaussian_norm_value_transport'),
            _intro('z','N','hn','hzero','hu')+_call('gaussian_search_two_le_nonzero_not_one','N')+('exact hzero','intro hone','apply hu')
            +_call('gaussian_norm_one_is_unit','z')+_call('gaussian_norm_value_transport','z','N','1')+('exact hone','exact hn'),
            'The actual nonzero norm of a Gaussian nonunit is at least two; a norm-one exception would construct an inverse.',
        ),
        spec(
            'gaussian_search_norm_factors_strict',f"forall a b A B N. ({_norm('a','A','strict_first_norm')}) -> ({_norm('b','B','strict_second_norm')}) -> N=A*B -> ~(N=0) -> ~({_unit('a','strict_first_nonunit')}) -> ~({_unit('b','strict_second_nonunit')}) -> "
            +_and(_lt('A','N','strict_first_result'),_lt('B','N','strict_second_result')),
            ('factor_nonzero_left','factor_nonzero_right','gaussian_search_nonunit_norm_two','succ_le_mul_of_two_le_right','mul_comm'),
            _intro('a','b','A','B','N','ha','hb','heq','hn','hu','hv')+('have hA : ~(A=0)','intro hz')+_call('factor_nonzero_left','N','A','B')+('exact hn','exact heq','exact hz',
              'have hB : ~(B=0)','intro hz')+_call('factor_nonzero_right','N','A','B')+('exact hn','exact heq','exact hz','split','rewrite heq')
            +_call('succ_le_mul_of_two_le_right','A','B')+('exact hA',)+_call('gaussian_search_nonunit_norm_two','b','B')+('exact hb','exact hB','exact hv',
              'have hreorder : N=B*A','trans A*B','exact heq','apply mul_comm','rewrite hreorder')
            +_call('succ_le_mul_of_two_le_right','B','A')+('exact hB',)+_call('gaussian_search_nonunit_norm_two','a','A')+('exact ha','exact hA','exact hu'),
            'In an actual nonzero product of two Gaussian nonunits, both natural factor norms are strictly smaller than the product norm.',
        ),
        spec(
            'gaussian_nonunit_factor_is_proper_norm_divisor',f"forall z N a b. ({_norm('z','N','factor_target_norm')}) -> ({_mul('a','b','z','factor_actual_product')}) -> ~(z=0) -> ~({_unit('a','factor_first_nonunit')}) -> ~({_unit('b','factor_second_nonunit')}) -> ({_proper('a','z','N','factor_proper_divisor')})",
            ('gaussian_norm_exists','gaussian_multiply_input_left_valid','gaussian_multiply_input_right_valid','gaussian_norm_functional','gaussian_norm_multiply','gaussian_search_norm_factors_strict','gaussian_norm_nonzero'),
            _intro('z','N','a','b','hn','hm','hz','hu','hv')+(f"have hA : exists A. ({_norm('a','A','factor_first_norm')})",)
            +_call('gaussian_norm_exists','a')+_call('gaussian_multiply_input_left_valid','a','b','z')+('exact hm','cases hA',f"have hB : exists B. ({_norm('b','B','factor_second_norm')})")
            +_call('gaussian_norm_exists','b')+_call('gaussian_multiply_input_right_valid','a','b','z')+('exact hm','cases hB','have heq : N=x*x1')
            +_call('gaussian_norm_functional','z','N','x*x1')+('exact hn',)+_call('gaussian_norm_multiply','a','b','z','x','x1')+('exact hA_witness','exact hB_witness','exact hm',
              f"have hstrict : {_and(_lt('x','N','factor_strict_first'),_lt('x1','N','factor_strict_second'))}")
            +_call('gaussian_search_norm_factors_strict','a','b','x','x1','N')+('exact hA_witness','exact hB_witness','exact heq','intro hzero')+_call('gaussian_norm_nonzero','z','N')+('exact hn','exact hz','exact hzero','exact hu','exact hv','cases hstrict','split','exact hu','split')
            +_exists('b')+('exact hm',)+_exists('x')+('split','exact hA_witness','exact hstrict_left'),
            'Every actual product of two nonunits supplies a genuine proper-norm divisor, so the finite search cannot miss a reducible nonzero value.',
        ),
    )


def _irreducibility_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    split_from_d=f"exists q D Q. ({_split_factorization('z','N','d','q','D','Q','proper_constructed_split')})"
    return (
        spec(
            'gaussian_search_divisor_of_nonzero_nonzero',f"forall d z. ({_dvd('d','z','nonzero_divisor')}) -> ~(z=0) -> ~(d=0)",
            ('gaussian_zero_divides_only_zero',),_intro('d','z','hd','hz','hdzero')+('apply hz',)+_call('gaussian_zero_divides_only_zero','z')+('rewrite hdzero at hd','exact hd'),
            'An actual divisor of a nonzero Gaussian value is nonzero, including the canonical zero boundary.',
        ),
        spec(
            'gaussian_proper_norm_divisor_split',f"forall d z N. ({_proper('d','z','N','proper_split_input')}) -> ({_norm('z','N','proper_split_norm')}) -> ~(z=0) -> ({split_from_d})",
            ('gaussian_divisor_norm_factor','gaussian_unit_has_norm_one','gaussian_norm_functional','mul_one','lt_irrefl_expanded','gaussian_search_norm_factors_strict','gaussian_norm_nonzero'),
            _intro('d','z','N','hd','hn','hz')+_parts('hd',3)+('cases hd_right_right','cases hd_right_right_witness',
              f"have hfactor : exists q Q. {_and(_mul('d','q','z','proper_factor_product'),_norm('q','Q','proper_factor_norm'),'N=x*Q')}")
            +_call('gaussian_divisor_norm_factor','d','z','x','N')+('exact hd_right_left','exact hd_right_right_witness_left','exact hn')+_cases('hfactor',2)+_parts('hfactor_witness_witness',3)
            +(f"have hqu : ~({_unit('x1','proper_quotient_nonunit')})",'intro hu','have heq : x2=1')
            +_call('gaussian_norm_functional','x1','x2','1')+('exact hfactor_witness_witness_right_left',)+_call('gaussian_unit_has_norm_one','x1')+('exact hu',
              'have htotal : N=x','trans x*x2','exact hfactor_witness_witness_right_right','rewrite heq','apply mul_one','rewrite htotal at hd_right_right_witness_right')
            +_call('lt_irrefl_expanded','x')+('exact hd_right_right_witness_right',
              f"have hstrict : {_and(_lt('x','N','proper_first_strict'),_lt('x2','N','proper_second_strict'))}")
            +_call('gaussian_search_norm_factors_strict','d','x1','x','x2','N')+('exact hd_right_right_witness_left','exact hfactor_witness_witness_right_left','exact hfactor_witness_witness_right_right','intro hzero')
            +_call('gaussian_norm_nonzero','z','N')+('exact hn','exact hz','exact hzero','exact hd_left','exact hqu','cases hstrict')
            +_exists('x1','x','x2')+('split','exact hfactor_witness_witness_left','split','exact hd_right_right_witness_left','split','exact hfactor_witness_witness_right_left','split','exact hd_left','split','exact hqu','split','exact hstrict_left','exact hstrict_right'),
            'A found proper-norm divisor yields an actual quotient; both factors are nonunits with strictly smaller actual norms.',
        ),
        spec(
            'gaussian_irreducible_or_strict_nonunit_factorization',f"forall z N. ({_norm('z','N','irreducible_split_norm')}) -> ~(z=0) -> ~({_unit('z','irreducible_split_nonunit')}) -> ({_irreducible_or_split('z','N','irreducible_split')})",
            ('gaussian_factor_search_complete','gaussian_proper_norm_divisor_split','gaussian_norm_input_valid','gaussian_unit_decidable','gaussian_multiply_input_left_valid','gaussian_multiply_input_right_valid','gaussian_nonunit_factor_is_proper_norm_divisor'),
            _intro('z','N','hn','hz','hu')+(f"have hsearch : ({_complete_search('z','N','irreducible_search')})",)+_call('gaussian_factor_search_complete','z','N')+('exact hn','cases hsearch','cases hsearch_left',
              f"have hs : exists q D Q. ({_split_factorization('z','N','x','q','D','Q','irreducible_found_split')})")
            +_call('gaussian_proper_norm_divisor_split','x','z','N')+('exact hsearch_left_witness','exact hn','exact hz')+_cases('hs',3)+('right',)+_exists('x','x1','x2','x3')+('exact hs_witness_witness_witness','left','split')
            +_call('gaussian_norm_input_valid','z','N')+('exact hn','split','exact hz','split','exact hu')+_intro('a','b','hm')
            +(f"have ha : ({_unit('a','irreducible_factor_left_unit')}) \\/ ~({_unit('a','irreducible_factor_left_nonunit')})",)
            +_call('gaussian_unit_decidable','a')+_call('gaussian_multiply_input_left_valid','a','b','z')+('exact hm','cases ha','left','exact ha_left',
              f"have hb : ({_unit('b','irreducible_factor_right_unit')}) \\/ ~({_unit('b','irreducible_factor_right_nonunit')})")
            +_call('gaussian_unit_decidable','b')+_call('gaussian_multiply_input_right_valid','a','b','z')+('exact hm','cases hb','right','exact hb_left','exfalso')
            +_call('hsearch_right','a')+_call('gaussian_nonunit_factor_is_proper_norm_divisor','z','N','a','b')+('exact hn','exact hm','exact hz','exact ha_right','exact hb_right'),
            'A finite constructive search proves irreducibility or produces an actual strictly norm-decreasing nonunit factorization; no classical negated-universal extraction is used.',
        ),
        spec(
            'gaussian_irreducible_decidable',f"forall z. ({_valid('z','irreducible_decision_domain')}) -> ({_irreducible('z','irreducible_decision_yes')}) \\/ ~({_irreducible('z','irreducible_decision_no')})",
            ('eq_decidable','gaussian_unit_decidable','gaussian_norm_exists','gaussian_irreducible_or_strict_nonunit_factorization'),
            _intro('z','hv')+('have hz : z=0 \\/ ~(z=0)',)+_call('eq_decidable','z','0')+('cases hz','right','intro hir')+_parts('hir',4)+(f"apply {_part('hir',4,1)}",'exact hz_left',
              f"have hu : ({_unit('z','irreducible_decision_unit_yes')}) \\/ ~({_unit('z','irreducible_decision_unit_no')})")
            +_call('gaussian_unit_decidable','z')+('exact hv','cases hu','right','intro hir')+_parts('hir',4)+(f"apply {_part('hir',4,2)}",'exact hu_left',
              f"have hn : exists N. ({_norm('z','N','irreducible_decision_norm')})")
            +_call('gaussian_norm_exists','z')+('exact hv','cases hn',f"have hs : ({_irreducible_or_split('z','x','irreducible_decision_split')})")
            +_call('gaussian_irreducible_or_strict_nonunit_factorization','z','x')+('exact hn_witness','exact hz_right','exact hu_right','cases hs','left','exact hs_left','right','intro hir')
            +_parts('hir',4)+_cases('hs_right',4)+_parts('hs_right'+'_witness'*4,7)
            +(f"have hcase : ({_unit('x1','irreducible_contradiction_left')}) \\/ ({_unit('x2','irreducible_contradiction_right')})",)
            +_call(_part('hir',4,3),'x1','x2')+(f"exact {_part('hs_right'+'_witness'*4,7,0)}",'cases hcase',f"apply {_part('hs_right'+'_witness'*4,7,3)}",'exact hcase_left',f"apply {_part('hs_right'+'_witness'*4,7,4)}",'exact hcase_right'),
            'Irreducibility of any actual Gaussian integer is constructively decidable, with zero, all units, and actual nonunit factors handled separately.',
        ),
    )


def _irreducible_divisor(p: str,z: str,tag: str) -> str:
    return _and(_irreducible(p,tag+'irreducible'),_dvd(p,z,tag+'divisor'))


def _descent_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    result='exists p. '+_irreducible_divisor('p','z','prime_divisor_result')
    return (
        spec(
            'gaussian_irreducible_divisor_bounded_norm',f"forall k z N. ({_le('N','k','prime_divisor_bound')}) -> ({_norm('z','N','prime_divisor_norm')}) -> ~(z=0) -> ~({_unit('z','prime_divisor_nonunit')}) -> ({result})",
            ('le_zero','gaussian_norm_value_transport','gaussian_norm_zero_implies_code_zero','gaussian_irreducible_or_strict_nonunit_factorization','gaussian_divides_reflexive','gaussian_norm_input_valid','le_of_succ_le_succ','lt_of_lt_of_le','gaussian_search_divisor_of_nonzero_nonzero','gaussian_divides_transitive'),
            ('induction k',)+_intro('z','N','hb','hn','hz','hu')+('exfalso','apply hz')+_call('gaussian_norm_zero_implies_code_zero','z')
            +_call('gaussian_norm_value_transport','z','N','0')+_call('le_zero','N')+('exact hb','exact hn')
            +_intro('z','N','hb','hn','hz','hu')+(f"have hs : ({_irreducible_or_split('z','N','prime_divisor_descent')})",)
            +_call('gaussian_irreducible_or_strict_nonunit_factorization','z','N')+('exact hn','exact hz','exact hu','cases hs')+_exists('z')+('split','exact hs_left')
            +_call('gaussian_divides_reflexive','z')+_call('gaussian_norm_input_valid','z','N')+('exact hn',)+_cases('hs_right',4)+_parts('hs_right'+'_witness'*4,7)
            +(f"have hrec : exists p. ({_irreducible_divisor('p','x','prime_divisor_recursive')})",)+_call('IH','x','x2')
            +_call('le_of_succ_le_succ','x2','k')+_call('lt_of_lt_of_le','x2','N','S k')+(f"exact {_part('hs_right'+'_witness'*4,7,5)}",'exact hb',f"exact {_part('hs_right'+'_witness'*4,7,1)}",'intro hzero')
            +_call('gaussian_search_divisor_of_nonzero_nonzero','x','z')+_exists('x1')+(f"exact {_part('hs_right'+'_witness'*4,7,0)}",'exact hz','exact hzero',f"exact {_part('hs_right'+'_witness'*4,7,3)}",'cases hrec','cases hrec_witness')
            +_exists('x4')+('split','exact hrec_witness_left')+_call('gaussian_divides_transitive','x4','x','z')+('exact hrec_witness_right',)+_exists('x1')+(f"exact {_part('hs_right'+'_witness'*4,7,0)}",),
            'Ordinary bounded-norm induction constructs an irreducible divisor of every nonzero Gaussian nonunit, using the actual finite factor search at each descent.',
        ),
        spec(
            'gaussian_irreducible_divisor_exists',f"forall z. ({_valid('z','prime_divisor_domain')}) -> ~(z=0) -> ~({_unit('z','prime_divisor_not_unit')}) -> ({result})",
            ('gaussian_norm_exists','gaussian_irreducible_divisor_bounded_norm','le_refl'),
            _intro('z','hv','hz','hu')+(f"have hn : exists N. ({_norm('z','N','prime_divisor_actual_norm')})",)+_call('gaussian_norm_exists','z')+('exact hv','cases hn')
            +_call('gaussian_irreducible_divisor_bounded_norm','x','z','x')+_call('le_refl','x')+('exact hn_witness','exact hz','exact hu'),
            'Every actual nonzero Gaussian nonunit has an actually witnessed irreducible Gaussian divisor, with no supplied search oracle.',
        ),
        spec(
            'gaussian_nonunit_divisor_strict_quotient',f"forall d z D N. ({_dvd('d','z','quotient_divisor')}) -> ({_norm('d','D','quotient_divisor_norm')}) -> ({_norm('z','N','quotient_total_norm')}) -> ~(z=0) -> ~({_unit('d','quotient_nonunit')}) -> exists q Q. "
            +_and(_mul('d','q','z','quotient_product'),_norm('q','Q','quotient_norm'),_lt('Q','N','quotient_strict'),'~(q=0)'),
            ('gaussian_divisor_norm_factor','gaussian_norm_nonzero','factor_nonzero_left','factor_nonzero_right','gaussian_search_nonunit_norm_two','succ_le_mul_of_two_le_right','mul_comm','gaussian_code_zero_implies_norm_zero'),
            _intro('d','z','D','N','hd','hD','hN','hz','hu')+(f"have hf : exists q Q. {_and(_mul('d','q','z','quotient_constructed_product'),_norm('q','Q','quotient_constructed_norm'),'N=D*Q')}",)
            +_call('gaussian_divisor_norm_factor','d','z','D','N')+('exact hd','exact hD','exact hN')+_cases('hf',2)+_parts('hf_witness_witness',3)
            +('have hpositive : ~(N=0)','intro hzero')+_call('gaussian_norm_nonzero','z','N')+('exact hN','exact hz','exact hzero','have hDpositive : ~(D=0)','intro hzero')
            +_call('factor_nonzero_left','N','D','x1')+('exact hpositive','exact hf_witness_witness_right_right','exact hzero','have hQpositive : ~(x1=0)','intro hzero')
            +_call('factor_nonzero_right','N','D','x1')+('exact hpositive','exact hf_witness_witness_right_right','exact hzero')+_exists('x','x1')+('split','exact hf_witness_witness_left','split','exact hf_witness_witness_right_left','split',
              'have heq : N=x1*D','trans D*x1','exact hf_witness_witness_right_right','apply mul_comm','rewrite heq')
            +_call('succ_le_mul_of_two_le_right','x1','D')+('exact hQpositive',)+_call('gaussian_search_nonunit_norm_two','d','D')+('exact hD','exact hDpositive','exact hu','intro hqzero','apply hQpositive')
            +_call('gaussian_code_zero_implies_norm_zero','x','x1')+('exact hf_witness_witness_right_left','exact hqzero'),
            'Dividing a nonzero Gaussian value by an actual nonunit strictly decreases the quotient norm, even when the quotient itself is a unit.',
        ),
        spec(
            'gaussian_irreducible_factor_reduction',f"forall z N. ({_norm('z','N','reduction_actual_norm')}) -> ~(z=0) -> ~({_unit('z','reduction_nonunit')}) -> exists p q Q. "
            +_and(_irreducible('p','reduction_irreducible'),_mul('p','q','z','reduction_product'),_norm('q','Q','reduction_quotient_norm'),_lt('Q','N','reduction_quotient_strict'),'~(q=0)'),
            ('gaussian_irreducible_divisor_exists','gaussian_norm_input_valid','gaussian_norm_exists','gaussian_nonunit_divisor_strict_quotient'),
            _intro('z','N','hn','hz','hu')+(f"have hp : exists p. ({_irreducible_divisor('p','z','reduction_divisor')})",)
            +_call('gaussian_irreducible_divisor_exists','z')+_call('gaussian_norm_input_valid','z','N')+('exact hn','exact hz','exact hu','cases hp','cases hp_witness')+_parts('hp_witness_left',4)
            +(f"have hP : exists P. ({_norm('x','P','reduction_divisor_norm')})",)+_call('gaussian_norm_exists','x')+(f"exact {_part('hp_witness_left',4,0)}",'cases hP',
              f"have hq : exists q Q. {_and(_mul('x','q','z','reduction_constructed_product'),_norm('q','Q','reduction_constructed_norm'),_lt('Q','N','reduction_constructed_strict'),'~(q=0)')}")
            +_call('gaussian_nonunit_divisor_strict_quotient','x','z','x1','N')+('exact hp_witness_right','exact hP_witness','exact hn','exact hz',f"exact {_part('hp_witness_left',4,2)}")+_cases('hq',2)+_parts('hq_witness_witness',4)
            +_exists('x','x2','x3')+('split','exact hp_witness_left','split','exact hq_witness_witness_left','split','exact hq_witness_witness_right_left','split','exact hq_witness_witness_right_right_left','exact hq_witness_witness_right_right_right'),
            'Construct an actual irreducible factor and a nonzero, strictly norm-smaller quotient for every nonzero Gaussian nonunit; this is the finite-factorization recursion step.',
        ),
    )


def make_gaussian_factor_search_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _coordinate_rows(spec)+_decision_rows(spec)+_complete_search_rows(spec)+_irreducibility_rows(spec)+_descent_rows(spec)
