"""Signed-quotient invariance of genuine recursive matrix determinants.

The integer represented by (p,n) is compared by p+N=P+n, never by equality
of chosen components. All rows are additive first-order HA proof candidates;
the kernel, historical evidence, and prior determinant/rank rows are unchanged.
"""

from __future__ import annotations

from typing import Any, Callable

from .integer_column_span_candidate import _equal, _natural_add
from .matrix_cofactor_expansion_candidate import _alternating_prefix_terms, _fold_terms, _sum_terms, _term_terms
from .matrix_recursive_determinant_candidate import (
    _and, _apply, _at, _cases, _cofactors, _det, _exists, _intro, _le, _lt,
    _minor, _names, _part, _parts, _rewrite_all, _safe,
)
from .matrix_rank_finite_coding_candidate import _arguments as _rank_arguments
from .matrix_determinant_minors_candidate import _skip_terms
from .matrix_recursive_determinant_extensional_candidate import _cell, _natural_minor, _cofactor_entry


def _arguments(*values: str) -> tuple[str, ...]:
    result = _rank_arguments(*values)
    if any(value.startswith('ics_') for value in result):
        raise ValueError('matrix integer argument captures an integer-vector binder')
    return result


def _rect_equal(ab: str, ac: str, bb: str, bc: str, eb: str, ec: str, fb: str, fc: str, r: str, w: str, tag: str) -> str:
    return _equal(ab,ac,bb,bc,eb,ec,fb,fc,f'({r}) * ({w})',tag)


def integer_matrix_entrywise_equal_relation(ab: str, ac: str, bb: str, bc: str, eb: str, ec: str, fb: str, fc: str, r: str, w: str, *, tag: str) -> str:
    """Every actual signed integer entry agrees, across arbitrary representatives."""
    return _rect_equal(*_arguments(ab,ac,bb,bc,eb,ec,fb,fc,r,w),_safe(tag))


def _product(ap: str, an: str, bp: str, bn: str) -> tuple[str,str]:
    return f'({ap}) * ({bp}) + ({an}) * ({bn})',f'({ap}) * ({bn}) + ({an}) * ({bp})'


def _legacy_transport(p: str, n: str, u: str, v: str, cp: str, cn: str) -> str:
    a,b = _product(p,n,cp,cn)
    c,d = _product(u,v,cp,cn)
    e,f = _product(cp,cn,p,n)
    g,h = _product(cp,cn,u,v)
    return _and(f'({a}) + ({d}) = ({b}) + ({c})',f'({e}) + ({h}) = ({f}) + ({g})')


def _alternating_entry(inputs: tuple[str,...], outputs: tuple[str,...], i: str, values: tuple[str,...], tag: str) -> str:
    ap,an,bp,bn,p,n = values
    return _and(
        *(_at(inputs[2*k],inputs[2*k+1],i,values[k],tag+str(k)) for k in range(4)),
        _at(outputs[0],outputs[1],i,p,tag+'positive'),_at(outputs[2],outputs[3],i,n,tag+'negative'),
        _term_terms(ap,an,bp,bn,i,p,n,tag=tag+'term'),
    )


def _skip(i: str, removed: str, source: str, tag: str) -> str:
    return _skip_terms(i,removed,source,tag=tag,avoid=())


def _integer_functional_property(d: str, tag: str) -> str:
    values = _names(tag,'ab','ac','bb','bc','eb','ec','fb','fc','p','n','P','N')
    ab,ac,bb,bc,eb,ec,fb,fc,p,n,P,N = values
    return (
        f"forall {' '.join(values)}. ({_rect_equal(ab,ac,bb,bc,eb,ec,fb,fc,d,d,tag+'entries')}) -> "
        f"({_det(ab,ac,bb,bc,d,p,n,tag+'first')}) -> ({_det(eb,ec,fb,fc,d,P,N,tag+'second')}) -> {p} + {N} = {P} + {n}"
    )


def make_matrix_integer_invariance_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    vector = ('ab','ac','bb','bc','eb','ec','fb','fc')
    row_a = ('ab','ac','bb','bc')
    cof_a = ('cb','cc','db','dc')
    row_b = ('eb','ec','fb','fc')
    cof_b = ('gb','gc','hb','hc')
    inputs = (*row_a,*cof_a,*row_b,*cof_b)
    out_a = ('ub','uc','vb','vc')
    out_b = ('Ub','Uc','Vb','Vc')
    product_ac = _product('ap','an','cp','cn')
    product_bc = _product('bp','bn','cp','cn')
    product_bd = _product('bp','bn','dp','dn')
    first_entry = 'hfirstentry'+'_witness'*6
    second_entry = 'hsecondentry'+'_witness'*6
    cofactor_first = 'hfirstcofactor'+'_witness'*6
    cofactor_second = 'hsecondcofactor'+'_witness'*6

    def term_branch(odd: bool) -> tuple[str,...]:
        side = 'right' if odd else 'left'
        theorem = 'signed_alternating_cofactor_term_odd' if odd else 'signed_alternating_cofactor_term_even'
        P,N = product_bd[::-1] if odd else product_bd
        commands = (f'cases hfirst_{side}',f'cases hfirst_{side}_right',f'have hother : P = ({P}) /\\ N = ({N})')
        commands += _apply(theorem,'bp','bn','dp','dn','i','P','N')+('exact hsecond',f'exact hfirst_{side}_left','cases hother')
        commands += (f'rewrite hfirst_{side}_right_left',f'rewrite hfirst_{side}_right_right','rewrite hother_left','rewrite hother_right')
        if odd:
            commands += _apply('matrix_integer_pair_negation_balance',*product_ac,*product_bd)
        return commands+_apply('matrix_integer_pair_product_balance','ap','an','bp','bn','cp','cn','dp','dn')+('exact hrow','exact hcofactor')

    return (
        spec(
            'matrix_integer_vector_equality_restrict',
            f"forall {' '.join(vector)} L K. ({_le('K','L','restriction_bound')}) -> ({_equal(*vector,'L','equality_full')}) -> ({_equal(*vector,'K','equality_prefix')})",
            ('lt_of_lt_of_le',),
            _intro(*vector,'L','K','hbound','hequal','i','a','b','c','d','hi','ha','hb','hc','hd')
            +_apply('hequal','i','a','b','c','d')+_apply('lt_of_lt_of_le','i','K','L')+('exact hi','exact hbound','exact ha','exact hb','exact hc','exact hd'),
            'Actual signed-integer equality restricts to every smaller finite prefix, without requiring equality of positive or negative components.',
        ),
        spec(
            'matrix_integer_vector_equality_symmetric',
            f"forall {' '.join(vector)} l. ({_equal(*vector,'l','equal_source')}) -> ({_equal(*row_b,*row_a,'l','equal_reverse')})",
            ('eq_symm',),
            _intro(*vector,'l','hequal','i','a','b','c','d','hi','ha','hb','hc','hd')+_apply('eq_symm','c + b','a + d')
            +_apply('hequal','i','c','d','a','b')+('exact hi','exact hc','exact hd','exact ha','exact hb'),
            'Signed-integer vector equality is symmetric at the actual decoded-entry level.',
        ),
        spec(
            'matrix_integer_pair_product_balance',
            f"forall ap an bp bn cp cn dp dn. ap + bn = bp + an -> cp + dn = dp + cn -> ({product_ac[0]}) + ({product_bd[1]}) = ({product_bd[0]}) + ({product_ac[1]})",
            ('signed_pair_mul_cross_transport','add_comm','add_cross_sum_chain'),
            _intro('ap','an','bp','bn','cp','cn','dp','dn','hrow','hcofactor')
            +('have hroworiented : ap + bn = an + bp','trans bp + an','exact hrow','apply add_comm')
            +('have hcoforiented : cp + dn = cn + dp','trans dp + cn','exact hcofactor','apply add_comm')
            +(f"have hfirst : {_legacy_transport('ap','an','bp','bn','cp','cn')}",)
            +_apply('signed_pair_mul_cross_transport','ap','an','bp','bn','cp','cn')+('exact hroworiented','cases hfirst')
            +(f"have hsecond : {_legacy_transport('cp','cn','dp','dn','bp','bn')}",)
            +_apply('signed_pair_mul_cross_transport','cp','cn','dp','dn','bp','bn')+('exact hcoforiented','cases hsecond')
            +(f'trans ({product_ac[1]}) + ({product_bd[0]})',)
            +_apply('add_cross_sum_chain',product_ac[0],product_ac[1],product_bc[1],product_bc[0],product_bd[1],product_bd[0])
            +('exact hfirst_left','exact hsecond_right','apply add_comm'),
            'Actual signed-pair multiplication preserves integer equality in both inputs, by two checked multiplication transports and cancellative cross-sum composition.',
        ),
        spec(
            'matrix_integer_pair_negation_balance',
            'forall p n P N. p + N = P + n -> n + P = N + p',
            ('add_comm',),
            _intro('p','n','P','N','hbalance')+('trans P + n','apply add_comm','trans p + N','symm','exact hbalance','apply add_comm'),
            'Swapping both signed pairs preserves their represented integer equality.',
        ),
        spec(
            'matrix_integer_cofactor_term_balance',
            'forall ap an cp cn bp bn dp dn i p n P N. ap + bn = bp + an -> cp + dn = dp + cn -> '
            f"({_term_terms('ap','an','cp','cn','i','p','n',tag='integer_first_term')}) -> "
            f"({_term_terms('bp','bn','dp','dn','i','P','N',tag='integer_second_term')}) -> p + N = P + n",
            ('signed_alternating_cofactor_term_even','signed_alternating_cofactor_term_odd','matrix_integer_pair_product_balance','matrix_integer_pair_negation_balance'),
            _intro('ap','an','cp','cn','bp','bn','dp','dn','i','p','n','P','N','hrow','hcofactor','hfirst','hsecond')+('cases hfirst',)
            +term_branch(False)+term_branch(True),
            'Each genuine parity-correct signed cofactor term respects integer equality of its row entry and its evaluated cofactor, in both parity branches.',
        ),
        spec(
            'matrix_integer_signed_sum_balance',
            f"forall {' '.join(vector)} l p n P N. ({_equal(*vector,'l','sum_pointwise')}) -> "
            f"({_sum_terms('ab','ac','l','p',tag='integer_sum_ap')}) -> ({_sum_terms('bb','bc','l','n',tag='integer_sum_an')}) -> "
            f"({_sum_terms('eb','ec','l','P',tag='integer_sum_bp')}) -> ({_sum_terms('fb','fc','l','N',tag='integer_sum_bn')}) -> p + N = P + n",
            ('beta_pointwise_add_prefix_exists','beta_sum_exists','beta_sum_pointwise_add','beta_at_exists'),
            _intro(*vector,'l','p','n','P','N','hequal','hap','han','hbp','hbn')
            +(f"have hadd : exists b c. ({_natural_add('ab','ac','fb','fc','b','c','l','integer_cross_code')})",)
            +_apply('beta_pointwise_add_prefix_exists','ab','ac','fb','fc','l')+_cases('hadd',2)
            +(f"have hsum : exists s. ({_sum_terms('x','x1','l','s',tag='integer_cross_sum')})",)
            +_apply('beta_sum_exists','x','x1','l')+('cases hsum','have hfirst : p + N = x2')
            +_apply('beta_sum_pointwise_add','ab','ac','fb','fc','x','x1','l','p','N','x2')
            +('exact hap','exact hbn','exact hsum_witness','exact hadd_witness_witness','have hsecond : P + n = x2')
            +_apply('beta_sum_pointwise_add','eb','ec','bb','bc','x','x1','l','P','n','x2')
            +('exact hbp','exact han','exact hsum_witness')+_intro('i','a','b','t','hi','ha','hb','ht')
            +(f"have hleft : exists c. {_at('ab','ac','i','c','integer_sum_left')}",)
            +_apply('beta_at_exists','ab','ac','i')+('cases hleft',)
            +(f"have hright : exists d. {_at('fb','fc','i','d','integer_sum_right')}",)
            +_apply('beta_at_exists','fb','fc','i')+('cases hright','trans x3 + x4')
            +_apply('hadd_witness_witness','i','x3','x4','t')+('exact hi','exact hleft_witness','exact hright_witness','exact ht')
            +_apply('hequal','i','x3','b','a','x4')+('exact hi','exact hleft_witness','exact hb','exact ha','exact hright_witness')
            +('trans x2','exact hfirst','symm','exact hsecond'),
            'Arbitrary genuine finite signed sums preserve integer equality of their entries, via an actually constructed common cross-sum code and checked finite-sum additivity.',
        ),
        spec(
            'matrix_integer_alternating_prefix_balance',
            f"forall {' '.join((*inputs,*out_a,*out_b))} l. ({_equal(*row_a,*row_b,'l','prefix_rows_equal')}) -> "
            f"({_equal(*cof_a,*cof_b,'l','prefix_cofactors_equal')}) -> "
            f"({_alternating_prefix_terms(*row_a,*cof_a,*out_a,'l',tag='integer_prefix_first')}) -> "
            f"({_alternating_prefix_terms(*row_b,*cof_b,*out_b,'l',tag='integer_prefix_second')}) -> ({_equal(*out_a,*out_b,'l','prefix_outputs_equal')})",
            ('matrix_integer_cofactor_term_balance','beta_at_unique'),
            _intro(*inputs,*out_a,*out_b,'l','hrows','hcofactors','hfirst','hsecond','i','p','n','P','N','hi','hp','hn','hP','hN')
            +(f"have hfirstentry : exists ap an bp bn tp tn. {_alternating_entry((*row_a,*cof_a),out_a,'i',('ap','an','bp','bn','tp','tn'),'integer_first_entry')}",)
            +_apply('hfirst','i')+('exact hi',)+_cases('hfirstentry',6)+_parts(first_entry,7)
            +(f"have hsecondentry : exists ap an bp bn tp tn. {_alternating_entry((*row_b,*cof_b),out_b,'i',('ap','an','bp','bn','tp','tn'),'integer_second_entry')}",)
            +_apply('hsecond','i')+('exact hi',)+_cases('hsecondentry',6)+_parts(second_entry,7)
            +('have hbalance : x4 + x11 = x10 + x5',)
            +_apply('matrix_integer_cofactor_term_balance','x','x1','x2','x3','x6','x7','x8','x9','i','x4','x5','x10','x11')
            +_apply('hrows','i','x','x1','x6','x7')+('exact hi',)
            +tuple(f'exact {_part(h,7,k)}' for h,k in ((first_entry,0),(first_entry,1),(second_entry,0),(second_entry,1)))
            +_apply('hcofactors','i','x2','x3','x8','x9')+('exact hi',)
            +tuple(f'exact {_part(h,7,k)}' for h,k in ((first_entry,2),(first_entry,3),(second_entry,2),(second_entry,3)))
            +(f'exact {_part(first_entry,7,6)}',f'exact {_part(second_entry,7,6)}')
            +tuple(command for label,code,scale,value,target,hypothesis,body,index in (
                ('hpositive','ub','uc','p','x4','hp',first_entry,4),
                ('hnegative','vb','vc','n','x5','hn',first_entry,5),
                ('hotherpositive','Ub','Uc','P','x10','hP',second_entry,4),
                ('hothernegative','Vb','Vc','N','x11','hN',second_entry,5),
            ) for command in (f'have {label} : {value} = {target}',*_apply('beta_at_unique',code,scale,'i',value,target),f'exact {hypothesis}',f'exact {_part(body,7,index)}'))
            +('rewrite hpositive','rewrite hnegative','rewrite hotherpositive','rewrite hothernegative','exact hbalance'),
            'Every actual alternating-product stream respects integer equality, including all decoded input and output streams and the parity-correct product rule.',
        ),
        spec(
            'matrix_integer_cofactor_fold_balance',
            f"forall {' '.join(inputs)} l p n P N. ({_equal(*row_a,*row_b,'l','fold_rows_equal')}) -> "
            f"({_equal(*cof_a,*cof_b,'l','fold_cofactors_equal')}) -> "
            f"({_fold_terms(*row_a,*cof_a,'l','p','n',tag='integer_fold_first')}) -> "
            f"({_fold_terms(*row_b,*cof_b,'l','P','N',tag='integer_fold_second')}) -> p + N = P + n",
            ('matrix_integer_alternating_prefix_balance','matrix_integer_signed_sum_balance'),
            _intro(*inputs,'l','p','n','P','N','hrows','hcofactors','hfirst','hsecond')
            +_cases('hfirst',4)+_parts('hfirst'+'_witness'*4,3)+_cases('hsecond',4)+_parts('hsecond'+'_witness'*4,3)
            +_apply('matrix_integer_signed_sum_balance','x','x1','x2','x3','x4','x5','x6','x7','l','p','n','P','N')
            +_apply('matrix_integer_alternating_prefix_balance',*inputs,'x','x1','x2','x3','x4','x5','x6','x7','l')
            +('exact hrows','exact hcofactors','exact hfirst_witness_witness_witness_witness_left','exact hsecond_witness_witness_witness_witness_left')
            +('exact hfirst_witness_witness_witness_witness_right_left','exact hfirst_witness_witness_witness_witness_right_right',
              'exact hsecond_witness_witness_witness_witness_right_left','exact hsecond_witness_witness_witness_witness_right_right'),
            'The complete actual alternating cofactor fold is independent of every input signed-pair representative, at arbitrary finite length.',
        ),
        spec(
            'matrix_integer_minor_cell_at_source',
            f"forall b c q j r s u v a. ({_skip('r','0','u','minor_selected_row')}) -> ({_skip('s','j','v','minor_selected_column')}) -> "
            f"({_cell('b','c','q','j','r','s','a','minor_source_cell')}) -> ({_at('b','c','u * (S q) + v','a','minor_source_value')})",
            ('matrix_skip_index_functional',),
            _intro('b','c','q','j','r','s','u','v','a','hrow','hcolumn','hcell')+_cases('hcell',2)+_parts('hcell_witness_witness',3)
            +('have hroweq : u = x',)+_apply('matrix_skip_index_functional','r','0','u','x')+('exact hrow','exact hcell_witness_witness_left')
            +('have hcoleq : v = x1',)+_apply('matrix_skip_index_functional','s','j','v','x1')+('exact hcolumn','exact hcell_witness_witness_right_left')
            +_rewrite_all('hroweq','u',_at('b','c','u * (S q) + v','a','minor_align_row'))
            +_rewrite_all('hcoleq','v',_at('b','c','x * (S q) + v','a','minor_align_column'))+('exact hcell_witness_witness_right_right',),
            'Any genuine cofactor cell is the actual source beta value at the uniquely determined skipped row and column.',
        ),
        spec(
            'matrix_integer_minor_cell_balance',
            f"forall {' '.join(vector)} q j r s a b c d. ({_rect_equal(*vector,'S q','S q','minor_parent_equal')}) -> "
            f"({_lt('r','q','minor_row_bound')}) -> ({_lt('s','q','minor_col_bound')}) -> "
            f"({_cell('ab','ac','q','j','r','s','a','minor_cell_ap')}) -> ({_cell('bb','bc','q','j','r','s','b','minor_cell_an')}) -> "
            f"({_cell('eb','ec','q','j','r','s','c','minor_cell_bp')}) -> ({_cell('fb','fc','q','j','r','s','d','minor_cell_bn')}) -> a + d = c + b",
            ('matrix_skip_index_bounded','matrix_recursive_flattened_index_bound','matrix_integer_minor_cell_at_source'),
            _intro(*vector,'q','j','r','s','a','b','c','d','hequal','hr','hs','hap','han','hbp','hbn')
            +_cases('hap',2)+_parts('hap_witness_witness',3)
            +(f"have hrow : {_lt('x','S q','minor_parent_row')}",)
            +_apply('matrix_skip_index_bounded','r','0','x','q')+('exact hap_witness_witness_left','exact hr')
            +(f"have hcolumn : {_lt('x1','S q','minor_parent_col')}",)
            +_apply('matrix_skip_index_bounded','s','j','x1','q')+('exact hap_witness_witness_right_left','exact hs')
            +_apply('hequal','x * (S q) + x1','a','b','c','d')
            +_apply('matrix_recursive_flattened_index_bound','S q','x','x1')+('exact hrow','exact hcolumn','exact hap_witness_witness_right_right')
            +tuple(command for code,scale,value,hyp in (('bb','bc','b','han'),('eb','ec','c','hbp'),('fb','fc','d','hbn')) for command in (
                *_apply('matrix_integer_minor_cell_at_source',code,scale,'q','j','r','s','x','x1',value),
                'exact hap_witness_witness_left','exact hap_witness_witness_right_left',f'exact {hyp}',
            )),
            'All four actual cofactor component cells satisfy the parent signed-integer equality at one genuinely shared in-range source position.',
        ),
        spec(
            'matrix_integer_minor_prefix_cell_at_coordinates',
            f"forall b c q j u v k r s a. ({_natural_minor('b','c','q','j','u','v','minor_prefix_source')}) -> "
            f"({_lt('k','q * q','minor_flat_bound')}) -> k = q * r + s -> ({_lt('s','q','minor_coordinate_bound')}) -> "
            f"({_at('u','v','k','a','minor_output_value')}) -> ({_cell('b','c','q','j','r','s','a','minor_cell_result')})",
            ('division_remainder_unique','beta_at_unique'),
            _intro('b','c','q','j','u','v','k','r','s','a','hminor','hk','hcoordinate','hs','ha')
            +(f"have hentry : exists R C A. {_and('k = q * R + C',_lt('C','q','decoded_col'),_cell('b','c','q','j','R','C','A','decoded_cell'),_at('u','v','k','A','decoded_value'))}",)
            +_apply('hminor','k')+('exact hk',)+_cases('hentry',3)+_parts('hentry'+'_witness'*3,4)
            +('have hcoordinates : r = x /\\ s = x1',)+_apply('division_remainder_unique','q','k','r','s','x','x1')
            +('exact hcoordinate','exact hs','exact hentry_witness_witness_witness_left','exact hentry_witness_witness_witness_right_left','cases hcoordinates','have hvalue : a = x2')
            +_apply('beta_at_unique','u','v','k','a','x2')+('exact ha','exact hentry_witness_witness_witness_right_right_right')
            +_rewrite_all('hcoordinates_left','r',_cell('b','c','q','j','r','s','a','aligned_row'))
            +_rewrite_all('hcoordinates_right','s',_cell('b','c','q','j','x','s','a','aligned_column'))
            +_rewrite_all('hvalue','a',_cell('b','c','q','j','x','x1','a','aligned_value'))+('exact hentry_witness_witness_witness_right_right_left',),
            'Every actual decoded minor output is its genuine cofactor cell at any valid quotient/remainder coordinates, by unique coordinates and beta functionality.',
        ),
        spec(
            'matrix_integer_square_index_width_nonzero',
            f"forall q i. ({_lt('i','q * q','square_index')}) -> ~(q = 0)",
            ('matrix_rank_no_index_below_zero',),
            _intro('q','i','hi','hzero')+('have hlength : q * q = 0','rewrite hzero','rewrite hzero','apply PA5','rewrite hlength at hi')
            +_apply('matrix_rank_no_index_below_zero','i')+('exact hi',),
            'An actual index in a square prefix proves its row width is nonzero; zero-dimensional bounds remain genuinely vacuous.',
        ),
        spec(
            'matrix_integer_signed_minor_balance',
            f"forall {' '.join((*vector,*out_a,*out_b))} q j. ({_rect_equal(*vector,'S q','S q','signed_minor_parent')}) -> "
            f"({_minor(*row_a,'q','j',*out_a,'signed_minor_first')}) -> ({_minor(*row_b,'q','j',*out_b,'signed_minor_second')}) -> "
            f"({_rect_equal(*out_a,*out_b,'q','q','signed_minor_equal')})",
            ('matrix_integer_square_index_width_nonzero','division_remainder_exists','matrix_recursive_quotient_row_bound',
             'matrix_integer_minor_prefix_cell_at_coordinates','matrix_integer_minor_cell_balance'),
            _intro(*vector,*out_a,*out_b,'q','j','hequal','hfirst','hsecond')+('cases hfirst','cases hsecond')
            +_intro('i','a','b','c','d','hi','ha','hb','hc','hd')
            +('have hq : ~(q = 0)','intro hzero')+_apply('matrix_integer_square_index_width_nonzero','q','i')+('exact hi','exact hzero')
            +(f"have hcoordinates : exists r s. i = q * r + s /\\ ({_lt('s','q','minor_common_col')})",)
            +_apply('division_remainder_exists','q','i')+('exact hq',)+_cases('hcoordinates',2)+('cases hcoordinates_witness_witness',)
            +(f"have hrow : {_lt('x','q','minor_common_row')}",)
            +_apply('matrix_recursive_quotient_row_bound','q','i','x','x1')+('exact hcoordinates_witness_witness_left','exact hi')
            +_apply('matrix_integer_minor_cell_balance',*vector,'q','j','x','x1','a','b','c','d')+('exact hequal','exact hrow','exact hcoordinates_witness_witness_right')
            +tuple(command for code,scale,outcode,outscale,value,hminor,hvalue in (
                ('ab','ac','ub','uc','a','hfirst_left','ha'),('bb','bc','vb','vc','b','hfirst_right','hb'),
                ('eb','ec','Ub','Uc','c','hsecond_left','hc'),('fb','fc','Vb','Vc','d','hsecond_right','hd'),
            ) for command in (
                *_apply('matrix_integer_minor_prefix_cell_at_coordinates',code,scale,'q','j',outcode,outscale,'i','x','x1',value),
                f'exact {hminor}','exact hi','exact hcoordinates_witness_witness_left','exact hcoordinates_witness_witness_right',f'exact {hvalue}',
            )),
            'Genuine cofactor minors of integer-equal matrices are integer-equal, even when every positive/negative code and representative differs.',
        ),
        spec(
            'matrix_integer_cofactor_streams_from_recursion',
            f"forall {' '.join((*vector,*cof_a,*cof_b))} q. ({_integer_functional_property('q','integer_recursion')}) -> "
            f"({_rect_equal(*vector,'S q','S q','integer_cofactor_parents')}) -> "
            f"({_cofactors(*row_a,'q',*cof_a,'integer_cofactor_first')}) -> ({_cofactors(*row_b,'q',*cof_b,'integer_cofactor_second')}) -> "
            f"({_equal(*cof_a,*cof_b,'S q','integer_cofactor_streams')})",
            ('matrix_integer_signed_minor_balance','beta_at_unique'),
            _intro(*vector,*cof_a,*cof_b,'q','hrecursion','hequal','hfirst','hsecond','i','p','n','P','N','hi','hp','hn','hP','hN')
            +(f"have hfirstcofactor : exists u v U V a b. {_cofactor_entry(*row_a,'q',*cof_a,'i','u','v','U','V','a','b','integer_first_cofactor')}",)
            +_apply('hfirst','i')+('exact hi',)+_cases('hfirstcofactor',6)+_parts(cofactor_first,4)
            +(f"have hsecondcofactor : exists u v U V a b. {_cofactor_entry(*row_b,'q',*cof_b,'i','u','v','U','V','a','b','integer_second_cofactor')}",)
            +_apply('hsecond','i')+('exact hi',)+_cases('hsecondcofactor',6)+_parts(cofactor_second,4)
            +('have hbalance : x4 + x11 = x10 + x5',)
            +_apply('hrecursion','x','x1','x2','x3','x6','x7','x8','x9','x4','x5','x10','x11')
            +_apply('matrix_integer_signed_minor_balance',*vector,'x','x1','x2','x3','x6','x7','x8','x9','q','i')
            +('exact hequal',f'exact {_part(cofactor_first,4,0)}',f'exact {_part(cofactor_second,4,0)}',f'exact {_part(cofactor_first,4,1)}',f'exact {_part(cofactor_second,4,1)}')
            +tuple(command for label,code,scale,value,target,hypothesis,body,index in (
                ('hpositive','cb','cc','p','x4','hp',cofactor_first,2),
                ('hnegative','db','dc','n','x5','hn',cofactor_first,3),
                ('hotherpositive','gb','gc','P','x10','hP',cofactor_second,2),
                ('hothernegative','hb','hc','N','x11','hN',cofactor_second,3),
            ) for command in (f'have {label} : {value} = {target}',*_apply('beta_at_unique',code,scale,'i',value,target),f'exact {hypothesis}',f'exact {_part(body,4,index)}'))
            +('rewrite hpositive','rewrite hnegative','rewrite hotherpositive','rewrite hothernegative','exact hbalance'),
            'The smaller-dimension integer-invariance induction hypothesis identifies all genuinely evaluated cofactor streams; the hypothesis is discharged by the final dimension induction.',
        ),
        spec(
            'matrix_integer_first_row_equality',
            f"forall {' '.join(vector)} q. ({_rect_equal(*vector,'S q','S q','parent_matrix_equal')}) -> ({_equal(*vector,'S q','first_row_equal')})",
            ('matrix_integer_vector_equality_restrict','le_scaled_nonzero','succ_ne_zero'),
            _intro(*vector,'q','hequal')+_apply('matrix_integer_vector_equality_restrict',*vector,'(S q) * (S q)','S q')
            +_apply('le_scaled_nonzero','S q','S q')+_apply('succ_ne_zero','q')+('exact hequal',),
            'Actual integer equality of a nonempty square matrix entails equality of its complete genuine first row.',
        ),
        spec(
            'signed_recursive_determinant_integer_invariant',
            f"forall d. ({_integer_functional_property('d','determinant_integer_invariance')})",
            ('signed_recursive_determinant_zero_value','signed_recursive_determinant_successor_decomposition',
             'matrix_integer_cofactor_streams_from_recursion','matrix_integer_first_row_equality','matrix_integer_cofactor_fold_balance'),
            ('induction d',)+_intro(*vector,'p','n','P','N','hequal','hfirst','hsecond')
            +('have hfirstvalue : p = 1 /\\ n = 0',)+_apply('signed_recursive_determinant_zero_value',*row_a,'p','n')+('exact hfirst','cases hfirstvalue')
            +('have hsecondvalue : P = 1 /\\ N = 0',)+_apply('signed_recursive_determinant_zero_value',*row_b,'P','N')+('exact hsecond','cases hsecondvalue')
            +('rewrite hfirstvalue_left','rewrite hfirstvalue_right','rewrite hsecondvalue_left','rewrite hsecondvalue_right','refl')
            +_intro(*vector,'p','n','P','N','hequal','hfirst','hsecond')
            +(f"have hfirstcof : exists u v U V. {_and(_cofactors(*row_a,'d','u','v','U','V','invariant_first_cofactors'),_fold_terms(*row_a,'u','v','U','V','S d','p','n',tag='integer_invariant_first_fold'))}",)
            +_apply('signed_recursive_determinant_successor_decomposition',*row_a,'d','p','n')+('exact hfirst',)+_cases('hfirstcof',4)+('cases hfirstcof_witness_witness_witness_witness',)
            +(f"have hsecondcof : exists u v U V. {_and(_cofactors(*row_b,'d','u','v','U','V','invariant_second_cofactors'),_fold_terms(*row_b,'u','v','U','V','S d','P','N',tag='integer_invariant_second_fold'))}",)
            +_apply('signed_recursive_determinant_successor_decomposition',*row_b,'d','P','N')+('exact hsecond',)+_cases('hsecondcof',4)+('cases hsecondcof_witness_witness_witness_witness',)
            +(f"have hcofactors : {_equal('x','x1','x2','x3','x4','x5','x6','x7','S d','recursive_cofactor_equal')}",)
            +_apply('matrix_integer_cofactor_streams_from_recursion',*vector,'x','x1','x2','x3','x4','x5','x6','x7','d')
            +('exact IH','exact hequal','exact hfirstcof_witness_witness_witness_witness_left','exact hsecondcof_witness_witness_witness_witness_left')
            +_apply('matrix_integer_cofactor_fold_balance',*row_a,'x','x1','x2','x3',*row_b,'x4','x5','x6','x7','S d','p','n','P','N')
            +_apply('matrix_integer_first_row_equality',*vector,'d')+('exact hequal','exact hcofactors','exact hfirstcof_witness_witness_witness_witness_right','exact hsecondcof_witness_witness_witness_witness_right'),
            'Unrestricted HA dimension induction proves the true signed determinant is invariant under all entrywise integer-equal representations: p+N=P+n, with genuine cofactor evaluations and no assumed induction or quotient-invariance premise.',
        ),
    )


__all__ = ['integer_matrix_entrywise_equal_relation','make_matrix_integer_invariance_candidate_theorems']
