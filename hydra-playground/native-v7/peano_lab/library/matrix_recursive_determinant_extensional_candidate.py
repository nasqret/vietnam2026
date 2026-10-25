"""Actual finite-matrix extensionality for recursive signed determinants.

Beta encodings of a finite matrix are not unique.  Therefore determinant
functionality must compare actual entries and actual cofactor minors, not
merely reuse uniqueness of a fold with fixed supplied value streams.
"""

from __future__ import annotations

from typing import Any, Callable

from .matrix_cofactor_expansion_candidate import _alternating_prefix_terms, _fold_terms, _term_terms
from .matrix_determinant_minors_candidate import _minor_cell_terms, _minor_prefix_terms
from .matrix_recursive_determinant_candidate import (
    _and, _apply, _arguments, _at, _cases, _cofactors, _det, _exists, _intro, _le, _lt,
    _history, _minor, _names, _part, _parts, _prefix, _record, _rewrite_all,
)


def _cell(b: str, c: str, q: str, j: str, r: str, s: str, a: str, tag: str) -> str:
    return _minor_cell_terms(b,c,f'S ({q})','0',j,r,s,a,tag=f'mdre_{tag}',avoid=())


def _natural_minor(b: str, c: str, q: str, j: str, u: str, v: str, tag: str) -> str:
    return _minor_prefix_terms(
        b,c,f'S ({q})','0',j,u,v,q,f'({q}) * ({q})',
        tag=f'mdre_{tag}',avoid=(),
    )


def _matrix_equal(pb: str, pc: str, nb: str, nc: str, qb: str, qc: str, rb: str, rc: str, d: str, tag: str) -> str:
    return _and(_prefix(pb,pc,qb,qc,f'({d}) * ({d})',tag+'p'),_prefix(nb,nc,rb,rc,f'({d}) * ({d})',tag+'n'))


def signed_matrix_prefix_equality_relation(pb: str, pc: str, nb: str, nc: str, qb: str, qc: str, rb: str, rc: str, d: str, *, tag: str) -> str:
    """Exact equality of all positive and negative cells of a finite square."""
    return _matrix_equal(*_arguments(pb,pc,nb,nc,qb,qc,rb,rc,d),tag)


def _functional_property(d: str, tag: str) -> str:
    values = _names(tag,'pb','pc','nb','nc','qb','qc','rb','rc','p','n','r','s')
    pb,pc,nb,nc,qb,qc,rb,rc,p,n,r,s = values
    return (
        f"forall {' '.join(values)}. ({_matrix_equal(pb,pc,nb,nc,qb,qc,rb,rc,d,tag+'m')}) -> "
        f"({_det(pb,pc,nb,nc,d,p,n,tag+'a')}) -> ({_det(qb,qc,rb,rc,d,r,s,tag+'b')}) -> "
        f"{p} = {r} /\\ {n} = {s}"
    )


def _cofactor_entry(pb: str, pc: str, nb: str, nc: str, q: str, eb: str, ec: str, fb: str, fc: str, j: str, up: str, us: str, un: str, ut: str, p: str, n: str, tag: str) -> str:
    return _and(
        _minor(pb,pc,nb,nc,q,j,up,us,un,ut,tag+'m'),
        _det(up,us,un,ut,q,p,n,tag+'d'),
        _at(eb,ec,j,p,tag+'p'),_at(fb,fc,j,n,tag+'n'),
    )


def make_matrix_recursive_determinant_extensional_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    first_h = 'hfirst' + '_witness'*3
    second_h = 'hsecond' + '_witness'*3
    source_h = 'hentry' + '_witness'*3
    fold_source = ('pb','pc','nb','nc','eb','ec','fb','fc')
    fold_target = ('qb','qc','rb','rc','ub','uc','vb','vc')
    products = ('wb','wc','zb','zc')
    fold_prefixes = tuple(_prefix(*fold_source[2*i:2*i+2],*fold_target[2*i:2*i+2],'l',f'fold_input_{i}') for i in range(4))
    fold_hypotheses = ('hrowp','hrown','hcofp','hcofn')
    fold_entry_parts = tuple(_at(*fold_source[2*i:2*i+2],'i',('ap','an','bp','bn')[i],f'fold_entry_{i}') for i in range(4))
    fold_entry = _and(*fold_entry_parts,_at('wb','wc','i','p','fold_entry_p'),_at('zb','zc','i','n','fold_entry_n'),_term_terms('ap','an','bp','bn','i','p','n',tag='mdre_fold_entry'))
    fold_entry_h = 'hentry' + '_witness'*6
    parents = ('pb','pc','nb','nc','qb','qc','rb','rc')
    cofactor_first_h = 'hfirstentry' + '_witness'*6
    cofactor_second_h = 'hsecondentry' + '_witness'*6
    unique_other = f"forall r s. ({_det('pb','pc','nb','nc','d','r','s','unique_other')}) -> r = p /\\ s = n"
    unique_result = _and(_det('pb','pc','nb','nc','d','p','n','unique_value'),unique_other)
    successor_det = _det('pb','pc','nb','nc','S q','p','n','cofactor_equation')
    cofactor_equation_rhs = 'exists eb ec fb fc. '+_and(
        _cofactors('pb','pc','nb','nc','q','eb','ec','fb','fc','equation_cofactors'),
        _fold_terms('pb','pc','nb','nc','eb','ec','fb','fc','S q','p','n',tag='mdre_equation_fold'),
    )
    empty_det = _det('pb','pc','nb','nc','0','p','n','empty_equation')
    empty_equation = _and(f'({empty_det}) -> (p = 1 /\\ n = 0)',f'(p = 1 /\\ n = 0) -> ({empty_det})')

    def cofactor_stream_component(negative: bool) -> tuple[str, ...]:
        source_code, source_scale, target_code, target_scale = (
            ('fb','fc','vb','vc') if negative else ('eb','ec','ub','uc')
        )
        source_value, target_value = ('x5','x11') if negative else ('x4','x10')
        entry_part = 3 if negative else 2
        return (
            _intro('j','a','hj','ha')
            +(f"have hfirstentry : exists up us un ut ap an. ({_cofactor_entry('pb','pc','nb','nc','q','eb','ec','fb','fc','j','up','us','un','ut','ap','an','cof_first')})",)
            +_apply('hcofirst','j')+('exact hj',)+_cases('hfirstentry',6)+_parts(cofactor_first_h,4)
            +(f"have hsecondentry : exists up us un ut ap an. ({_cofactor_entry('qb','qc','rb','rc','q','ub','uc','vb','vc','j','up','us','un','ut','ap','an','cof_second')})",)
            +_apply('hcosecond','j')+('exact hj',)+_cases('hsecondentry',6)+_parts(cofactor_second_h,4)
            +('have hvalues : x4 = x10 /\\ x5 = x11',)
            +_apply('hrecursion','x','x1','x2','x3','x6','x7','x8','x9','x4','x5','x10','x11')
            +_apply('matrix_recursive_signed_minor_extensional',*parents,'q','j','x','x1','x2','x3','x6','x7','x8','x9')
            +('exact hparent',f"exact {_part(cofactor_first_h,4,0)}",f"exact {_part(cofactor_second_h,4,0)}",f"exact {_part(cofactor_first_h,4,1)}",f"exact {_part(cofactor_second_h,4,1)}",'cases hvalues')
            +(f"have houtput : a = {target_value}",f"trans {source_value}")
            +_apply('beta_at_unique',source_code,source_scale,'j','a',source_value)
            +('exact ha',f"exact {_part(cofactor_first_h,4,entry_part)}",f"exact hvalues_{'right' if negative else 'left'}")
            +_rewrite_all('houtput','a',_at(target_code,target_scale,'j','a','cof_value_target'))
            +(f"exact {_part(cofactor_second_h,4,entry_part)}",)
        )

    return (
        spec(
            'matrix_recursive_lt_add_left',
            f"forall a b c. ({_lt('a','b','add_source')}) -> ({_lt('c + a','c + b','add_result')})",
            ('add_le_add_left',), _intro('a','b','c','hab')
            +('have heq : c + S a = S (c + a)','apply PA4')
            +(f"have hsum : {_le('c + S a','c + b','add_middle')}",)
            +_apply('add_le_add_left','S a','b','c')+('exact hab','rewrite heq at hsum','exact hsum'),
            'Strict natural order is preserved by a common left summand, by explicit successor transport.',
        ),
        spec(
            'matrix_recursive_flattened_index_bound',
            f"forall w r s. ({_lt('r','w','flat_row')}) -> ({_lt('s','w','flat_column')}) -> ({_lt('r * w + s','w * w','flat_result')})",
            ('matrix_recursive_lt_add_left','mul_le_mul_right','mul_succ_left','lt_of_lt_of_le'),
            _intro('w','r','s','hr','hs')
            +('have heq : (S r) * w = r * w + w','apply mul_succ_left')
            +(f"have hrowend : {_le('(S r) * w','w * w','flat_row_end')}",)
            +_apply('mul_le_mul_right','S r','w','w')+('exact hr','rewrite heq at hrowend')
            +_apply('lt_of_lt_of_le','r * w + s','r * w + w','w * w')
            +_apply('matrix_recursive_lt_add_left','s','w','r * w')+('exact hs','exact hrowend'),
            'Every in-range row and column has an actual flattened index below the square matrix length.',
        ),
        spec(
            'matrix_recursive_quotient_row_bound',
            f"forall q k r s. k = q * r + s -> ({_lt('k','q * q','quotient_source')}) -> ({_lt('r','q','quotient_row')})",
            ('le_or_lt','mul_le_mul_left','le_add_right','le_trans','lt_not_le'),
            _intro('q','k','r','s','hk','hbound')
            +('specialize le_or_lt q','specialize le_or_lt r','cases le_or_lt','exfalso')
            +(f"have hreverse : {_le('q * q','k','quotient_reverse')}",'rewrite hk')
            +_apply('le_trans','q * q','q * r','q * r + s')
            +_apply('mul_le_mul_left','q','r','q')+('exact le_or_lt_left',)
            +_apply('le_add_right','q * r','s')
            +_apply('lt_not_le','k','q * q')+('exact hbound','exact hreverse','exact le_or_lt_right'),
            'A genuine row-major index below q squared has row coordinate below q, including the vacuous zero-width boundary.',
        ),
        spec(
            'matrix_recursive_minor_cell_transport',
            f"forall b c B C q j r s a. ({_prefix('b','c','B','C','(S q) * (S q)','cell_parent')}) -> "
            f"({_lt('r','q','cell_row')}) -> ({_lt('s','q','cell_column')}) -> "
            f"({_cell('b','c','q','j','r','s','a','cell_source')}) -> ({_cell('B','C','q','j','r','s','a','cell_result')})",
            ('matrix_skip_index_bounded','matrix_recursive_flattened_index_bound'),
            _intro('b','c','B','C','q','j','r','s','a','hprefix','hr','hs','hcell')
            +_cases('hcell',2)+_parts('hcell_witness_witness',3)
            +(f"have hrow : {_lt('x','S q','transport_row')}",)
            +_apply('matrix_skip_index_bounded','r','0','x','q')
            +(f"exact {_part('hcell_witness_witness',3,0)}",'exact hr')
            +(f"have hcolumn : {_lt('x1','S q','transport_column')}",)
            +_apply('matrix_skip_index_bounded','s','j','x1','q')
            +(f"exact {_part('hcell_witness_witness',3,1)}",'exact hs')
            +(f"have hindex : {_lt('x * (S q) + x1','(S q) * (S q)','transport_index')}",)
            +_apply('matrix_recursive_flattened_index_bound','S q','x','x1')+('exact hrow','exact hcolumn')
            +_exists('x','x1')+('split',f"exact {_part('hcell_witness_witness',3,0)}",'split',f"exact {_part('hcell_witness_witness',3,1)}")
            +_apply('hprefix','x * (S q) + x1','a')+('exact hindex',f"exact {_part('hcell_witness_witness',3,2)}"),
            'Every actual first-row minor cell transports across equality of all in-range parent-matrix entries.',
        ),
        spec(
            'matrix_recursive_minor_prefix_transport',
            f"forall b c B C q j u v. ({_prefix('b','c','B','C','(S q) * (S q)','minor_parent')}) -> "
            f"({_natural_minor('b','c','q','j','u','v','minor_source')}) -> ({_natural_minor('B','C','q','j','u','v','minor_result')})",
            ('matrix_recursive_quotient_row_bound','matrix_recursive_minor_cell_transport'),
            _intro('b','c','B','C','q','j','u','v','hprefix','hminor','k','hk')
            +(f"have hentry : exists r s a. {_and('k = q * r + s',_lt('s','q','entry_s'),_cell('b','c','q','j','r','s','a','entry_cell'),_at('u','v','k','a','entry_value'))}",)
            +_apply('hminor','k')+('exact hk',)+_cases('hentry',3)+_parts(source_h,4)
            +_exists('x','x1','x2')+('split',f"exact {_part(source_h,4,0)}",'split',f"exact {_part(source_h,4,1)}",'split')
            +_apply('matrix_recursive_minor_cell_transport','b','c','B','C','q','j','x','x1','x2')
            +('exact hprefix',)+_apply('matrix_recursive_quotient_row_bound','q','k','x','x1')
            +(f"exact {_part(source_h,4,0)}",'exact hk',f"exact {_part(source_h,4,1)}",f"exact {_part(source_h,4,2)}",f"exact {_part(source_h,4,3)}"),
            'An actual finite cofactor-minor code remains the same minor after extensionally equal recoding of its parent matrix.',
        ),
        spec(
            'matrix_recursive_minor_prefix_functional',
            f"forall b c q j u v U V. ({_natural_minor('b','c','q','j','u','v','first_minor')}) -> "
            f"({_natural_minor('b','c','q','j','U','V','second_minor')}) -> ({_prefix('u','v','U','V','q * q','minor_unique')})",
            ('division_remainder_unique','beta_at_unique','beta_matrix_minor_cell_functional'),
            _intro('b','c','q','j','u','v','U','V','hleft','hright','k','a','hk','ha')
            +(f"have hfirst : exists r s z. {_and('k = q * r + s',_lt('s','q','first_s'),_cell('b','c','q','j','r','s','z','first_cell'),_at('u','v','k','z','first_value'))}",)
            +_apply('hleft','k')+('exact hk',)+_cases('hfirst',3)+_parts(first_h,4)
            +(f"have hsecond : exists r s z. {_and('k = q * r + s',_lt('s','q','second_s'),_cell('b','c','q','j','r','s','z','second_cell'),_at('U','V','k','z','second_value'))}",)
            +_apply('hright','k')+('exact hk',)+_cases('hsecond',3)+_parts(second_h,4)
            +('have hcoordinates : x = x3 /\\ x1 = x4',)
            +_apply('division_remainder_unique','q','k','x','x1','x3','x4')
            +(f"exact {_part(first_h,4,0)}",f"exact {_part(first_h,4,1)}",f"exact {_part(second_h,4,0)}",f"exact {_part(second_h,4,1)}",'cases hcoordinates')
            +('have hvalues : x2 = x5',)
            +_apply('beta_matrix_minor_cell_functional','b','c','S q','0','j','x','x1','x2','x5')
            +(f"exact {_part(first_h,4,2)}",)
            +_rewrite_all('hcoordinates_left','x',_cell('b','c','q','j','x','x1','x5','align_row'))
            +_rewrite_all('hcoordinates_right','x1',_cell('b','c','q','j','x3','x1','x5','align_column'))
            +(f"exact {_part(second_h,4,2)}",'have houtput : a = x5','trans x2')
            +_apply('beta_at_unique','u','v','k','a','x2')+('exact ha',f"exact {_part(first_h,4,3)}",'exact hvalues')
            +_rewrite_all('houtput','a',_at('U','V','k','a','unique_value'))
            +(f"exact {_part(second_h,4,3)}",),
            'Two complete codes of the same actual cofactor minor agree at every in-range child entry; division uniqueness aligns the genuine row/column witnesses.',
        ),
        spec(
            'matrix_recursive_signed_minor_extensional',
            f"forall pb pc nb nc qb qc rb rc q j up us un ut vp vs vn vt. "
            f"({_matrix_equal('pb','pc','nb','nc','qb','qc','rb','rc','S q','parent_equal')}) -> "
            f"({_minor('pb','pc','nb','nc','q','j','up','us','un','ut','left_signed_minor')}) -> "
            f"({_minor('qb','qc','rb','rc','q','j','vp','vs','vn','vt','right_signed_minor')}) -> "
            f"({_matrix_equal('up','us','un','ut','vp','vs','vn','vt','q','child_equal')})",
            ('matrix_recursive_minor_prefix_transport','matrix_recursive_minor_prefix_functional'),
            _intro('pb','pc','nb','nc','qb','qc','rb','rc','q','j','up','us','un','ut','vp','vs','vn','vt','hparent','hfirst','hsecond')
            +('cases hparent','cases hfirst','cases hsecond','split')
            +(f"have hpositive : {_natural_minor('qb','qc','q','j','up','us','transported_positive')}",)
            +_apply('matrix_recursive_minor_prefix_transport','pb','pc','qb','qc','q','j','up','us')
            +('exact hparent_left','exact hfirst_left')
            +_apply('matrix_recursive_minor_prefix_functional','qb','qc','q','j','up','us','vp','vs')
            +('exact hpositive','exact hsecond_left')
            +(f"have hnegative : {_natural_minor('rb','rc','q','j','un','ut','transported_negative')}",)
            +_apply('matrix_recursive_minor_prefix_transport','nb','nc','rb','rc','q','j','un','ut')
            +('exact hparent_right','exact hfirst_right')
            +_apply('matrix_recursive_minor_prefix_functional','rb','rc','q','j','un','ut','vn','vt')
            +('exact hnegative','exact hsecond_right'),
            'Every pair of corresponding actual signed cofactor minors of pointwise-equal matrices are themselves pointwise equal, regardless of their beta encodings.',
        ),
        spec(
            'matrix_recursive_alternating_prefix_transport',
            f"forall {' '.join((*fold_source,*fold_target,*products,'l'))}. "
            +''.join(f'({item}) -> ' for item in fold_prefixes)
            +f"({_alternating_prefix_terms(*fold_source,*products,'l',tag='mdre_alt_source')}) -> ({_alternating_prefix_terms(*fold_target,*products,'l',tag='mdre_alt_target')})",
            (), _intro(*fold_source,*fold_target,*products,'l',*fold_hypotheses,'hprefix','i','hi')
            +(f"have hentry : exists ap an bp bn p n. {fold_entry}",)
            +_apply('hprefix','i')+('exact hi',)+_cases('hentry',6)+_parts(fold_entry_h,7)
            +_exists('x','x1','x2','x3','x4','x5')
            +tuple(command for index,(hypothesis,value) in enumerate(zip(fold_hypotheses,('x','x1','x2','x3')))
                   for command in (('split',)+_apply(hypothesis,'i',value)+('exact hi',f"exact {_part(fold_entry_h,7,index)}")))
            +('split',f"exact {_part(fold_entry_h,7,4)}",'split',f"exact {_part(fold_entry_h,7,5)}",f"exact {_part(fold_entry_h,7,6)}"),
            'The exact signed parity-correct product stream is unchanged when all four finite input streams preserve their actual entries.',
        ),
        spec(
            'matrix_recursive_alternating_fold_transport',
            f"forall {' '.join((*fold_source,*fold_target,'l','p','n'))}. "
            +''.join(f'({item}) -> ' for item in fold_prefixes)
            +f"({_fold_terms(*fold_source,'l','p','n',tag='mdre_fold_source')}) -> ({_fold_terms(*fold_target,'l','p','n',tag='mdre_fold_target')})",
            ('matrix_recursive_alternating_prefix_transport',),
            _intro(*fold_source,*fold_target,'l','p','n',*fold_hypotheses,'hfold')
            +_cases('hfold',4)+_parts('hfold'+'_witness'*4,3)+_exists('x','x1','x2','x3')+('split',)
            +_apply('matrix_recursive_alternating_prefix_transport',*fold_source,*fold_target,'x','x1','x2','x3','l')
            +tuple(f'exact {name}' for name in fold_hypotheses)
            +(f"exact {_part('hfold'+'_witness'*4,3,0)}",'split',f"exact {_part('hfold'+'_witness'*4,3,1)}",f"exact {_part('hfold'+'_witness'*4,3,2)}"),
            'An actual signed alternating sum transports to extensionally equal input encodings while preserving its genuine term and partial-sum witnesses.',
        ),
        spec(
            'matrix_recursive_alternating_fold_extensional',
            f"forall {' '.join((*fold_source,*fold_target,'l','p','n','r','s'))}. "
            +''.join(f'({item}) -> ' for item in fold_prefixes)
            +f"({_fold_terms(*fold_source,'l','p','n',tag='mdre_fold_first')}) -> ({_fold_terms(*fold_target,'l','r','s',tag='mdre_fold_second')}) -> p = r /\\ n = s",
            ('matrix_recursive_alternating_fold_transport','signed_alternating_cofactor_fold_functional'),
            _intro(*fold_source,*fold_target,'l','p','n','r','s',*fold_hypotheses,'hfirst','hsecond')
            +(f"have htransported : {_fold_terms(*fold_target,'l','p','n',tag='mdre_transported_fold')}",)
            +_apply('matrix_recursive_alternating_fold_transport',*fold_source,*fold_target,'l','p','n')
            +tuple(f'exact {name}' for name in fold_hypotheses)+('exact hfirst',)
            +_apply('signed_alternating_cofactor_fold_functional',*fold_target,'l','p','n','r','s')
            +('exact htransported','exact hsecond'),
            'Every finite signed alternating cofactor sum is functional across pointwise-equal input codes, not just identical beta parameters.',
        ),
        spec(
            'matrix_recursive_matrix_equality_refl',
            f"forall pb pc nb nc d. ({_matrix_equal('pb','pc','nb','nc','pb','pc','nb','nc','d','matrix_refl')})",
            ('matrix_recursive_prefix_refl',), _intro('pb','pc','nb','nc','d')+('split',)
            +_apply('matrix_recursive_prefix_refl','pb','pc','d * d')
            +_apply('matrix_recursive_prefix_refl','nb','nc','d * d'),
            'Every actual finite signed matrix is pointwise equal to itself.',
        ),
        spec(
            'matrix_recursive_initial_row_prefix',
            f"forall b c B C q. ({_prefix('b','c','B','C','(S q) * (S q)','square_prefix')}) -> ({_prefix('b','c','B','C','S q','row_prefix')})",
            ('succ_ne_zero','le_scaled_nonzero','matrix_recursive_prefix_restrict'),
            _intro('b','c','B','C','q','hprefix')
            +_apply('matrix_recursive_prefix_restrict','b','c','B','C','(S q) * (S q)','S q')
            +_apply('le_scaled_nonzero','S q','S q')
            +_apply('succ_ne_zero','q')+('exact hprefix',),
            'Equality of all cells of a nonempty square matrix includes every actual first-row entry.',
        ),
        spec(
            'matrix_recursive_cofactor_streams_from_functionality',
            f"forall {' '.join(parents)} q eb ec fb fc ub uc vb vc. ({_functional_property('q','cofactor_recursion')}) -> "
            f"({_matrix_equal(*parents,'S q','cofactor_parents')}) -> ({_cofactors('pb','pc','nb','nc','q','eb','ec','fb','fc','cofactor_left')}) -> "
            f"({_cofactors('qb','qc','rb','rc','q','ub','uc','vb','vc','cofactor_right')}) -> "
            +_and(_prefix('eb','ec','ub','uc','S q','cofactor_equal_positive'),_prefix('fb','fc','vb','vc','S q','cofactor_equal_negative')),
            ('beta_at_unique','matrix_recursive_signed_minor_extensional'),
            _intro(*parents,'q','eb','ec','fb','fc','ub','uc','vb','vc','hrecursion','hparent','hcofirst','hcosecond')
            +('split',)+cofactor_stream_component(False)+cofactor_stream_component(True),
            'Genuine determinant functionality in dimension q makes every corresponding evaluated first-row cofactor stream of equal (q+1)-matrices pointwise equal.',
        ),
        spec(
            'matrix_recursive_determinant_extensional',
            f"forall d. ({_functional_property('d','all_extensional')})",
            ('signed_recursive_determinant_zero_value','signed_recursive_determinant_successor_decomposition',
             'matrix_recursive_cofactor_streams_from_functionality','matrix_recursive_initial_row_prefix',
             'matrix_recursive_alternating_fold_extensional'),
            ('induction d',)+_intro(*parents,'p','n','r','s','hmatrix','hfirst','hsecond')
            +('have hzeroa : p = 1 /\\ n = 0',)
            +_apply('signed_recursive_determinant_zero_value','pb','pc','nb','nc','p','n')+('exact hfirst','cases hzeroa')
            +('have hzerob : r = 1 /\\ s = 0',)
            +_apply('signed_recursive_determinant_zero_value','qb','qc','rb','rc','r','s')+('exact hsecond','cases hzerob')
            +('split','trans 1','exact hzeroa_left','symm','exact hzerob_left','trans 0','exact hzeroa_right','symm','exact hzerob_right')
            +_intro(*parents,'p','n','r','s','hmatrix','hfirst','hsecond')
            +(f"have hfa : exists eb ec fb fc. {_and(_cofactors('pb','pc','nb','nc','d','eb','ec','fb','fc','functionality_first_cofactors'),_fold_terms('pb','pc','nb','nc','eb','ec','fb','fc','S d','p','n',tag='mdre_functionality_first_fold'))}",)
            +_apply('signed_recursive_determinant_successor_decomposition','pb','pc','nb','nc','d','p','n')+('exact hfirst',)
            +_cases('hfa',4)+_parts('hfa'+'_witness'*4,2)
            +(f"have hfb : exists eb ec fb fc. {_and(_cofactors('qb','qc','rb','rc','d','eb','ec','fb','fc','functionality_second_cofactors'),_fold_terms('qb','qc','rb','rc','eb','ec','fb','fc','S d','r','s',tag='mdre_functionality_second_fold'))}",)
            +_apply('signed_recursive_determinant_successor_decomposition','qb','qc','rb','rc','d','r','s')+('exact hsecond',)
            +_cases('hfb',4)+_parts('hfb'+'_witness'*4,2)
            +(f"have hstreams : {_and(_prefix('x','x1','x4','x5','S d','functional_stream_positive'),_prefix('x2','x3','x6','x7','S d','functional_stream_negative'))}",)
            +_apply('matrix_recursive_cofactor_streams_from_functionality',*parents,'d','x','x1','x2','x3','x4','x5','x6','x7')
            +('exact IH','exact hmatrix',f"exact hfa{'_witness'*4}_left",f"exact hfb{'_witness'*4}_left",'cases hstreams','cases hmatrix')
            +_apply('matrix_recursive_alternating_fold_extensional','pb','pc','nb','nc','x','x1','x2','x3','qb','qc','rb','rc','x4','x5','x6','x7','S d','p','n','r','s')
            +_apply('matrix_recursive_initial_row_prefix','pb','pc','qb','qc','d')+('exact hmatrix_left',)
            +_apply('matrix_recursive_initial_row_prefix','nb','nc','rb','rc','d')+('exact hmatrix_right','exact hstreams_left','exact hstreams_right',f"exact hfa{'_witness'*4}_right",f"exact hfb{'_witness'*4}_right"),
            'Unrestricted HA induction proves exact determinant-component equality for any two actual pointwise-equal signed matrices, across arbitrary finite evaluation histories and arbitrary beta recodings.',
        ),
        spec(
            'signed_recursive_determinant_functional',
            f"forall pb pc nb nc d p n r s. ({_det('pb','pc','nb','nc','d','p','n','functional_first')}) -> "
            f"({_det('pb','pc','nb','nc','d','r','s','functional_second')}) -> p = r /\\ n = s",
            ('matrix_recursive_determinant_extensional','matrix_recursive_matrix_equality_refl'),
            _intro('pb','pc','nb','nc','d','p','n','r','s','hfirst','hsecond')
            +_apply('matrix_recursive_determinant_extensional','d','pb','pc','nb','nc','pb','pc','nb','nc','p','n','r','s')
            +_apply('matrix_recursive_matrix_equality_refl','pb','pc','nb','nc','d')+('exact hfirst','exact hsecond'),
            'Every actual signed matrix has unique recursive cofactor components, independently of the size, layout, or codes of its valid evaluation history.',
        ),
        spec(
            'signed_recursive_determinant_exists_unique',
            f"forall pb pc nb nc d. exists p n. {unique_result}",
            ('signed_recursive_determinant_exists','signed_recursive_determinant_functional'),
            _intro('pb','pc','nb','nc','d')
            +(f"have hvalue : exists p n. ({_det('pb','pc','nb','nc','d','p','n','unique_existence')})",)
            +_apply('signed_recursive_determinant_exists','pb','pc','nb','nc','d')+_cases('hvalue',2)
            +_exists('x','x1')+('split','exact hvalue_witness_witness')+_intro('r','s','hother')
            +_apply('signed_recursive_determinant_functional','pb','pc','nb','nc','d','r','s','x','x1')
            +('exact hother','exact hvalue_witness_witness'),
            'Every unrestricted-dimensional signed beta-coded square matrix has exactly one positive/negative recursive determinant pair, with both existence and cross-history functionality proved.',
        ),
        spec(
            'signed_recursive_determinant_from_evaluated_cofactors',
            f"forall pb pc nb nc q eb ec fb fc p n. ({_cofactors('pb','pc','nb','nc','q','eb','ec','fb','fc','given_cofactors')}) -> "
            f"({_fold_terms('pb','pc','nb','nc','eb','ec','fb','fc','S q','p','n',tag='mdre_given_fold')}) -> ({successor_det})",
            ('signed_recursive_determinant_exists','signed_recursive_determinant_successor_decomposition',
             'matrix_recursive_cofactor_streams_from_functionality','matrix_recursive_determinant_extensional',
             'matrix_recursive_matrix_equality_refl','matrix_recursive_prefix_refl','matrix_recursive_alternating_fold_extensional'),
            _intro('pb','pc','nb','nc','q','eb','ec','fb','fc','p','n','hcofactors','hfold')
            +(f"have hvalue : exists r s. ({_det('pb','pc','nb','nc','S q','r','s','constructed_parent')})",)
            +_apply('signed_recursive_determinant_exists','pb','pc','nb','nc','S q')+_cases('hvalue',2)
            +(f"have hcanonical : exists ub uc vb vc. {_and(_cofactors('pb','pc','nb','nc','q','ub','uc','vb','vc','canonical_cofactors'),_fold_terms('pb','pc','nb','nc','ub','uc','vb','vc','S q','x','x1',tag='mdre_canonical_fold'))}",)
            +_apply('signed_recursive_determinant_successor_decomposition','pb','pc','nb','nc','q','x','x1')
            +('exact hvalue_witness_witness',)+_cases('hcanonical',4)+_parts('hcanonical'+'_witness'*4,2)
            +(f"have hstreams : {_and(_prefix('eb','ec','x2','x3','S q','canonical_positive'),_prefix('fb','fc','x4','x5','S q','canonical_negative'))}",)
            +_apply('matrix_recursive_cofactor_streams_from_functionality','pb','pc','nb','nc','pb','pc','nb','nc','q','eb','ec','fb','fc','x2','x3','x4','x5')
            +_apply('matrix_recursive_determinant_extensional','q')
            +_apply('matrix_recursive_matrix_equality_refl','pb','pc','nb','nc','S q')
            +('exact hcofactors',f"exact hcanonical{'_witness'*4}_left",'cases hstreams')
            +('have hvalues : p = x /\\ n = x1',)
            +_apply('matrix_recursive_alternating_fold_extensional','pb','pc','nb','nc','eb','ec','fb','fc','pb','pc','nb','nc','x2','x3','x4','x5','S q','p','n','x','x1')
            +_apply('matrix_recursive_prefix_refl','pb','pc','S q')
            +_apply('matrix_recursive_prefix_refl','nb','nc','S q')
            +('exact hstreams_left','exact hstreams_right','exact hfold',f"exact hcanonical{'_witness'*4}_right",'cases hvalues')
            +_rewrite_all('hvalues_left','p',successor_det)+_rewrite_all('hvalues_right','n',successor_det)
            +('exact hvalue_witness_witness',),
            'A parity-correct fold over every genuinely evaluated actual minor is the determinant: existence supplies a genuine parent history and proved extensional functionality identifies its value.',
        ),
        spec(
            'signed_recursive_determinant_cofactor_equation',
            f"forall pb pc nb nc q p n. {_and(f'({successor_det}) -> ({cofactor_equation_rhs})',f'({cofactor_equation_rhs}) -> ({successor_det})')}",
            ('signed_recursive_determinant_successor_decomposition','signed_recursive_determinant_from_evaluated_cofactors'),
            _intro('pb','pc','nb','nc','q','p','n')+('split','intro hdeterminant')
            +_apply('signed_recursive_determinant_successor_decomposition','pb','pc','nb','nc','q','p','n')
            +('exact hdeterminant','intro hcofactors')+_cases('hcofactors',4)+_parts('hcofactors'+'_witness'*4,2)
            +_apply('signed_recursive_determinant_from_evaluated_cofactors','pb','pc','nb','nc','q','x','x1','x2','x3','p','n')
            +(f"exact hcofactors{'_witness'*4}_left",f"exact hcofactors{'_witness'*4}_right"),
            'For every natural dimension, a nonempty determinant is equivalent to its genuine first-row recursive cofactor equation, in both directions and without a supplied-determinant assumption.',
        ),
        spec(
            'signed_recursive_determinant_empty',
            f"forall pb pc nb nc. ({_det('pb','pc','nb','nc','0','1','0','exact_empty')})",
            ('le_refl','matrix_recursive_empty_history','matrix_recursive_history_extend'),
            _intro('pb','pc','nb','nc')
            +(f"have hext : exists u v. {_and(_prefix('0','0','u','v','0','empty_prefix'),_history('u','v','1','empty_history'),_record('u','v','0','0','pb','pc','nb','nc','1','0','empty_record'))}",)
            +_apply('matrix_recursive_history_extend','0','0','0','0','pb','pc','nb','nc','1','0')
            +_apply('matrix_recursive_empty_history','0','0')+('left','split','refl','split','refl','refl')
            +_cases('hext',2)+_parts('hext_witness_witness',3)+_exists('x','x1','1','0')
            +('split',f"exact {_part('hext_witness_witness',3,1)}",'split','apply le_refl',f"exact {_part('hext_witness_witness',3,2)}"),
            'The empty square matrix has an explicit valid one-node determinant history with value (1,0).',
        ),
        spec(
            'signed_recursive_determinant_empty_equation',
            f"forall pb pc nb nc p n. {empty_equation}",
            ('signed_recursive_determinant_zero_value','signed_recursive_determinant_empty'),
            _intro('pb','pc','nb','nc','p','n')+('split','intro hdeterminant')
            +_apply('signed_recursive_determinant_zero_value','pb','pc','nb','nc','p','n')
            +('exact hdeterminant','intro hvalues','cases hvalues')
            +_rewrite_all('hvalues_left','p',empty_det)+_rewrite_all('hvalues_right','n',empty_det)
            +_apply('signed_recursive_determinant_empty','pb','pc','nb','nc'),
            'The exact zero-dimensional determinant equation is an iff, including arbitrary input beta codes and both output components.',
        ),
    )


__all__ = [
    'signed_matrix_prefix_equality_relation',
    'make_matrix_recursive_determinant_extensional_candidate_theorems',
]
