"""Constructive rectangular rank by exhaustive actual-minor search.

The finite search boxes are proved complete for all selector encodings.
Every candidate uses a genuine selected submatrix and the unrestricted
recursive determinant. Maximality is over all minor orders, not merely the
next leading principal minor. These are additive HA candidate bodies only.
"""

from __future__ import annotations

from typing import Any, Callable

from .matrix_recursive_determinant_candidate import (
    _and, _apply, _cases, _exists, _intro, _le, _lt,
    _names, _part, _parts, _prefix, _rewrite_all, _safe,
)
from .matrix_rank_finite_coding_candidate import _arguments, _box, _selector
from .matrix_rank_selected_minors_candidate import (
    _nonzero_minor, _nonzero_selected, _selected_det,
)


def _search(predicate: Callable[[str],str], limit: str, tag: str) -> str:
    a, = _names(tag,'a')
    return f'exists {a}. ({_and(_lt(a,limit,tag+"bound"),predicate(a))})'


def _column_search(pb: str, pc: str, nb: str, nc: str, r: str, w: str, q: str, rb: str, rc: str, cc: str, C: str, tag: str) -> str:
    return _search(lambda cb:_nonzero_selected(pb,pc,nb,nc,r,w,q,rb,rc,cb,cc,tag+'minor'),C,tag+'columns')


def _box_search(pb: str, pc: str, nb: str, nc: str, r: str, w: str, q: str, rc: str, cc: str, R: str, C: str, tag: str) -> str:
    return _search(lambda rb:_column_search(pb,pc,nb,nc,r,w,q,rb,rc,cc,C,tag+'row'),R,tag+'rows')


def _rewrite_at(equation: str, variable: str, formula: str, hypothesis: str) -> tuple[str, ...]:
    return tuple(command+' at '+hypothesis for command in _rewrite_all(equation,variable,formula))


def _finite_search_spec(
    spec: Callable[...,Any], name: str, parameters: tuple[str,...],
    predicate: Callable[[str],str], decision: str, decision_arguments: Callable[[str],tuple[str,...]],
) -> Any:
    """Instantiate an ordinary first-order HA induction; no new kernel rule."""
    yes = _search(predicate,'L',name+'yes')
    no = _search(predicate,'L',name+'no')
    return spec(
        name, f"forall {' '.join(parameters)} L. ({yes}) \\/ ~({no})",
        ('matrix_rank_no_index_below_zero','le_succ','le_refl','finite_lt_succ_eq_or_lt',decision),
        _intro(*parameters)+('induction L','right','intro hfound','cases hfound','cases hfound_witness')
        +_apply('matrix_rank_no_index_below_zero','x')+('exact hfound_witness_left','cases IH')
        +('left','cases IH_left','cases IH_left_witness','exists x','split')
        +_apply('le_succ','S x','L')+('exact IH_left_witness_left','exact IH_left_witness_right')
        +(f'have hcurrent : ({predicate("L")}) \\/ ~({predicate("L")})',)
        +_apply(decision,*decision_arguments('L'))+('cases hcurrent','left','exists L','split')
        +_apply('le_refl','S L')+('exact hcurrent_left','right','intro hfound','cases hfound','cases hfound_witness')
        +(f"have hcase : x = L \\/ ({_lt('x','L',name+'previous')})",)
        +_apply('finite_lt_succ_eq_or_lt','L','x')+('exact hfound_witness_left','cases hcase','apply hcurrent_right')
        +_rewrite_at('hcase_left','x',predicate('x'),'hfound_witness_right')+('exact hfound_witness_right',)
        +('apply IH_right','exists x','split','exact hcase_right','exact hfound_witness_right'),
        'An ordinary HA induction exhaustively searches the finite code bound using an already proved actual-candidate decision; no unbounded existential decision is assumed.',
    )


def _all_zero(pb: str, pc: str, nb: str, nc: str, r: str, w: str, q: str, tag: str) -> str:
    rb,rc,cb,cc,p,n = _names(tag,'rb','rc','cb','cc','p','n')
    return (
        f'forall {rb} {rc} {cb} {cc} {p} {n}. ({_selector(rb,rc,q,r,tag+"rows")}) -> '
        f'({_selector(cb,cc,q,w,tag+"columns")}) -> '
        f'({_selected_det(pb,pc,nb,nc,w,rb,rc,cb,cc,q,p,n,tag+"evaluation")}) -> {p} = {n}'
    )


def all_signed_minors_zero_relation(pb: str, pc: str, nb: str, nc: str, r: str, w: str, q: str, *, tag: str) -> str:
    """Every actual minor of this order has equal signed components."""
    return _all_zero(*_arguments(pb,pc,nb,nc,r,w,q),_safe(tag))


def _higher_absent(pb: str, pc: str, nb: str, nc: str, r: str, w: str, K: str, rank: str, tag: str) -> str:
    j, = _names(tag,'j')
    return (
        f'forall {j}. ({_lt(rank,j,tag+"above")}) -> ({_le(j,K,tag+"limit")}) -> '
        f'~({_nonzero_minor(pb,pc,nb,nc,r,w,j,tag+"minor")})'
    )


def _maximum(pb: str, pc: str, nb: str, nc: str, r: str, w: str, K: str, rank: str, tag: str) -> str:
    return _and(
        _le(rank,K,tag+'bound'),_nonzero_minor(pb,pc,nb,nc,r,w,rank,tag+'witness'),
        _higher_absent(pb,pc,nb,nc,r,w,K,rank,tag+'higher'),
    )


def _rank(pb: str, pc: str, nb: str, nc: str, r: str, w: str, rank: str, tag: str) -> str:
    q, = _names(tag,'q')
    return _and(
        _le(rank,r,tag+'rows_bound'),_le(rank,w,tag+'columns_bound'),
        _nonzero_minor(pb,pc,nb,nc,r,w,rank,tag+'witness'),
        f'forall {q}. ({_lt(rank,q,tag+"higher")}) -> ({_all_zero(pb,pc,nb,nc,r,w,q,tag+"zero")})',
    )


def rectangular_matrix_rank_relation(pb: str, pc: str, nb: str, nc: str, r: str, w: str, rank: str, *, tag: str) -> str:
    """A genuine nonzero rank minor and vanishing of *all* higher minors."""
    return _rank(*_arguments(pb,pc,nb,nc,r,w,rank),_safe(tag))


def make_matrix_rank_certificate_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    matrix = ('pb','pc','nb','nc','r','w')
    column_parameters = (*matrix,'q','rb','rc','cc')
    box_parameters = (*matrix,'q','rc','cc','C')
    hminor = 'hminor'+'_witness'*4
    unique_other = f"forall other. ({_rank(*matrix,'other','other_rank')}) -> other = rank"
    unique_result = _and(_rank(*matrix,'rank','unique_rank'),unique_other)
    return (
        _finite_search_spec(
            spec,'matrix_rank_selected_column_search_decidable',column_parameters,
            lambda cb:_nonzero_selected(*matrix,'q','rb','rc',cb,'cc','column_candidate'),
            'matrix_rank_nonzero_selected_minor_decidable',lambda cb:(*matrix,'q','rb','rc',cb,'cc'),
        ),
        _finite_search_spec(
            spec,'matrix_rank_selected_box_search_decidable',box_parameters,
            lambda rb:_column_search(*matrix,'q',rb,'rc','cc','C','row_candidate'),
            'matrix_rank_selected_column_search_decidable',lambda rb:(*matrix,'q',rb,'rc','cc','C'),
        ),
        spec(
            'matrix_rank_nonzero_minor_recode_in_box',
            f"forall {' '.join(matrix)} q rc cc R C. ({_box('rc','R','q','r','rows_box')}) -> ({_box('cc','C','q','w','columns_box')}) -> "
            f"({_nonzero_minor(*matrix,'q','unbounded_minor')}) -> ({_box_search(*matrix,'q','rc','cc','R','C','bounded_minor')})",
            ('matrix_rank_nonzero_selected_minor_transport',),
            _intro(*matrix,'q','rc','cc','R','C','hrowbox','hcolbox','hminor')
            +('cases hrowbox','cases hcolbox')+_cases('hminor',4)+_parts(hminor,3)
            +(f'cases {hminor}_left',f'cases {hminor}_right_left')
            +(f"have hrow : exists a. {_and(_lt('a','R','row_code_bound'),_prefix('x','x1','a','rc','q','row_code_prefix'))}",)
            +_apply('hrowbox_right','x','x1')+(f'exact {hminor}_left_left',)+('cases hrow','cases hrow_witness')
            +(f"have hcolumn : exists a. {_and(_lt('a','C','column_code_bound'),_prefix('x2','x3','a','cc','q','column_code_prefix'))}",)
            +_apply('hcolbox_right','x2','x3')+(f'exact {hminor}_right_left_left',)+('cases hcolumn','cases hcolumn_witness')
            +('exists x4','split','exact hrow_witness_left','exists x5','split','exact hcolumn_witness_left')
            +_apply('matrix_rank_nonzero_selected_minor_transport',*matrix,'q','x','x1','x2','x3','x4','rc','x5','cc')
            +('exact hrow_witness_right','exact hcolumn_witness_right',f'exact {hminor}'),
            'Every genuine nonzero minor, whatever its original selector encodings, occurs in the proved finite row/column code search box.',
        ),
        spec(
            'matrix_rank_nonzero_minor_of_box_search',
            f"forall {' '.join(matrix)} q rc cc R C. ({_box_search(*matrix,'q','rc','cc','R','C','found_minor')}) -> "
            f"({_nonzero_minor(*matrix,'q','actual_minor')})",
            (),
            _intro(*matrix,'q','rc','cc','R','C','hsearch')+('cases hsearch','cases hsearch_witness','cases hsearch_witness_right','cases hsearch_witness_right_witness')
            +_exists('x','rc','x1','cc')+('exact hsearch_witness_right_witness_right',),
            'A successful bounded code search supplies actual distinct in-range selectors and a genuine nonzero determinant, not merely a Boolean flag.',
        ),
        spec(
            'matrix_rank_nonzero_minor_decidable',
            f"forall {' '.join(matrix)} q. ({_nonzero_minor(*matrix,'q','exists_minor')}) \\/ ~({_nonzero_minor(*matrix,'q','no_minor')})",
            ('matrix_rank_uniform_beta_prefix_box_exists','matrix_rank_selected_box_search_decidable',
             'matrix_rank_nonzero_minor_of_box_search','matrix_rank_nonzero_minor_recode_in_box'),
            _intro(*matrix,'q')
            +(f"have hrows : exists rc R. ({_box('rc','R','q','r','finite_rows')})",)
            +_apply('matrix_rank_uniform_beta_prefix_box_exists','q','r')+_cases('hrows',2)
            +(f"have hcolumns : exists cc C. ({_box('cc','C','q','w','finite_columns')})",)
            +_apply('matrix_rank_uniform_beta_prefix_box_exists','q','w')+_cases('hcolumns',2)
            +(f"have hsearch : ({_box_search(*matrix,'q','x','x2','x1','x3','search_yes')}) \\/ ~({_box_search(*matrix,'q','x','x2','x1','x3','search_no')})",)
            +_apply('matrix_rank_selected_box_search_decidable',*matrix,'q','x','x2','x3','x1')+('cases hsearch','left')
            +_apply('matrix_rank_nonzero_minor_of_box_search',*matrix,'q','x','x2','x1','x3')+('exact hsearch_left','right','intro hminor','apply hsearch_right')
            +_apply('matrix_rank_nonzero_minor_recode_in_box',*matrix,'q','x','x2','x1','x3')
            +('exact hrows_witness_witness','exact hcolumns_witness_witness','exact hminor'),
            'Existence of a genuine nonzero minor of any requested order is constructively decidable, with completeness for all unbounded beta selector encodings proved.',
        ),
        spec(
            'matrix_rank_le_successor_cases',
            f"forall j K. ({_le('j','S K','successor_bound')}) -> j = S K \\/ ({_le('j','K','previous_bound')})",
            ('succ_le_succ','finite_lt_succ_eq_or_lt','le_of_succ_le_succ'),
            _intro('j','K','hj')
            +(f"have hstrict : {_lt('j','S (S K)','strict_successor')}",)
            +_apply('succ_le_succ','j','S K')+('exact hj',)
            +(f"have hcase : j = S K \\/ ({_lt('j','S K','previous_strict')})",)
            +_apply('finite_lt_succ_eq_or_lt','S K','j')+('exact hstrict','cases hcase','left','exact hcase_left','right')
            +_apply('le_of_succ_le_succ','j','K')+('exact hcase_right',),
            'A natural number bounded by a successor is either that successor or is bounded by its predecessor.',
        ),
        spec(
            'matrix_rank_maximal_nonzero_prefix_exists',
            f"forall {' '.join(matrix)} K. exists rank. ({_maximum(*matrix,'K','rank','maximal_prefix')})",
            ('matrix_rank_nonzero_minor_empty','matrix_rank_nonzero_minor_decidable','zero_le','le_refl','le_succ','lt_not_le','matrix_rank_le_successor_cases'),
            _intro(*matrix)+('induction K','exists 0','split')+_apply('zero_le','0')
            +('split',)+_apply('matrix_rank_nonzero_minor_empty',*matrix)+_intro('j','habove','hbound','hminor')
            +_apply('lt_not_le','0','j')+('exact habove','exact hbound')
            +(f"have hcurrent : ({_nonzero_minor(*matrix,'S K','current_yes')}) \\/ ~({_nonzero_minor(*matrix,'S K','current_no')})",)
            +_apply('matrix_rank_nonzero_minor_decidable',*matrix,'S K')+('cases hcurrent','exists S K','split')
            +_apply('le_refl','S K')+('split','exact hcurrent_left')+_intro('j','habove','hbound','hminor')
            +_apply('lt_not_le','S K','j')+('exact habove','exact hbound')
            +('cases IH',)+_parts('IH_witness',3)+('exists x','split')+_apply('le_succ','x','K')+('exact IH_witness_left','split','exact IH_witness_right_left')
            +_intro('j','habove','hbound','hminor')
            +(f"have hcase : j = S K \\/ ({_le('j','K','max_previous')})",)
            +_apply('matrix_rank_le_successor_cases','j','K')+('exact hbound','cases hcase','apply hcurrent_right')
            +_rewrite_at('hcase_left','j',_nonzero_minor(*matrix,'j','max_found'),'hminor')+('exact hminor',)
            +_apply('IH_witness_right_right','j')+('exact habove','exact hcase_right','exact hminor'),
            'HA induction with complete finite minor decisions constructs an actual nonzero minor of greatest order within every finite dimension prefix; the empty minor seeds rank zero.',
        ),
        spec(
            'matrix_rank_all_minors_zero_from_absence',
            f"forall {' '.join(matrix)} q. ~({_nonzero_minor(*matrix,'q','absent_minor')}) -> ({_all_zero(*matrix,'q','all_zero')})",
            ('eq_decidable',),
            _intro(*matrix,'q','habsent','rb','rc','cb','cc','p','n','hrows','hcolumns','hvalue')
            +('specialize eq_decidable p','specialize eq_decidable n','cases eq_decidable','exact eq_decidable_left','exfalso','apply habsent')
            +_exists('rb','rc','cb','cc')+('split','exact hrows','split','exact hcolumns')+_exists('p','n')+('split','exact hvalue','exact eq_decidable_right'),
            'Absence of any actual nonzero minor implies that every genuinely selected evaluated minor has equal signed components, constructively using natural equality decision.',
        ),
        spec(
            'matrix_rank_absence_from_all_minors_zero',
            f"forall {' '.join(matrix)} q. ({_all_zero(*matrix,'q','zero_minors')}) -> ~({_nonzero_minor(*matrix,'q','forbidden_minor')})",
            (),
            _intro(*matrix,'q','hzero','hminor')+_cases('hminor',4)+_parts(hminor,3)+_cases(hminor+'_right_right',2)
            +(f'cases {hminor}_right_right_witness_witness',f'apply {hminor}_right_right_witness_witness_right')
            +_apply('hzero','x','x1','x2','x3','x4','x5')
            +(f'exact {hminor}_left',f'exact {hminor}_right_left',f'exact {hminor}_right_right_witness_witness_left'),
            'Universal vanishing rules out every witness to a genuine nonzero minor of the same order.',
        ),
        spec(
            'rectangular_matrix_rank_certificate_exists',
            f"forall {' '.join(matrix)}. exists rank. ({_rank(*matrix,'rank','rank_exists')})",
            ('matrix_rank_maximal_nonzero_prefix_exists','matrix_rank_nonzero_minor_dimension_bounds','matrix_rank_all_minors_zero_from_absence'),
            _intro(*matrix)
            +(f"have hmaximum : exists rank. ({_maximum(*matrix,'r','rank','full_maximum')})",)
            +_apply('matrix_rank_maximal_nonzero_prefix_exists',*matrix,'r')+('cases hmaximum',)+_parts('hmaximum_witness',3)
            +(f"have hdimensions : {_and(_le('x','r','rank_row_bound'),_le('x','w','rank_column_bound'))}",)
            +_apply('matrix_rank_nonzero_minor_dimension_bounds',*matrix,'x')+('exact hmaximum_witness_right_left','cases hdimensions','exists x','split','exact hdimensions_left','split','exact hdimensions_right','split','exact hmaximum_witness_right_left')
            +_intro('q','hq')+_apply('matrix_rank_all_minors_zero_from_absence',*matrix,'q')+('intro hminor',)
            +(f"have hminorbound : {_and(_le('q','r','higher_row_bound'),_le('q','w','higher_column_bound'))}",)
            +_apply('matrix_rank_nonzero_minor_dimension_bounds',*matrix,'q')+('exact hminor','cases hminorbound')
            +_apply('hmaximum_witness_right_right','q')+('exact hq','exact hminorbound_left','exact hminor'),
            'Every arbitrary finite rectangular signed matrix has an actual nonzero rank minor, rank bounded by both dimensions, and every higher minor is proved zero; all searches and determinant evaluations are object-level constructive proofs.',
        ),
        spec(
            'rectangular_matrix_rank_functional',
            f"forall {' '.join(matrix)} rank other. ({_rank(*matrix,'rank','first_rank')}) -> ({_rank(*matrix,'other','second_rank')}) -> rank = other",
            ('lt_trichotomy','matrix_rank_absence_from_all_minors_zero'),
            _intro(*matrix,'rank','other','hfirst','hsecond')+_parts('hfirst',4)+_parts('hsecond',4)
            +('specialize lt_trichotomy rank','specialize lt_trichotomy other','cases lt_trichotomy','exact lt_trichotomy_left','cases lt_trichotomy_right','exfalso')
            +_apply('matrix_rank_absence_from_all_minors_zero',*matrix,'other')
            +_apply('hfirst_right_right_right','other')+('exact lt_trichotomy_right_left','exact hsecond_right_right_left','exfalso')
            +_apply('matrix_rank_absence_from_all_minors_zero',*matrix,'rank')
            +_apply('hsecond_right_right_right','rank')+('exact lt_trichotomy_right_right','exact hfirst_right_right_left'),
            'The genuine maximal-nonzero-minor rank is unique: either strict inequality contradicts one actual nonzero witness and the other certificate\'s universal higher-minor vanishing.',
        ),
        spec(
            'rectangular_matrix_rank_exists_unique',
            f"forall {' '.join(matrix)}. exists rank. ({unique_result})",
            ('rectangular_matrix_rank_certificate_exists','rectangular_matrix_rank_functional'),
            _intro(*matrix)
            +(f"have hcertificate : exists rank. ({_rank(*matrix,'rank','constructed_rank')})",)
            +_apply('rectangular_matrix_rank_certificate_exists',*matrix)+('cases hcertificate','exists x','split','exact hcertificate_witness')
            +_intro('other','hother')+_apply('rectangular_matrix_rank_functional',*matrix,'other','x')+('exact hother','exact hcertificate_witness'),
            'Every finite rectangular signed beta-coded matrix has exactly one genuine rank certificate value, with a nonzero rank minor and universal vanishing of all higher minors.',
        ),
        spec(
            'rectangular_matrix_rank_successor_minors_zero',
            f"forall {' '.join(matrix)} rank. ({_rank(*matrix,'rank','successor_rank')}) -> ({_all_zero(*matrix,'S rank','successor_minors')})",
            ('le_refl',),
            _intro(*matrix,'rank','hrank')+_parts('hrank',4)
            +_apply('hrank_right_right_right','S rank')+_apply('le_refl','S rank'),
            'In particular, every actual minor of order rank plus one vanishes, with no choice of selector or determinant history left implicit.',
        ),
        spec(
            'rectangular_matrix_rank_zero_rows',
            f"forall pb pc nb nc w. ({_rank('pb','pc','nb','nc','0','w','0','zero_rows_rank')})",
            ('rectangular_matrix_rank_certificate_exists','le_zero'),
            _intro('pb','pc','nb','nc','w')
            +(f"have hrank : exists rank. ({_rank('pb','pc','nb','nc','0','w','rank','zero_rows_exists')})",)
            +_apply('rectangular_matrix_rank_certificate_exists','pb','pc','nb','nc','0','w')+('cases hrank','cases hrank_witness','have hzero : x = 0')
            +_apply('le_zero','x')+('exact hrank_witness_left',)
            +_rewrite_at('hzero','x',_rank('pb','pc','nb','nc','0','w','x','zero_rows_result'),'hrank_witness')+('exact hrank_witness',),
            'Every zero-row rectangular matrix has rank zero, with the actual empty determinant supplying its nonzero zero-order minor.',
        ),
        spec(
            'rectangular_matrix_rank_zero_columns',
            f"forall pb pc nb nc r. ({_rank('pb','pc','nb','nc','r','0','0','zero_columns_rank')})",
            ('rectangular_matrix_rank_certificate_exists','le_zero'),
            _intro('pb','pc','nb','nc','r')
            +(f"have hrank : exists rank. ({_rank('pb','pc','nb','nc','r','0','rank','zero_columns_exists')})",)
            +_apply('rectangular_matrix_rank_certificate_exists','pb','pc','nb','nc','r','0')+('cases hrank','cases hrank_witness','cases hrank_witness_right','have hzero : x = 0')
            +_apply('le_zero','x')+('exact hrank_witness_right_left',)
            +_rewrite_at('hzero','x',_rank('pb','pc','nb','nc','r','0','x','zero_columns_result'),'hrank_witness')+('exact hrank_witness',),
            'Every zero-column rectangular matrix has rank zero, including the zero-by-zero matrix, without a positivity premise on either dimension.',
        ),
    )


__all__ = ['all_signed_minors_zero_relation','rectangular_matrix_rank_relation','make_matrix_rank_certificate_candidate_theorems']
