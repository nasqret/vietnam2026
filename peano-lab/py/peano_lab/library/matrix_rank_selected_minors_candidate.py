"""Actual arbitrary selected submatrices and their recursive determinants.

The row and column streams select genuine entries of a row-major parent
matrix. Distinctness and ambient bounds belong to the separate selector
relation; no supplied numerical table is accepted as a determinant.
"""

from __future__ import annotations

from typing import Any, Callable

from .matrix_recursive_determinant_candidate import (
    _and, _apply, _at, _cases, _det, _exists, _intro, _le, _lt,
    _names, _part, _parts, _prefix, _rewrite_all, _safe,
)
from .matrix_recursive_determinant_extensional_candidate import _matrix_equal
from .matrix_rank_finite_coding_candidate import _arguments, _selector


def _point(b: str, c: str, w: str, rb: str, rc: str, cb: str, cc: str, q: str, i: str, a: str, tag: str) -> str:
    r,s,u,v = _names(tag,'r','s','u','v')
    return f'exists {r} {s} {u} {v}. '+_and(
        f'{i} = ({q}) * {r} + {s}',_lt(s,q,tag+'column'),
        _at(rb,rc,r,u,tag+'row_index'),_at(cb,cc,s,v,tag+'column_index'),
        _at(b,c,f'({u}) * ({w}) + ({v})',a,tag+'source'),
    )


def _selected_prefix(b: str, c: str, w: str, rb: str, rc: str, cb: str, cc: str, q: str, ub: str, uc: str, length: str, tag: str) -> str:
    i,a = _names(tag,'i','a')
    return (
        f'forall {i}. ({_lt(i,length,tag+"bound")}) -> exists {a}. '
        f'({_and(_point(b,c,w,rb,rc,cb,cc,q,i,a,tag+"point"),_at(ub,uc,i,a,tag+"output"))})'
    )


def _selected(pb: str, pc: str, nb: str, nc: str, w: str, rb: str, rc: str, cb: str, cc: str, q: str, ub: str, uc: str, vb: str, vc: str, tag: str) -> str:
    return _and(
        _selected_prefix(pb,pc,w,rb,rc,cb,cc,q,ub,uc,f'({q}) * ({q})',tag+'positive'),
        _selected_prefix(nb,nc,w,rb,rc,cb,cc,q,vb,vc,f'({q}) * ({q})',tag+'negative'),
    )


def signed_selected_submatrix_relation(pb: str, pc: str, nb: str, nc: str, w: str, rb: str, rc: str, cb: str, cc: str, q: str, ub: str, uc: str, vb: str, vc: str, *, tag: str) -> str:
    """Every entry of a genuine arbitrary selected square submatrix."""
    return _selected(*_arguments(pb,pc,nb,nc,w,rb,rc,cb,cc,q,ub,uc,vb,vc),_safe(tag))


def _selected_det(pb: str, pc: str, nb: str, nc: str, w: str, rb: str, rc: str, cb: str, cc: str, q: str, p: str, n: str, tag: str) -> str:
    ub,uc,vb,vc = _names(tag,'ub','uc','vb','vc')
    return f'exists {ub} {uc} {vb} {vc}. '+_and(
        _selected(pb,pc,nb,nc,w,rb,rc,cb,cc,q,ub,uc,vb,vc,tag+'matrix'),
        _det(ub,uc,vb,vc,q,p,n,tag+'determinant'),
    )


def signed_selected_determinant_relation(pb: str, pc: str, nb: str, nc: str, w: str, rb: str, rc: str, cb: str, cc: str, q: str, p: str, n: str, *, tag: str) -> str:
    """An actual unrestricted-dimensional determinant of a selected submatrix."""
    return _selected_det(*_arguments(pb,pc,nb,nc,w,rb,rc,cb,cc,q,p,n),_safe(tag))


def _nonzero_value(pb: str, pc: str, nb: str, nc: str, w: str, rb: str, rc: str, cb: str, cc: str, q: str, tag: str) -> str:
    p,n = _names(tag,'p','n')
    return f'exists {p} {n}. '+_and(_selected_det(pb,pc,nb,nc,w,rb,rc,cb,cc,q,p,n,tag+'evaluation'),f'~({p} = {n})')


def _nonzero_selected(pb: str, pc: str, nb: str, nc: str, r: str, w: str, q: str, rb: str, rc: str, cb: str, cc: str, tag: str) -> str:
    return _and(
        _selector(rb,rc,q,r,tag+'rows'),_selector(cb,cc,q,w,tag+'columns'),
        _nonzero_value(pb,pc,nb,nc,w,rb,rc,cb,cc,q,tag+'nonzero'),
    )


def _nonzero_minor(pb: str, pc: str, nb: str, nc: str, r: str, w: str, q: str, tag: str) -> str:
    rb,rc,cb,cc = _names(tag,'rb','rc','cb','cc')
    return f'exists {rb} {rc} {cb} {cc}. ({_nonzero_selected(pb,pc,nb,nc,r,w,q,rb,rc,cb,cc,tag+"minor")})'


def nonzero_selected_minor_relation(pb: str, pc: str, nb: str, nc: str, r: str, w: str, q: str, rb: str, rc: str, cb: str, cc: str, *, tag: str) -> str:
    """Distinct, bounded selectors and an actual nonzero evaluated minor."""
    return _nonzero_selected(*_arguments(pb,pc,nb,nc,r,w,q,rb,rc,cb,cc),_safe(tag))


def nonzero_matrix_minor_relation(pb: str, pc: str, nb: str, nc: str, r: str, w: str, q: str, *, tag: str) -> str:
    """The given rectangular matrix has a genuine nonzero minor of order q."""
    return _nonzero_minor(*_arguments(pb,pc,nb,nc,r,w,q),_safe(tag))


def make_matrix_rank_selected_minors_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    natural = ('b','c','w','rb','rc','cb','cc','q')
    signed = ('pb','pc','nb','nc','w','rb','rc','cb','cc','q')
    nonzero = ('pb','pc','nb','nc','r','w','q','rb','rc','cb','cc')
    matrix = ('pb','pc','nb','nc','r','w')
    recoded_natural = ('b','c','w','Rb','Rc','Cb','Cc','q')
    recoded_signed = ('pb','pc','nb','nc','w','Rb','Rc','Cb','Cc','q')
    recoded_nonzero = ('pb','pc','nb','nc','r','w','q','Rb','Rc','Cb','Cc')
    hfirst = 'hfirst'+'_witness'*4
    hsecond = 'hsecond'+'_witness'*4
    return (
        spec(
            'matrix_rank_selected_point_exists',
            f"forall {' '.join(natural)} i. ~(q = 0) -> exists a. ({_point(*natural,'i','a','point_exists')})",
            ('division_remainder_exists','beta_at_exists'),
            _intro(*natural,'i','hq')
            +(f"have hcoordinates : exists r s. i = q * r + s /\\ ({_lt('s','q','point_column')})",)
            +_apply('division_remainder_exists','q','i')+('exact hq',)+_cases('hcoordinates',2)+('cases hcoordinates_witness_witness',)
            +(f"have hrow : exists u. {_at('rb','rc','x','u','selected_row')}",)
            +_apply('beta_at_exists','rb','rc','x')+('cases hrow',)
            +(f"have hcolumn : exists v. {_at('cb','cc','x1','v','selected_column')}",)
            +_apply('beta_at_exists','cb','cc','x1')+('cases hcolumn',)
            +(f"have hentry : exists a. {_at('b','c','x2 * w + x3','a','selected_source')}",)
            +_apply('beta_at_exists','b','c','x2 * w + x3')+('cases hentry',)
            +_exists('x4','x','x1','x2','x3')
            +('split','exact hcoordinates_witness_witness_left','split','exact hcoordinates_witness_witness_right',
              'split','exact hrow_witness','split','exact hcolumn_witness','exact hentry_witness'),
            'Decode a genuine row selector, column selector, and parent entry at every flattened selected-matrix index.',
        ),
        spec(
            'matrix_rank_selected_point_functional',
            f"forall {' '.join(natural)} i a A. ({_point(*natural,'i','a','point_first')}) -> ({_point(*natural,'i','A','point_second')}) -> a = A",
            ('division_remainder_unique','beta_at_unique'),
            _intro(*natural,'i','a','A','hfirst','hsecond')+_cases('hfirst',4)+_parts(hfirst,5)+_cases('hsecond',4)+_parts(hsecond,5)
            +('have hcoordinates : x = x4 /\\ x1 = x5',)+_apply('division_remainder_unique','q','i','x','x1','x4','x5')
            +tuple(f'exact {_part(h,count,index)}' for h,count,index in ((hfirst,5,0),(hfirst,5,1),(hsecond,5,0),(hsecond,5,1)))
            +('cases hcoordinates','have hrow : x2 = x6')+_apply('beta_at_unique','rb','rc','x','x2','x6')
            +(f'exact {_part(hfirst,5,2)}',)+_rewrite_all('hcoordinates_left','x',_at('rb','rc','x','x6','align_row'))+(f'exact {_part(hsecond,5,2)}',)
            +('have hcolumn : x3 = x7',)+_apply('beta_at_unique','cb','cc','x1','x3','x7')
            +(f'exact {_part(hfirst,5,3)}',)+_rewrite_all('hcoordinates_right','x1',_at('cb','cc','x1','x7','align_column'))+(f'exact {_part(hsecond,5,3)}',)
            +_apply('beta_at_unique','b','c','x2 * w + x3','a','A')+(f'exact {_part(hfirst,5,4)}',)
            +_rewrite_all('hrow','x2',_at('b','c','x2 * w + x3','A','align_parent_row'))
            +_rewrite_all('hcolumn','x3',_at('b','c','x6 * w + x3','A','align_parent_column'))+(f'exact {_part(hsecond,5,4)}',),
            'Actual selected-matrix cells are functional, by quotient/remainder uniqueness and three genuine beta-decoding uniqueness arguments.',
        ),
        spec(
            'matrix_rank_selected_prefix_empty',
            f"forall {' '.join(natural)} ub uc. ({_selected_prefix(*natural,'ub','uc','0','empty_prefix')})",
            ('matrix_rank_no_index_below_zero',),
            _intro(*natural,'ub','uc','i','hi')+('exfalso',)+_apply('matrix_rank_no_index_below_zero','i')+('exact hi',),
            'Every code witnesses the actual selected-submatrix prefix of length zero.',
        ),
        spec(
            'matrix_rank_selected_prefix_extend',
            f"forall {' '.join(natural)} ub uc l a. ({_selected_prefix(*natural,'ub','uc','l','prefix_previous')}) -> "
            f"({_point(*natural,'l','a','prefix_last')}) -> exists vb vc. ({_selected_prefix(*natural,'vb','vc','S l','prefix_successor')})",
            ('beta_prefix_extend','finite_lt_succ_eq_or_lt'),
            _intro(*natural,'ub','uc','l','a','hprevious','hpoint')
            +(f"have hcode : exists vb vc. {_and(_at('vb','vc','l','a','new_entry'),_prefix('ub','uc','vb','vc','l','old_entries'))}",)
            +_apply('beta_prefix_extend','l','ub','uc','a')+_cases('hcode',2)+('cases hcode_witness_witness',)
            +_exists('x','x1')+_intro('i','hi')
            +(f"have hindex : i = l \\/ ({_lt('i','l','old_index')})",)
            +_apply('finite_lt_succ_eq_or_lt','l','i')+('exact hi','cases hindex','exists a','split')
            +_rewrite_all('hindex_left','i',_point(*natural,'i','a','new_point'))+('exact hpoint',)
            +_rewrite_all('hindex_left','i',_at('x','x1','i','a','new_output'))+('exact hcode_witness_witness_left',)
            +(f"have hold : exists z. {_and(_point(*natural,'i','z','old_point'),_at('ub','uc','i','z','old_output'))}",)
            +_apply('hprevious','i')+('exact hindex_right','cases hold','cases hold_witness','exists x2','split','exact hold_witness_left')
            +_apply('hcode_witness_witness_right','i','x2')+('exact hindex_right','exact hold_witness_right'),
            'Append one actual selected parent entry while preserving every earlier selected entry in the same new beta code.',
        ),
        spec(
            'matrix_rank_selected_prefix_exists_nonzero',
            f"forall {' '.join(natural)} l. ~(q = 0) -> exists ub uc. ({_selected_prefix(*natural,'ub','uc','l','prefix_exists')})",
            ('matrix_rank_selected_prefix_empty','matrix_rank_selected_point_exists','matrix_rank_selected_prefix_extend'),
            _intro(*natural)+('induction l','intro hq',)+_exists('0','0')+_apply('matrix_rank_selected_prefix_empty',*natural,'0','0')
            +('intro hq',f"have hprevious : exists ub uc. ({_selected_prefix(*natural,'ub','uc','l','prefix_previous_exists')})")
            +('apply IH','exact hq')+_cases('hprevious',2)
            +(f"have hpoint : exists a. {_point(*natural,'l','a','next_point_exists')}",)
            +_apply('matrix_rank_selected_point_exists',*natural,'l')+('exact hq','cases hpoint')
            +_apply('matrix_rank_selected_prefix_extend',*natural,'x','x1','l','x2')+('exact hprevious_witness_witness','exact hpoint_witness'),
            'HA induction constructs arbitrary finite prefixes of actual selected matrices whenever the selected row width is positive.',
        ),
        spec(
            'matrix_rank_selected_square_exists',
            f"forall {' '.join(natural)}. exists ub uc. ({_selected_prefix(*natural,'ub','uc','q * q','square_exists')})",
            ('eq_decidable','matrix_rank_selected_prefix_empty','matrix_rank_selected_prefix_exists_nonzero'),
            _intro(*natural)+('specialize eq_decidable q','specialize eq_decidable 0','cases eq_decidable')
            +('have hlength : q * q = 0','rewrite eq_decidable_left','rewrite eq_decidable_left','apply PA5','rewrite hlength')
            +_exists('0','0')+_apply('matrix_rank_selected_prefix_empty',*natural,'0','0')
            +_apply('matrix_rank_selected_prefix_exists_nonzero',*natural,'q * q')+('exact eq_decidable_right',),
            'Every arbitrary selected square submatrix has a complete actual beta code, including dimension zero.',
        ),
        spec(
            'matrix_rank_signed_selected_square_exists',
            f"forall {' '.join(signed)}. exists ub uc vb vc. ({_selected(*signed,'ub','uc','vb','vc','signed_square_exists')})",
            ('matrix_rank_selected_square_exists',),
            _intro(*signed)
            +(f"have hpositive : exists u v. {_selected_prefix('pb','pc','w','rb','rc','cb','cc','q','u','v','q * q','positive_exists')}",)
            +_apply('matrix_rank_selected_square_exists','pb','pc','w','rb','rc','cb','cc','q')+_cases('hpositive',2)
            +(f"have hnegative : exists u v. {_selected_prefix('nb','nc','w','rb','rc','cb','cc','q','u','v','q * q','negative_exists')}",)
            +_apply('matrix_rank_selected_square_exists','nb','nc','w','rb','rc','cb','cc','q')+_cases('hnegative',2)
            +_exists('x','x1','x2','x3')+('split','exact hpositive_witness_witness','exact hnegative_witness_witness'),
            'Construct both genuine natural-component streams of an arbitrary signed selected square matrix.',
        ),
        spec(
            'matrix_rank_selected_prefix_functional',
            f"forall {' '.join(natural)} ub uc vb vc. ({_selected_prefix(*natural,'ub','uc','q * q','first_prefix')}) -> "
            f"({_selected_prefix(*natural,'vb','vc','q * q','second_prefix')}) -> ({_prefix('ub','uc','vb','vc','q * q','prefix_unique')})",
            ('matrix_rank_selected_point_functional','beta_at_unique'),
            _intro(*natural,'ub','uc','vb','vc','hfirst','hsecond','i','a','hi','ha')
            +(f"have hleft : exists z. {_and(_point(*natural,'i','z','first_cell'),_at('ub','uc','i','z','first_output'))}",)
            +_apply('hfirst','i')+('exact hi','cases hleft','cases hleft_witness')
            +(f"have hright : exists z. {_and(_point(*natural,'i','z','second_cell'),_at('vb','vc','i','z','second_output'))}",)
            +_apply('hsecond','i')+('exact hi','cases hright','cases hright_witness','have hvalues : x = x1')
            +_apply('matrix_rank_selected_point_functional',*natural,'i','x','x1')+('exact hleft_witness_left','exact hright_witness_left','have houtput : a = x1','trans x')
            +_apply('beta_at_unique','ub','uc','i','a','x')+('exact ha','exact hleft_witness_right','exact hvalues')
            +_rewrite_all('houtput','a',_at('vb','vc','i','a','unique_output'))+('exact hright_witness_right',),
            'Any two codes of the same actual selected square agree on every finite entry.',
        ),
        spec(
            'matrix_rank_signed_selected_square_functional',
            f"forall {' '.join(signed)} ub uc vb vc Ub Uc Vb Vc. ({_selected(*signed,'ub','uc','vb','vc','first_selected')}) -> "
            f"({_selected(*signed,'Ub','Uc','Vb','Vc','second_selected')}) -> ({_matrix_equal('ub','uc','vb','vc','Ub','Uc','Vb','Vc','q','signed_selected_equal')})",
            ('matrix_rank_selected_prefix_functional',),
            _intro(*signed,'ub','uc','vb','vc','Ub','Uc','Vb','Vc','hfirst','hsecond')+('cases hfirst','cases hsecond','split')
            +_apply('matrix_rank_selected_prefix_functional','pb','pc','w','rb','rc','cb','cc','q','ub','uc','Ub','Uc')+('exact hfirst_left','exact hsecond_left')
            +_apply('matrix_rank_selected_prefix_functional','nb','nc','w','rb','rc','cb','cc','q','vb','vc','Vb','Vc')+('exact hfirst_right','exact hsecond_right'),
            'Both signed components of any two genuine selected-submatrix encodings are extensionally identical.',
        ),
        spec(
            'matrix_rank_selected_determinant_exists',
            f"forall {' '.join(signed)}. exists p n. ({_selected_det(*signed,'p','n','selected_det_exists')})",
            ('matrix_rank_signed_selected_square_exists','signed_recursive_determinant_exists'),
            _intro(*signed)
            +(f"have hmatrix : exists ub uc vb vc. ({_selected(*signed,'ub','uc','vb','vc','selected_matrix_exists')})",)
            +_apply('matrix_rank_signed_selected_square_exists',*signed)+_cases('hmatrix',4)
            +(f"have hdet : exists p n. ({_det('x','x1','x2','x3','q','p','n','selected_evaluation_exists')})",)
            +_apply('signed_recursive_determinant_exists','x','x1','x2','x3','q')+_cases('hdet',2)
            +_exists('x4','x5','x','x1','x2','x3')+('split','exact hmatrix_witness_witness_witness_witness','exact hdet_witness_witness'),
            'Every genuinely selected submatrix has an actual unrestricted-dimensional recursively evaluated signed determinant.',
        ),
        spec(
            'matrix_rank_selected_determinant_functional',
            f"forall {' '.join(signed)} p n P N. ({_selected_det(*signed,'p','n','selected_det_first')}) -> "
            f"({_selected_det(*signed,'P','N','selected_det_second')}) -> p = P /\\ n = N",
            ('matrix_rank_signed_selected_square_functional','matrix_recursive_determinant_extensional'),
            _intro(*signed,'p','n','P','N','hfirst','hsecond')+_cases('hfirst',4)+('cases '+hfirst,)+_cases('hsecond',4)+('cases '+hsecond,)
            +_apply('matrix_recursive_determinant_extensional','q','x','x1','x2','x3','x4','x5','x6','x7','p','n','P','N')
            +_apply('matrix_rank_signed_selected_square_functional',*signed,'x','x1','x2','x3','x4','x5','x6','x7')
            +(f'exact {hfirst}_left',f'exact {hsecond}_left',f'exact {hfirst}_right',f'exact {hsecond}_right'),
            'Actual selected-minor determinant values are functional even across different finite submatrix and evaluation-history encodings.',
        ),
        spec(
            'matrix_rank_selected_point_selector_transport',
            f"forall {' '.join(natural)} Rb Rc Cb Cc i a. ({_prefix('rb','rc','Rb','Rc','q','point_rows')}) -> "
            f"({_prefix('cb','cc','Cb','Cc','q','point_columns')}) -> ({_lt('i','q * q','point_index')}) -> "
            f"({_point(*natural,'i','a','point_source')}) -> ({_point(*recoded_natural,'i','a','point_target')})",
            ('matrix_recursive_quotient_row_bound',),
            _intro(*natural,'Rb','Rc','Cb','Cc','i','a','hrows','hcolumns','hi','hpoint')+_cases('hpoint',4)+_parts('hpoint'+'_witness'*4,5)
            +(f"have hr : {_lt('x','q','transport_row_bound')}",)
            +_apply('matrix_recursive_quotient_row_bound','q','i','x','x1')+(f"exact {_part('hpoint'+'_witness'*4,5,0)}",'exact hi')
            +_exists('x','x1','x2','x3')
            +('split',f"exact {_part('hpoint'+'_witness'*4,5,0)}",'split',f"exact {_part('hpoint'+'_witness'*4,5,1)}",'split')
            +_apply('hrows','x','x2')+('exact hr',f"exact {_part('hpoint'+'_witness'*4,5,2)}",'split')
            +_apply('hcolumns','x1','x3')+(f"exact {_part('hpoint'+'_witness'*4,5,1)}",f"exact {_part('hpoint'+'_witness'*4,5,3)}",f"exact {_part('hpoint'+'_witness'*4,5,4)}"),
            'The genuine source cell is unchanged by extensionally equal finite row and column selectors; both selector coordinates are proved in range.',
        ),
        spec(
            'matrix_rank_selected_prefix_selector_transport',
            f"forall {' '.join(natural)} Rb Rc Cb Cc ub uc. ({_prefix('rb','rc','Rb','Rc','q','prefix_rows')}) -> "
            f"({_prefix('cb','cc','Cb','Cc','q','prefix_columns')}) -> ({_selected_prefix(*natural,'ub','uc','q * q','selected_prefix_source')}) -> "
            f"({_selected_prefix(*recoded_natural,'ub','uc','q * q','selected_prefix_target')})",
            ('matrix_rank_selected_point_selector_transport',),
            _intro(*natural,'Rb','Rc','Cb','Cc','ub','uc','hrows','hcolumns','hselected','i','hi')
            +(f"have hentry : exists a. {_and(_point(*natural,'i','a','transported_point'),_at('ub','uc','i','a','transported_output'))}",)
            +_apply('hselected','i')+('exact hi','cases hentry','cases hentry_witness','exists x','split')
            +_apply('matrix_rank_selected_point_selector_transport',*natural,'Rb','Rc','Cb','Cc','i','x')
            +('exact hrows','exact hcolumns','exact hi','exact hentry_witness_left','exact hentry_witness_right'),
            'A complete actual selected-submatrix code remains valid under equality-preserving selector recoding.',
        ),
        spec(
            'matrix_rank_signed_selected_selector_transport',
            f"forall {' '.join(signed)} Rb Rc Cb Cc ub uc vb vc. ({_prefix('rb','rc','Rb','Rc','q','signed_rows')}) -> "
            f"({_prefix('cb','cc','Cb','Cc','q','signed_columns')}) -> ({_selected(*signed,'ub','uc','vb','vc','signed_selected_source')}) -> "
            f"({_selected(*recoded_signed,'ub','uc','vb','vc','signed_selected_target')})",
            ('matrix_rank_selected_prefix_selector_transport',),
            _intro(*signed,'Rb','Rc','Cb','Cc','ub','uc','vb','vc','hrows','hcolumns','hselected')+('cases hselected','split')
            +_apply('matrix_rank_selected_prefix_selector_transport','pb','pc','w','rb','rc','cb','cc','q','Rb','Rc','Cb','Cc','ub','uc')
            +('exact hrows','exact hcolumns','exact hselected_left')
            +_apply('matrix_rank_selected_prefix_selector_transport','nb','nc','w','rb','rc','cb','cc','q','Rb','Rc','Cb','Cc','vb','vc')
            +('exact hrows','exact hcolumns','exact hselected_right'),
            'Both signed component matrices transport across complete finite selector recoding.',
        ),
        spec(
            'matrix_rank_selected_determinant_selector_transport',
            f"forall {' '.join(signed)} Rb Rc Cb Cc p n. ({_prefix('rb','rc','Rb','Rc','q','det_rows')}) -> "
            f"({_prefix('cb','cc','Cb','Cc','q','det_columns')}) -> ({_selected_det(*signed,'p','n','selected_det_source')}) -> "
            f"({_selected_det(*recoded_signed,'p','n','selected_det_target')})",
            ('matrix_rank_signed_selected_selector_transport',),
            _intro(*signed,'Rb','Rc','Cb','Cc','p','n','hrows','hcolumns','hdet')+_cases('hdet',4)+('cases '+'hdet'+'_witness'*4,)
            +_exists('x','x1','x2','x3')+('split',)
            +_apply('matrix_rank_signed_selected_selector_transport',*signed,'Rb','Rc','Cb','Cc','x','x1','x2','x3')
            +('exact hrows','exact hcolumns','exact hdet_witness_witness_witness_witness_left','exact hdet_witness_witness_witness_witness_right'),
            'Recoding selectors preserves the same actual determinant history and its exact signed output pair.',
        ),
        spec(
            'matrix_rank_selected_nonzero_value_decidable',
            f"forall {' '.join(signed)}. ({_nonzero_value(*signed,'nonzero_value_yes')}) \\/ ~({_nonzero_value(*signed,'nonzero_value_no')})",
            ('matrix_rank_selected_determinant_exists','matrix_rank_selected_determinant_functional','eq_decidable'),
            _intro(*signed)
            +(f"have hvalue : exists p n. {_selected_det(*signed,'p','n','decidable_evaluation')}",)
            +_apply('matrix_rank_selected_determinant_exists',*signed)+_cases('hvalue',2)
            +('specialize eq_decidable x','specialize eq_decidable x1','cases eq_decidable','right','intro hnonzero')
            +_cases('hnonzero',2)+('cases hnonzero_witness_witness','have hvalues : x = x2 /\\ x1 = x3')
            +_apply('matrix_rank_selected_determinant_functional',*signed,'x','x1','x2','x3')
            +('exact hvalue_witness_witness','exact hnonzero_witness_witness_left','cases hvalues','apply hnonzero_witness_witness_right','trans x','symm','exact hvalues_left','trans x1','exact eq_decidable_left','exact hvalues_right')
            +('left',)+_exists('x','x1')+('split','exact hvalue_witness_witness','exact eq_decidable_right'),
            'Nonzeroness of a genuinely evaluated selected determinant is decidable by total evaluation and cross-history functionality.',
        ),
        spec(
            'matrix_rank_nonzero_selected_minor_decidable',
            f"forall {' '.join(nonzero)}. ({_nonzero_selected(*nonzero,'minor_yes')}) \\/ ~({_nonzero_selected(*nonzero,'minor_no')})",
            ('matrix_rank_selector_decidable','matrix_rank_selected_nonzero_value_decidable'),
            _intro(*nonzero)
            +(f"have hrows : ({_selector('rb','rc','q','r','rows_yes')}) \\/ ~({_selector('rb','rc','q','r','rows_no')})",)
            +_apply('matrix_rank_selector_decidable','rb','rc','q','r')+('cases hrows',)
            +(f"have hcolumns : ({_selector('cb','cc','q','w','columns_yes')}) \\/ ~({_selector('cb','cc','q','w','columns_no')})",)
            +_apply('matrix_rank_selector_decidable','cb','cc','q','w')+('cases hcolumns',)
            +(f"have hvalue : ({_nonzero_value(*signed,'value_yes')}) \\/ ~({_nonzero_value(*signed,'value_no')})",)
            +_apply('matrix_rank_selected_nonzero_value_decidable',*signed)+('cases hvalue','left','split','exact hrows_left','split','exact hcolumns_left','exact hvalue_left')
            +('right','intro hminor','cases hminor','cases hminor_right','apply hvalue_right','exact hminor_right_right')
            +('right','intro hminor','cases hminor','cases hminor_right','apply hcolumns_right','exact hminor_right_left')
            +('right','intro hminor','cases hminor','apply hrows_right','exact hminor_left'),
            'Actual nonzero minors with fixed selectors are decidable, checking all bounds, distinctness, and a genuine determinant evaluation.',
        ),
        spec(
            'matrix_rank_nonzero_selected_minor_transport',
            f"forall {' '.join(nonzero)} Rb Rc Cb Cc. ({_prefix('rb','rc','Rb','Rc','q','nonzero_rows')}) -> "
            f"({_prefix('cb','cc','Cb','Cc','q','nonzero_columns')}) -> ({_nonzero_selected(*nonzero,'nonzero_source')}) -> "
            f"({_nonzero_selected(*recoded_nonzero,'nonzero_target')})",
            ('matrix_rank_selector_transport','matrix_rank_selected_determinant_selector_transport'),
            _intro(*nonzero,'Rb','Rc','Cb','Cc','hrows','hcolumns','hminor')+_parts('hminor',3)+('split',)
            +_apply('matrix_rank_selector_transport','rb','rc','Rb','Rc','q','r')+('exact hrows','exact hminor_left','split')
            +_apply('matrix_rank_selector_transport','cb','cc','Cb','Cc','q','w')+('exact hcolumns','exact hminor_right_left')
            +_cases('hminor_right_right',2)+('cases hminor_right_right_witness_witness',)+_exists('x','x1')+('split',)
            +_apply('matrix_rank_selected_determinant_selector_transport',*signed,'Rb','Rc','Cb','Cc','x','x1')
            +('exact hrows','exact hcolumns','exact hminor_right_right_witness_witness_left','exact hminor_right_right_witness_witness_right'),
            'Every genuine nonzero minor survives the complete finite row and column selector recoding with its nonzero value unchanged.',
        ),
        spec(
            'matrix_rank_selected_determinant_empty',
            f"forall {' '.join(signed[:-1])}. ({_selected_det(*signed[:-1],'0','1','0','selected_empty')})",
            ('matrix_rank_selected_prefix_empty','signed_recursive_determinant_empty'),
            _intro(*signed[:-1])+_exists('0','0','0','0')+('split','split','have hlength : 0 * 0 = 0','apply PA5','rewrite hlength')
            +_apply('matrix_rank_selected_prefix_empty','pb','pc','w','rb','rc','cb','cc','0','0','0')
            +('have hlength : 0 * 0 = 0','apply PA5','rewrite hlength')
            +_apply('matrix_rank_selected_prefix_empty','nb','nc','w','rb','rc','cb','cc','0','0','0')
            +_apply('signed_recursive_determinant_empty','0','0','0','0'),
            'The selected zero-by-zero submatrix has its genuine determinant (1,0), for arbitrary ambient matrices and selector codes.',
        ),
        spec(
            'matrix_rank_nonzero_minor_dimension_bounds',
            f"forall {' '.join(matrix)} q. ({_nonzero_minor(*matrix,'q','minor_dimensions')}) -> "
            f"({_and(_le('q','r','minor_rows_bound'),_le('q','w','minor_columns_bound'))})",
            ('matrix_rank_selector_dimension_bound',),
            _intro(*matrix,'q','hminor')+_cases('hminor',4)+_parts('hminor'+'_witness'*4,3)+('split',)
            +_apply('matrix_rank_selector_dimension_bound','x','x1','q','r')+('exact hminor_witness_witness_witness_witness_left',)
            +_apply('matrix_rank_selector_dimension_bound','x2','x3','q','w')+('exact hminor_witness_witness_witness_witness_right_left',),
            'The order of every actual nonzero minor is bounded by both rectangular dimensions; no extra size premise is built into nonzeroness.',
        ),
        spec(
            'matrix_rank_nonzero_minor_empty',
            f"forall {' '.join(matrix)}. ({_nonzero_minor(*matrix,'0','minor_empty')})",
            ('matrix_rank_selector_empty','matrix_rank_selected_determinant_empty','succ_ne_zero'),
            _intro(*matrix)+_exists('0','0','0','0')+('split',)+_apply('matrix_rank_selector_empty','0','0','r')
            +('split',)+_apply('matrix_rank_selector_empty','0','0','w')+_exists('1','0')+('split',)
            +_apply('matrix_rank_selected_determinant_empty','pb','pc','nb','nc','w','0','0','0','0')+_apply('succ_ne_zero','0'),
            'Every rectangular matrix has a genuine nonzero empty minor, including zero-row and zero-column matrices.',
        ),
    )


__all__ = ['signed_selected_submatrix_relation','signed_selected_determinant_relation','nonzero_selected_minor_relation','nonzero_matrix_minor_relation','make_matrix_rank_selected_minors_candidate_theorems']
