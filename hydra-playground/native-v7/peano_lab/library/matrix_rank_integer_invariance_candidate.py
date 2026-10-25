"""Actual rectangular rank is independent of integer pair representatives."""

from __future__ import annotations

from typing import Any, Callable

from .matrix_recursive_determinant_candidate import (
    _and, _apply, _at, _cases, _exists, _intro, _le, _lt, _part, _parts, _rewrite_all,
)
from .matrix_rank_selected_minors_candidate import _point, _selected_prefix, _selected, _selected_det, _nonzero_minor
from .matrix_rank_finite_coding_candidate import _selector
from .matrix_rank_certificate_candidate import _rank, _all_zero
from .matrix_integer_invariance_candidate import _rect_equal


def make_matrix_rank_integer_invariance_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    first = ('ab','ac','bb','bc')
    second = ('eb','ec','fb','fc')
    parents = (*first,*second)
    selectors = ('rb','rc','cb','cc')
    out_a = ('ub','uc','vb','vc')
    out_b = ('Ub','Uc','Vb','Vc')
    natural = ('b','c','w',*selectors,'q')
    first_point = 'hap_witness_witness_witness_witness'
    source_minor = 'hminor_witness_witness_witness_witness'
    return (
        spec(
            'matrix_integer_rectangular_index_bound',
            f"forall r w i j. ({_lt('i','r','rect_row')}) -> ({_lt('j','w','rect_column')}) -> ({_lt('i * w + j','r * w','rect_flat')})",
            ('mul_le_mul_right','mul_succ_left','matrix_recursive_lt_add_left','lt_of_lt_of_le'),
            _intro('r','w','i','j','hi','hj')
            +(f"have hrow : {_le('(S i) * w','r * w','rect_row_end')}",)
            +_apply('mul_le_mul_right','S i','r','w')+('exact hi','have heq : (S i) * w = i * w + w','apply mul_succ_left','rewrite heq at hrow')
            +_apply('lt_of_lt_of_le','i * w + j','i * w + w','r * w')+_apply('matrix_recursive_lt_add_left','j','w','i * w')+('exact hj','exact hrow'),
            'Every actual in-range rectangular row and column has flattened index below rows times columns, including vacuous zero boundaries.',
        ),
        spec(
            'matrix_integer_selected_point_at_source',
            f"forall {' '.join(natural)} i r s u v a. ({_point(*natural,'i','a','selected_source_point')}) -> i = q * r + s -> "
            f"({_lt('s','q','selected_source_column')}) -> ({_at('rb','rc','r','u','selected_source_row_code')}) -> "
            f"({_at('cb','cc','s','v','selected_source_col_code')}) -> ({_at('b','c','u * w + v','a','selected_source_value')})",
            ('division_remainder_unique','beta_at_unique'),
            _intro(*natural,'i','r','s','u','v','a','hpoint','hcoordinate','hs','hrow','hcolumn')+_cases('hpoint',4)+_parts('hpoint'+'_witness'*4,5)
            +('have hcoordinates : r = x /\\ s = x1',)+_apply('division_remainder_unique','q','i','r','s','x','x1')
            +('exact hcoordinate','exact hs','exact hpoint_witness_witness_witness_witness_left','exact hpoint_witness_witness_witness_witness_right_left','cases hcoordinates','have hrowvalue : u = x2')
            +_apply('beta_at_unique','rb','rc','r','u','x2')+('exact hrow',)
            +_rewrite_all('hcoordinates_left','r',_at('rb','rc','r','x2','row_source_aligned'))+('exact hpoint_witness_witness_witness_witness_right_right_left','have hcolvalue : v = x3')
            +_apply('beta_at_unique','cb','cc','s','v','x3')+('exact hcolumn',)
            +_rewrite_all('hcoordinates_right','s',_at('cb','cc','s','x3','col_source_aligned'))+('exact hpoint_witness_witness_witness_witness_right_right_right_left',)
            +_rewrite_all('hrowvalue','u',_at('b','c','u * w + v','a','source_row_aligned'))
            +_rewrite_all('hcolvalue','v',_at('b','c','x2 * w + v','a','source_col_aligned'))+('exact hpoint_witness_witness_witness_witness_right_right_right_right',),
            'Every actual selected cell is its genuine source entry for any matching quotient coordinates and selector values; all coordinate and selector equalities are proved.',
        ),
        spec(
            'matrix_integer_selected_point_balance',
            f"forall {' '.join(parents)} r w q {' '.join(selectors)} i a b c d. ({_rect_equal(*parents,'r','w','selected_parent_equal')}) -> "
            f"({_selector('rb','rc','q','r','selected_rows')}) -> ({_selector('cb','cc','q','w','selected_columns')}) -> ({_lt('i','q * q','selected_flat_bound')}) -> "
            f"({_point('ab','ac','w',*selectors,'q','i','a','selected_point_ap')}) -> ({_point('bb','bc','w',*selectors,'q','i','b','selected_point_an')}) -> "
            f"({_point('eb','ec','w',*selectors,'q','i','c','selected_point_bp')}) -> ({_point('fb','fc','w',*selectors,'q','i','d','selected_point_bn')}) -> a + d = c + b",
            ('matrix_recursive_quotient_row_bound','matrix_rank_bounded_prefix_value','matrix_integer_rectangular_index_bound','matrix_integer_selected_point_at_source'),
            _intro(*parents,'r','w','q',*selectors,'i','a','b','c','d','hequal','hrows','hcolumns','hi','hap','han','hbp','hbn')
            +('cases hrows','cases hcolumns')+_cases('hap',4)+_parts(first_point,5)
            +(f"have hselectedrow : {_lt('x','q','selected_row_coordinate')}",)
            +_apply('matrix_recursive_quotient_row_bound','q','i','x','x1')+(f'exact {_part(first_point,5,0)}','exact hi')
            +(f"have hrow : {_lt('x2','r','source_row_coordinate')}",)
            +_apply('matrix_rank_bounded_prefix_value','rb','rc','q','r','x','x2')+('exact hrows_left','exact hselectedrow',f'exact {_part(first_point,5,2)}')
            +(f"have hcolumn : {_lt('x3','w','source_column_coordinate')}",)
            +_apply('matrix_rank_bounded_prefix_value','cb','cc','q','w','x1','x3')+('exact hcolumns_left',f'exact {_part(first_point,5,1)}',f'exact {_part(first_point,5,3)}')
            +_apply('hequal','x2 * w + x3','a','b','c','d')
            +_apply('matrix_integer_rectangular_index_bound','r','w','x2','x3')+('exact hrow','exact hcolumn',f'exact {_part(first_point,5,4)}')
            +tuple(command for code,scale,value,hypothesis in (('bb','bc','b','han'),('eb','ec','c','hbp'),('fb','fc','d','hbn')) for command in (
                *_apply('matrix_integer_selected_point_at_source',code,scale,'w',*selectors,'q','i','x','x1','x2','x3',value),
                f'exact {hypothesis}',f'exact {_part(first_point,5,0)}',f'exact {_part(first_point,5,1)}',f'exact {_part(first_point,5,2)}',f'exact {_part(first_point,5,3)}',
            )),
            'Actual selected cells of integer-equal rectangular matrices are integer-equal at one proved in-range shared parent index.',
        ),
        spec(
            'matrix_integer_selected_prefix_point_at',
            f"forall {' '.join(natural)} u v i a. ({_selected_prefix(*natural,'u','v','q * q','selected_prefix')}) -> "
            f"({_lt('i','q * q','selected_index')}) -> ({_at('u','v','i','a','selected_value')}) -> ({_point(*natural,'i','a','actual_selected_point')})",
            ('beta_at_unique',),
            _intro(*natural,'u','v','i','a','hprefix','hi','ha')
            +(f"have hentry : exists z. {_and(_point(*natural,'i','z','selected_decoded_point'),_at('u','v','i','z','selected_decoded_value'))}",)
            +_apply('hprefix','i')+('exact hi','cases hentry','cases hentry_witness','have hvalue : a = x')
            +_apply('beta_at_unique','u','v','i','a','x')+('exact ha','exact hentry_witness_right')
            +_rewrite_all('hvalue','a',_point(*natural,'i','a','point_output_aligned'))+('exact hentry_witness_left',),
            'Every output decoded from a complete selected-submatrix prefix has its actual source-point certificate, independently of the existential value witness used by the prefix.',
        ),
        spec(
            'matrix_integer_signed_selected_balance',
            f"forall {' '.join(parents)} r w q {' '.join((*selectors,*out_a,*out_b))}. ({_rect_equal(*parents,'r','w','selected_matrix_parents')}) -> "
            f"({_selector('rb','rc','q','r','selected_matrix_rows')}) -> ({_selector('cb','cc','q','w','selected_matrix_columns')}) -> "
            f"({_selected(*first,'w',*selectors,'q',*out_a,'first_selected_matrix')}) -> ({_selected(*second,'w',*selectors,'q',*out_b,'second_selected_matrix')}) -> "
            f"({_rect_equal(*out_a,*out_b,'q','q','selected_matrices_equal')})",
            ('matrix_integer_selected_point_balance','matrix_integer_selected_prefix_point_at'),
            _intro(*parents,'r','w','q',*selectors,*out_a,*out_b,'hequal','hrows','hcolumns','hfirst','hsecond')+('cases hfirst','cases hsecond')
            +_intro('i','a','b','c','d','hi','ha','hb','hc','hd')
            +_apply('matrix_integer_selected_point_balance',*parents,'r','w','q',*selectors,'i','a','b','c','d')+('exact hequal','exact hrows','exact hcolumns','exact hi')
            +tuple(command for code,scale,output,outputscale,value,hprefix,hvalue in (
                ('ab','ac','ub','uc','a','hfirst_left','ha'),('bb','bc','vb','vc','b','hfirst_right','hb'),
                ('eb','ec','Ub','Uc','c','hsecond_left','hc'),('fb','fc','Vb','Vc','d','hsecond_right','hd'),
            ) for command in (
                *_apply('matrix_integer_selected_prefix_point_at',code,scale,'w',*selectors,'q',output,outputscale,'i',value),
                f'exact {hprefix}','exact hi',f'exact {hvalue}',
            )),
            'Every pair of genuinely selected submatrices from integer-equal rectangular parents has equal represented integer entries, despite arbitrary component recodings.',
        ),
        spec(
            'matrix_integer_selected_determinant_balance',
            f"forall {' '.join(parents)} r w q {' '.join(selectors)} p n P N. ({_rect_equal(*parents,'r','w','selected_determinant_parents')}) -> "
            f"({_selector('rb','rc','q','r','selected_determinant_rows')}) -> ({_selector('cb','cc','q','w','selected_determinant_columns')}) -> "
            f"({_selected_det(*first,'w',*selectors,'q','p','n','first_selected_determinant')}) -> "
            f"({_selected_det(*second,'w',*selectors,'q','P','N','second_selected_determinant')}) -> p + N = P + n",
            ('matrix_integer_signed_selected_balance','signed_recursive_determinant_integer_invariant'),
            _intro(*parents,'r','w','q',*selectors,'p','n','P','N','hequal','hrows','hcolumns','hfirst','hsecond')
            +_cases('hfirst',4)+('cases hfirst_witness_witness_witness_witness',)+_cases('hsecond',4)+('cases hsecond_witness_witness_witness_witness',)
            +_apply('signed_recursive_determinant_integer_invariant','q','x','x1','x2','x3','x4','x5','x6','x7','p','n','P','N')
            +_apply('matrix_integer_signed_selected_balance',*parents,'r','w','q',*selectors,'x','x1','x2','x3','x4','x5','x6','x7')
            +('exact hequal','exact hrows','exact hcolumns','exact hfirst_witness_witness_witness_witness_left','exact hsecond_witness_witness_witness_witness_left',
              'exact hfirst_witness_witness_witness_witness_right','exact hsecond_witness_witness_witness_witness_right'),
            'Every actual selected-minor determinant represents the same integer in any entrywise integer-equal rectangular parent representation.',
        ),
        spec(
            'matrix_integer_nonzero_pair_transport',
            'forall p n P N. p + N = P + n -> ~(p = n) -> ~(P = N)',
            ('add_right_cancel','add_comm'),
            _intro('p','n','P','N','hbalance','hnonzero','hzero')+('apply hnonzero',)
            +_apply('add_right_cancel','p','n','N')+('trans P + n','exact hbalance','rewrite hzero','apply add_comm'),
            'Nonzeroness of the represented integer is preserved by cross-sum equality, using actual additive cancellation.',
        ),
        spec(
            'matrix_integer_nonzero_minor_transport',
            f"forall {' '.join(parents)} r w q. ({_rect_equal(*parents,'r','w','minor_parent_equality')}) -> "
            f"({_nonzero_minor(*first,'r','w','q','first_nonzero_minor')}) -> ({_nonzero_minor(*second,'r','w','q','second_nonzero_minor')})",
            ('matrix_rank_selected_determinant_exists','matrix_integer_selected_determinant_balance','matrix_integer_nonzero_pair_transport'),
            _intro(*parents,'r','w','q','hequal','hminor')+_cases('hminor',4)+_parts(source_minor,3)
            +_cases(source_minor+'_right_right',2)+(f'cases {source_minor}_right_right_witness_witness',)
            +(f"have hvalue : exists P N. {_selected_det(*second,'w','x','x1','x2','x3','q','P','N','transported_minor_value')}",)
            +_apply('matrix_rank_selected_determinant_exists',*second,'w','x','x1','x2','x3','q')+_cases('hvalue',2)
            +('have hbalance : x4 + x7 = x6 + x5',)
            +_apply('matrix_integer_selected_determinant_balance',*parents,'r','w','q','x','x1','x2','x3','x4','x5','x6','x7')
            +('exact hequal',f'exact {source_minor}_left',f'exact {source_minor}_right_left',f'exact {source_minor}_right_right_witness_witness_left','exact hvalue_witness_witness')
            +_exists('x','x1','x2','x3')+('split',f'exact {source_minor}_left','split',f'exact {source_minor}_right_left')
            +_exists('x6','x7')+('split','exact hvalue_witness_witness','intro hzero')
            +_apply('matrix_integer_nonzero_pair_transport','x4','x5','x6','x7')+('exact hbalance',f'exact {source_minor}_right_right_witness_witness_right','exact hzero'),
            'Every genuine nonzero minor is transported using the same actual selectors and a newly constructed target determinant; cross-sum invariance proves that its represented value stays nonzero.',
        ),
        spec(
            'matrix_integer_all_minors_zero_transport',
            f"forall {' '.join(parents)} r w q. ({_rect_equal(*parents,'r','w','zero_parent_equality')}) -> "
            f"({_all_zero(*first,'r','w','q','first_zero_minors')}) -> ({_all_zero(*second,'r','w','q','second_zero_minors')})",
            ('matrix_rank_all_minors_zero_from_absence','matrix_rank_absence_from_all_minors_zero','matrix_integer_vector_equality_symmetric','matrix_integer_nonzero_minor_transport'),
            _intro(*parents,'r','w','q','hequal','hzero')+_apply('matrix_rank_all_minors_zero_from_absence',*second,'r','w','q')
            +('intro hminor',)+_apply('matrix_rank_absence_from_all_minors_zero',*first,'r','w','q')+('exact hzero',)
            +_apply('matrix_integer_nonzero_minor_transport',*second,*first,'r','w','q')
            +_apply('matrix_integer_vector_equality_symmetric',*parents,'r * w')+('exact hequal','exact hminor'),
            'Universal actual-minor vanishing is independent of the chosen signed-integer parent representation.',
        ),
        spec(
            'rectangular_matrix_rank_integer_transport',
            f"forall {' '.join(parents)} r w rank. ({_rect_equal(*parents,'r','w','rank_parent_equality')}) -> "
            f"({_rank(*first,'r','w','rank','first_integer_rank')}) -> ({_rank(*second,'r','w','rank','second_integer_rank')})",
            ('matrix_integer_nonzero_minor_transport','matrix_integer_all_minors_zero_transport'),
            _intro(*parents,'r','w','rank','hequal','hrank')+_parts('hrank',4)+('split','exact hrank_left','split','exact hrank_right_left','split')
            +_apply('matrix_integer_nonzero_minor_transport',*parents,'r','w','rank')+('exact hequal','exact hrank_right_right_left')
            +_intro('q','hq')+_apply('matrix_integer_all_minors_zero_transport',*parents,'r','w','q')+('exact hequal',)
            +_apply('hrank_right_right_right','q')+('exact hq',),
            'The complete actual rank certificate—including nonzero witness and every higher zero minor—transports across arbitrary entrywise equal integer representations.',
        ),
        spec(
            'rectangular_matrix_rank_integer_invariant',
            f"forall {' '.join(parents)} r w rank other. ({_rect_equal(*parents,'r','w','rank_integer_equality')}) -> "
            f"({_rank(*first,'r','w','rank','rank_integer_first')}) -> ({_rank(*second,'r','w','other','rank_integer_second')}) -> rank = other",
            ('rectangular_matrix_rank_integer_transport','rectangular_matrix_rank_functional'),
            _intro(*parents,'r','w','rank','other','hequal','hfirst','hsecond')
            +_apply('rectangular_matrix_rank_functional',*second,'r','w','rank','other')
            +_apply('rectangular_matrix_rank_integer_transport',*parents,'r','w','rank')+('exact hequal','exact hfirst','exact hsecond'),
            'The genuine finite rectangular rank value is an invariant of the integer matrix itself, not of any positive/negative beta representatives or determinant histories.',
        ),
    )


__all__ = ['make_matrix_rank_integer_invariance_candidate_theorems']
