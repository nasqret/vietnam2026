"""Positive absolute-determinant data and the full-rank square interface.

This encodes the blueprint's nondegenerate integral square-matrix data.
It does not prove a lattice index, geometric covolume, independent basis,
Hermite/Smith normal form, or LLL theorem.
"""

from __future__ import annotations

from typing import Any, Callable

from .matrix_recursive_determinant_candidate import (
    _and, _apply, _at, _cases, _det, _exists, _intro, _le, _lt, _names, _part, _parts, _rewrite_all, _safe,
)
from .matrix_integer_invariance_candidate import _arguments, _rect_equal
from .matrix_rank_finite_coding_candidate import _selector
from .matrix_rank_selected_minors_candidate import _point, _selected_prefix, _selected, _nonzero_minor
from .matrix_rank_certificate_candidate import _rank


def _absolute(p: str, n: str, D: str) -> str:
    return f'(({p}) = ({n}) + ({D})) \\/ (({n}) = ({p}) + ({D}))'


def _absolute_det(ab: str, ac: str, bb: str, bc: str, d: str, D: str, tag: str) -> str:
    p,n = _names(tag,'p','n')
    return f'exists {p} {n}. '+_and(_det(ab,ac,bb,bc,d,p,n,tag+'evaluation'),_absolute(p,n,D))


def absolute_recursive_determinant_relation(ab: str, ac: str, bb: str, bc: str, d: str, D: str, *, tag: str) -> str:
    """D is the actual natural absolute value of the recursively evaluated determinant."""
    return _absolute_det(*_arguments(ab,ac,bb,bc,d,D),_safe(tag))


def _data(ab: str, ac: str, bb: str, bc: str, d: str, D: str, tag: str) -> str:
    return _and(f'~({d} = 0)',f'~({D} = 0)',_absolute_det(ab,ac,bb,bc,d,D,tag+'absolute'))


def positive_determinant_matrix_data_relation(ab: str, ac: str, bb: str, bc: str, d: str, D: str, *, tag: str) -> str:
    """Positive-dimensional integral square data with actual positive absolute determinant."""
    return _data(*_arguments(ab,ac,bb,bc,d,D),_safe(tag))


def _identity(b: str, c: str, length: str, tag: str) -> str:
    i, = _names(tag,'i')
    return f'forall {i}. ({_lt(i,length,tag+"bound")}) -> ({_at(b,c,i,i,tag+"entry")})'


def identity_matrix_selector_relation(b: str, c: str, length: str, *, tag: str) -> str:
    """The actual beta selector 0,1,...,length-1, not an assumed permutation."""
    return _identity(*_arguments(b,c,length),_safe(tag))


def make_matrix_lattice_data_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    matrix = ('ab','ac','bb','bc')
    other = ('eb','ec','fb','fc')
    absolute_unique = _and(_absolute_det(*matrix,'d','D','unique_absolute'),f"forall E. ({_absolute_det(*matrix,'d','E','other_absolute')}) -> E = D")
    data_unique = _and(_data(*matrix,'d','D','unique_positive_data'),f"forall E. ({_data(*matrix,'d','E','other_positive_data')}) -> E = D")
    return (
        spec(
            'matrix_lattice_absolute_difference_exists',
            f"forall p n. exists D. ({_absolute('p','n','D')})",
            ('le_or_lt','lt_to_le','add_comm'),
            _intro('p','n')+('specialize le_or_lt p','specialize le_or_lt n','cases le_or_lt','cases le_or_lt_left','exists x','right','trans x + p','symm','exact le_or_lt_left_witness','apply add_comm')
            +(f"have hreverse : {_le('n','p','absolute_reverse')}",)+_apply('lt_to_le','n','p')+('exact le_or_lt_right','cases hreverse','exists x','left','trans x + n','symm','exact hreverse_witness','apply add_comm'),
            'Construct an actual natural absolute difference of every signed pair using constructive natural order.',
        ),
        spec(
            'matrix_lattice_opposite_gaps_zero',
            'forall a b D E. a = b + D -> b = a + E -> D = 0 /\\ E = 0',
            ('add_left_cancel','add_assoc','add_eq_zero_left','add_eq_zero_right'),
            _intro('a','b','D','E','hfirst','hsecond')+('have hsum : D + E = 0',)
            +_apply('add_left_cancel','b','D + E','0')
            +('trans (b + D) + E','symm','apply add_assoc','trans a + E','congr','symm','exact hfirst','refl','trans b','symm','exact hsecond','symm','apply PA3','split')
            +_apply('add_eq_zero_left','D','E')+('exact hsum',)+_apply('add_eq_zero_right','D','E')+('exact hsum',),
            'Oppositely oriented nonnegative gaps can coexist only when both are zero, by actual cancellative natural arithmetic.',
        ),
        spec(
            'matrix_lattice_absolute_difference_functional',
            f"forall p n D E. ({_absolute('p','n','D')}) -> ({_absolute('p','n','E')}) -> D = E",
            ('add_left_cancel','matrix_lattice_opposite_gaps_zero'),
            _intro('p','n','D','E','hfirst','hsecond')+('cases hfirst','cases hsecond')
            +_apply('add_left_cancel','n','D','E')+('trans p','symm','exact hfirst_left','exact hsecond_left')
            +('have hzeros : D = 0 /\\ E = 0',)+_apply('matrix_lattice_opposite_gaps_zero','p','n','D','E')+('exact hfirst_left','exact hsecond_right','cases hzeros','trans 0','exact hzeros_left','symm','exact hzeros_right')
            +('cases hsecond','have hzeros : D = 0 /\\ E = 0')+_apply('matrix_lattice_opposite_gaps_zero','n','p','D','E')+('exact hfirst_right','exact hsecond_left','cases hzeros','trans 0','exact hzeros_left','symm','exact hzeros_right')
            +_apply('add_left_cancel','p','D','E')+('trans n','symm','exact hfirst_right','exact hsecond_right'),
            'The actual natural absolute value of a signed pair is unique, including the zero and opposite-orientation boundaries.',
        ),
        spec(
            'matrix_lattice_absolute_nonzero_of_pair',
            f"forall p n D. ~(p = n) -> ({_absolute('p','n','D')}) -> ~(D = 0)",
            (),
            _intro('p','n','D','hpair','habsolute','hzero')+('apply hpair','cases habsolute','trans n + D','exact habsolute_left','rewrite hzero','apply PA3','symm','trans p + D','exact habsolute_right','rewrite hzero','apply PA3'),
            'A nonzero represented integer has a nonzero actual absolute difference, in either sign orientation.',
        ),
        spec(
            'matrix_lattice_pair_nonzero_of_absolute',
            f"forall p n D. ~(D = 0) -> ({_absolute('p','n','D')}) -> ~(p = n)",
            ('add_left_cancel',),
            _intro('p','n','D','habsolute','hgap','hpair')+('apply habsolute','cases hgap')
            +_apply('add_left_cancel','n','D','0')+('trans p','symm','exact hgap_left','trans n','exact hpair','symm','apply PA3')
            +_apply('add_left_cancel','p','D','0')+('trans n','symm','exact hgap_right','trans p','symm','exact hpair','symm','apply PA3'),
            'A positive actual absolute difference rules out equal signed components, without assuming a canonical representative.',
        ),
        spec(
            'matrix_lattice_positive_gap_integer_transport',
            'forall p n P N D. p + N = P + n -> P = N + D -> p = n + D',
            ('add_right_cancel','four_square_euler_add_swap_last','add_comm'),
            _intro('p','n','P','N','D','hbalance','hgap')+_apply('add_right_cancel','p','n + D','N')
            +('trans P + n','exact hbalance','rewrite hgap','trans (N + n) + D','apply four_square_euler_add_swap_last','trans (n + N) + D','congr','apply add_comm','refl','apply four_square_euler_add_swap_last'),
            'A genuine nonnegative signed gap transports across integer cross-sum equality by additive cancellation.',
        ),
        spec(
            'matrix_lattice_absolute_difference_integer_transport',
            f"forall p n P N D. p + N = P + n -> ({_absolute('p','n','D')}) -> ({_absolute('P','N','D')})",
            ('matrix_lattice_positive_gap_integer_transport','matrix_integer_pair_negation_balance','eq_symm'),
            _intro('p','n','P','N','D','hbalance','habsolute')+('cases habsolute','left')
            +_apply('matrix_lattice_positive_gap_integer_transport','P','N','p','n','D')
            +_apply('eq_symm','p + N','P + n')+('exact hbalance','exact habsolute_left','right')
            +_apply('matrix_lattice_positive_gap_integer_transport','N','P','n','p','D')
            +_apply('eq_symm','n + P','N + p')+_apply('matrix_integer_pair_negation_balance','p','n','P','N')+('exact hbalance','exact habsolute_right'),
            'Natural absolute value is an invariant of the represented integer, not of the chosen positive and negative components.',
        ),
        spec(
            'absolute_recursive_determinant_exists',
            f"forall {' '.join(matrix)} d. exists D. ({_absolute_det(*matrix,'d','D','absolute_det_exists')})",
            ('signed_recursive_determinant_exists','matrix_lattice_absolute_difference_exists'),
            _intro(*matrix,'d')
            +(f"have hvalue : exists p n. ({_det(*matrix,'d','p','n','absolute_actual_value')})",)
            +_apply('signed_recursive_determinant_exists',*matrix,'d')+_cases('hvalue',2)
            +(f"have habsolute : exists D. ({_absolute('x','x1','D')})",)
            +_apply('matrix_lattice_absolute_difference_exists','x','x1')+('cases habsolute',)+_exists('x2','x','x1')+('split','exact hvalue_witness_witness','exact habsolute_witness'),
            'Every square matrix in every natural dimension has an actual natural absolute determinant obtained from its genuine recursive evaluation.',
        ),
        spec(
            'absolute_recursive_determinant_functional',
            f"forall {' '.join(matrix)} d D E. ({_absolute_det(*matrix,'d','D','absolute_first')}) -> ({_absolute_det(*matrix,'d','E','absolute_second')}) -> D = E",
            ('signed_recursive_determinant_functional','matrix_lattice_absolute_difference_functional'),
            _intro(*matrix,'d','D','E','hfirst','hsecond')+_cases('hfirst',2)+('cases hfirst_witness_witness',)+_cases('hsecond',2)+('cases hsecond_witness_witness','have hvalues : x = x2 /\\ x1 = x3')
            +_apply('signed_recursive_determinant_functional',*matrix,'d','x','x1','x2','x3')+('exact hfirst_witness_witness_left','exact hsecond_witness_witness_left','cases hvalues')
            +_apply('matrix_lattice_absolute_difference_functional','x2','x3','D','E')
            +tuple(command+' at hfirst_witness_witness_right' for command in _rewrite_all('hvalues_left','x',_absolute('x','x1','D')))
            +tuple(command+' at hfirst_witness_witness_right' for command in _rewrite_all('hvalues_right','x1',_absolute('x2','x1','D')))
            +('exact hfirst_witness_witness_right','exact hsecond_witness_witness_right'),
            'The actual absolute determinant is unique across all recursive evaluation histories and sign orientations.',
        ),
        spec(
            'absolute_recursive_determinant_integer_transport',
            f"forall {' '.join((*matrix,*other))} d D. ({_rect_equal(*matrix,*other,'d','d','absolute_parent_equality')}) -> "
            f"({_absolute_det(*matrix,'d','D','absolute_source')}) -> ({_absolute_det(*other,'d','D','absolute_target')})",
            ('signed_recursive_determinant_exists','signed_recursive_determinant_integer_invariant','matrix_lattice_absolute_difference_integer_transport'),
            _intro(*matrix,*other,'d','D','hequal','hfirst')+_cases('hfirst',2)+('cases hfirst_witness_witness',)
            +(f"have hvalue : exists p n. ({_det(*other,'d','p','n','absolute_other_value')})",)
            +_apply('signed_recursive_determinant_exists',*other,'d')+_cases('hvalue',2)
            +_exists('x2','x3')+('split','exact hvalue_witness_witness')
            +_apply('matrix_lattice_absolute_difference_integer_transport','x','x1','x2','x3','D')
            +_apply('signed_recursive_determinant_integer_invariant','d',*matrix,*other,'x','x1','x2','x3')
            +('exact hequal','exact hfirst_witness_witness_left','exact hvalue_witness_witness','exact hfirst_witness_witness_right'),
            'The actual absolute determinant is invariant under arbitrary entrywise equal integer matrix representations.',
        ),
        spec(
            'positive_determinant_matrix_data_from_nonzero',
            f"forall {' '.join(matrix)} d p n. ~(d = 0) -> ({_det(*matrix,'d','p','n','nondegenerate_value')}) -> ~(p = n) -> "
            f"exists D. ({_data(*matrix,'d','D','nondegenerate_data')})",
            ('matrix_lattice_absolute_difference_exists','matrix_lattice_absolute_nonzero_of_pair'),
            _intro(*matrix,'d','p','n','hd','hdet','hnonzero')
            +(f"have habsolute : exists D. ({_absolute('p','n','D')})",)
            +_apply('matrix_lattice_absolute_difference_exists','p','n')+('cases habsolute','exists x','split','exact hd','split','intro hzero')
            +_apply('matrix_lattice_absolute_nonzero_of_pair','p','n','x')+('exact hnonzero','exact habsolute_witness','exact hzero')
            +_exists('p','n')+('split','exact hdet','exact habsolute_witness'),
            'From a positive-dimensional square matrix with an actually nonzero recursive determinant, construct its genuine positive absolute-determinant data; this is data, not an unproved lattice index or covolume theorem.',
        ),
        spec(
            'positive_determinant_matrix_data_nonzero',
            f"forall {' '.join(matrix)} d D. ({_data(*matrix,'d','D','positive_data')}) -> exists p n. ({_and(_det(*matrix,'d','p','n','positive_actual_det'),'~(p = n)')})",
            ('matrix_lattice_pair_nonzero_of_absolute',),
            _intro(*matrix,'d','D','hdata')+_parts('hdata',3)+_cases('hdata_right_right',2)+('cases hdata_right_right_witness_witness',)
            +_exists('x','x1')+('split','exact hdata_right_right_witness_witness_left','intro hzero')
            +_apply('matrix_lattice_pair_nonzero_of_absolute','x','x1','D')+('exact hdata_right_left','exact hdata_right_right_witness_witness_right','exact hzero'),
            'Nondegenerate square-matrix data contains an actual nonzero full determinant witness, not only a positivity label.',
        ),
        spec(
            'positive_determinant_matrix_data_functional',
            f"forall {' '.join(matrix)} d D E. ({_data(*matrix,'d','D','first_positive_data')}) -> ({_data(*matrix,'d','E','second_positive_data')}) -> D = E",
            ('absolute_recursive_determinant_functional',),
            _intro(*matrix,'d','D','E','hfirst','hsecond')+_parts('hfirst',3)+_parts('hsecond',3)
            +_apply('absolute_recursive_determinant_functional',*matrix,'d','D','E')+('exact hfirst_right_right','exact hsecond_right_right'),
            'The positive absolute determinant in the nondegenerate square-matrix data is uniquely determined by the actual matrix.',
        ),
        spec(
            'positive_determinant_matrix_data_integer_transport',
            f"forall {' '.join((*matrix,*other))} d D. ({_rect_equal(*matrix,*other,'d','d','data_integer_equal')}) -> "
            f"({_data(*matrix,'d','D','data_integer_first')}) -> ({_data(*other,'d','D','data_integer_second')})",
            ('absolute_recursive_determinant_integer_transport',),
            _intro(*matrix,*other,'d','D','hequal','hdata')+_parts('hdata',3)+('split','exact hdata_left','split','exact hdata_right_left')
            +_apply('absolute_recursive_determinant_integer_transport',*matrix,*other,'d','D')+('exact hequal','exact hdata_right_right'),
            'Positive-dimensional absolute-determinant data respects the integer matrix itself, not arbitrary signed beta representatives.',
        ),
        spec(
            'matrix_lattice_identity_selector_exists',
            f"forall d. exists b c. ({_identity('b','c','d','identity_exists')})",
            ('beta_range_exists','zero_add'),
            _intro('d')
            +(f"have hrange : exists b c. forall i. ({_lt('i','d','identity_index')}) -> ({_at('b','c','i','0 + i','identity_range_value')})",)
            +_apply('beta_range_exists','0','d')+_cases('hrange',2)+_exists('x','x1')+_intro('i','hi')
            +(f"have hentry : {_at('x','x1','i','0 + i','identity_entry')}",)
            +_apply('hrange_witness_witness','i')+('exact hi','have hzero : 0 + i = i','apply zero_add','rewrite hzero at hentry','rewrite hzero at hentry','exact hentry'),
            'Construct an actual beta-coded identity selector of every natural length from the checked finite range construction.',
        ),
        spec(
            'matrix_lattice_identity_is_selector',
            f"forall b c d. ({_identity('b','c','d','identity_source')}) -> ({_selector('b','c','d','d','identity_selector')})",
            ('beta_at_unique','eq_trans'),
            _intro('b','c','d','hidentity')+('split',)+_intro('i','hi')+('exists i','split')
            +_apply('hidentity','i')+('exact hi','exact hi')
            +_intro('i','j','a','hi','hj','ha','hb')+_apply('eq_trans','i','a','j')
            +_apply('beta_at_unique','b','c','i','i','a')+_apply('hidentity','i')+('exact hi','exact ha')
            +_apply('beta_at_unique','b','c','j','a','j')+('exact hb',)+_apply('hidentity','j')+('exact hj',),
            'The actual identity selector is in range and genuinely injective, not merely a supplied permutation label.',
        ),
        spec(
            'matrix_lattice_identity_selected_natural',
            f"forall b c d ib ic. ~(d = 0) -> ({_identity('ib','ic','d','natural_identity')}) -> "
            f"({_selected_prefix('b','c','d','ib','ic','ib','ic','d','b','c','d * d','identity_selected_natural')})",
            ('division_remainder_exists','matrix_recursive_quotient_row_bound','beta_at_exists','mul_comm'),
            _intro('b','c','d','ib','ic','hd','hidentity','i','hi')
            +(f"have hcoordinates : exists r s. i = d * r + s /\\ ({_lt('s','d','identity_column')})",)
            +_apply('division_remainder_exists','d','i')+('exact hd',)+_cases('hcoordinates',2)+('cases hcoordinates_witness_witness',)
            +(f"have hrow : {_lt('x','d','identity_row')}",)
            +_apply('matrix_recursive_quotient_row_bound','d','i','x','x1')+('exact hcoordinates_witness_witness_left','exact hi')
            +(f"have hvalue : exists a. {_at('b','c','i','a','identity_parent_value')}",)
            +_apply('beta_at_exists','b','c','i')+('cases hvalue','exists x2','split')
            +_exists('x','x1','x','x1')+('split','exact hcoordinates_witness_witness_left','split','exact hcoordinates_witness_witness_right','split')
            +_apply('hidentity','x')+('exact hrow','split')+_apply('hidentity','x1')+('exact hcoordinates_witness_witness_right',)
            +('have hsource : x * d + x1 = i','trans d * x + x1','congr','apply mul_comm','refl','symm','exact hcoordinates_witness_witness_left','rewrite hsource','rewrite hsource','exact hvalue_witness','exact hvalue_witness'),
            'Selecting every actual row and column with the identity beta prefix yields exactly the original natural matrix code, by genuine row-major index arithmetic.',
        ),
        spec(
            'matrix_lattice_identity_selected_signed',
            f"forall {' '.join(matrix)} d ib ic. ~(d = 0) -> ({_identity('ib','ic','d','signed_identity')}) -> "
            f"({_selected(*matrix,'d','ib','ic','ib','ic','d',*matrix,'identity_selected_signed')})",
            ('matrix_lattice_identity_selected_natural',),
            _intro(*matrix,'d','ib','ic','hd','hidentity')+('split',)
            +_apply('matrix_lattice_identity_selected_natural','ab','ac','d','ib','ic')+('exact hd','exact hidentity')
            +_apply('matrix_lattice_identity_selected_natural','bb','bc','d','ib','ic')+('exact hd','exact hidentity'),
            'The actual identity-selected signed submatrix is the original signed square matrix in both component codes.',
        ),
        spec(
            'matrix_lattice_nonzero_full_determinant_minor',
            f"forall {' '.join(matrix)} d p n. ({_det(*matrix,'d','p','n','full_determinant')}) -> ~(p = n) -> "
            f"({_nonzero_minor(*matrix,'d','d','d','full_nonzero_minor')})",
            ('eq_decidable','matrix_rank_nonzero_minor_empty','matrix_lattice_identity_selector_exists','matrix_lattice_identity_is_selector','matrix_lattice_identity_selected_signed'),
            _intro(*matrix,'d','p','n','hdet','hnonzero')+('specialize eq_decidable d','specialize eq_decidable 0','cases eq_decidable')
            +_rewrite_all('eq_decidable_left','d',_nonzero_minor(*matrix,'d','d','d','full_nonzero_target'))
            +_apply('matrix_rank_nonzero_minor_empty',*matrix,'0','0')
            +(f"have hidentity : exists b c. ({_identity('b','c','d','full_minor_identity')})",)
            +_apply('matrix_lattice_identity_selector_exists','d')+_cases('hidentity',2)
            +_exists('x','x1','x','x1')+('split',)+_apply('matrix_lattice_identity_is_selector','x','x1','d')+('exact hidentity_witness_witness','split')
            +_apply('matrix_lattice_identity_is_selector','x','x1','d')+('exact hidentity_witness_witness',)
            +_exists('p','n')+('split',)+_exists(*matrix)+('split',)
            +_apply('matrix_lattice_identity_selected_signed',*matrix,'d','x','x1')+('exact eq_decidable_right','exact hidentity_witness_witness','exact hdet','exact hnonzero'),
            'A nonzero actual full determinant gives a genuine full-order nonzero minor using proved identity selectors, including the exact zero-dimensional boundary.',
        ),
        spec(
            'square_matrix_full_rank_from_nonzero_determinant',
            f"forall {' '.join(matrix)} d p n. ({_det(*matrix,'d','p','n','nonsingular_determinant')}) -> ~(p = n) -> "
            f"({_rank(*matrix,'d','d','d','nonsingular_rank')})",
            ('le_refl','matrix_lattice_nonzero_full_determinant_minor','matrix_rank_selector_dimension_bound','lt_not_le'),
            _intro(*matrix,'d','p','n','hdet','hnonzero')+('split',)+_apply('le_refl','d')+('split',)+_apply('le_refl','d')+('split',)
            +_apply('matrix_lattice_nonzero_full_determinant_minor',*matrix,'d','p','n')+('exact hdet','exact hnonzero')
            +_intro('q','hq','rb','rc','cb','cc','P','N','hrows','hcolumns','hvalue')+('exfalso',)
            +_apply('lt_not_le','d','q')+('exact hq',)+_apply('matrix_rank_selector_dimension_bound','rb','rc','q','d')+('exact hrows',),
            'A genuinely nonzero full determinant proves the square matrix has full determinantal rank d; identity selectors provide the witness and finite pigeonhole rules out every higher minor.',
        ),
        spec(
            'positive_determinant_matrix_data_full_rank',
            f"forall {' '.join(matrix)} d D. ({_data(*matrix,'d','D','full_rank_data')}) -> ({_rank(*matrix,'d','d','d','data_full_rank')})",
            ('positive_determinant_matrix_data_nonzero','square_matrix_full_rank_from_nonzero_determinant'),
            _intro(*matrix,'d','D','hdata')
            +(f"have hvalue : exists p n. ({_and(_det(*matrix,'d','p','n','data_actual_determinant'),'~(p = n)')})",)
            +_apply('positive_determinant_matrix_data_nonzero',*matrix,'d','D')+('exact hdata',)+_cases('hvalue',2)+('cases hvalue_witness_witness',)
            +_apply('square_matrix_full_rank_from_nonzero_determinant',*matrix,'d','x','x1')+('exact hvalue_witness_witness_left','exact hvalue_witness_witness_right'),
            'The explicit positive absolute-determinant matrix data entails genuine full determinantal rank, without claiming a lattice basis, index, or geometric covolume theorem.',
        ),
        spec(
            'absolute_recursive_determinant_exists_unique',
            f"forall {' '.join(matrix)} d. exists D. ({absolute_unique})",
            ('absolute_recursive_determinant_exists','absolute_recursive_determinant_functional'),
            _intro(*matrix,'d')
            +(f"have hvalue : exists D. ({_absolute_det(*matrix,'d','D','constructed_absolute')})",)
            +_apply('absolute_recursive_determinant_exists',*matrix,'d')+('cases hvalue','exists x','split','exact hvalue_witness')
            +_intro('E','hother')+_apply('absolute_recursive_determinant_functional',*matrix,'d','E','x')+('exact hother','exact hvalue_witness'),
            'Every square matrix has exactly one genuine natural absolute determinant, including zero determinant and dimension zero.',
        ),
        spec(
            'positive_determinant_matrix_data_exists_unique',
            f"forall {' '.join(matrix)} d p n. ~(d = 0) -> ({_det(*matrix,'d','p','n','unique_data_determinant')}) -> ~(p = n) -> exists D. ({data_unique})",
            ('positive_determinant_matrix_data_from_nonzero','positive_determinant_matrix_data_functional'),
            _intro(*matrix,'d','p','n','hd','hdet','hnonzero')
            +(f"have hdata : exists D. ({_data(*matrix,'d','D','constructed_positive_data')})",)
            +_apply('positive_determinant_matrix_data_from_nonzero',*matrix,'d','p','n')+('exact hd','exact hdet','exact hnonzero','cases hdata','exists x','split','exact hdata_witness')
            +_intro('E','hother')+_apply('positive_determinant_matrix_data_functional',*matrix,'d','E','x')+('exact hother','exact hdata_witness'),
            'Construct the unique positive absolute-determinant data of every positive-dimensional square matrix with an actual nonzero full determinant.',
        ),
    )


__all__ = ['absolute_recursive_determinant_relation','positive_determinant_matrix_data_relation','identity_matrix_selector_relation','make_matrix_lattice_data_candidate_theorems']
