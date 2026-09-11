"""Actual decoded-tuple index maps and independent Jordan count uniqueness.

These new ordinary candidates do not modify the verified Jordan75 sources.
The map records actual beta positions and tuple equality, never a cardinality
equation. All ten bodies remain candidates until original conditional replay.
"""
from .finite_permutation_theorems import injective_prefix
from . import jordan_multiplicativity_candidate as prior
base = prior._base

_and,_at,_lt,_equal,_bounded,_primitive,_enum,_jordan=(base._and,base._at,base._lt,base._equal,
    base._bounded,base._primitive,base._enumeration,base._jordan)
_entry,_le,_rewrite=prior._entry,prior._le,prior._rewrite
_intro,_call,_parts=base._intro,base._call,base._parts
LEFT=('A','B','C','D');RIGHT=('E','F','G','H');CODES=LEFT+RIGHT


def _contract(args,premises,result):
    return 'forall '+' '.join(args)+'. '+' -> '.join('('+f+')' for f in (*premises,result))


def _match(k,A,B,C,D,E,F,G,H,i,j,tag):
    args=(k,A,B,C,D,E,F,G,H,i,j)
    b,c,d,e=base._fresh(tag,args,'b','c','d','e')
    return _contract((b,c,d,e),(_entry(A,B,C,D,i,b,c,tag+'left'),
        _entry(E,F,G,H,j,d,e,tag+'right')),_equal(b,c,d,e,k,tag+'equal'))


def _map(k,A,B,C,D,E,F,G,H,Z,W,q,v,tag):
    args=(k,A,B,C,D,E,F,G,H,Z,W,q,v)
    i,j=base._fresh(tag,args,'index','image')
    return (f'forall {i}. ({_lt(i,q,tag+"index")}) -> exists {j}. '+
        _and(_at(Z,W,i,j,tag+'at'),_lt(j,v,tag+'bound'),
             _match(k,A,B,C,D,E,F,G,H,i,j,tag+'match')))


def _map_value(k,A,B,C,D,E,F,G,H,Z,W,i,j,v,tag):
    return _and(_at(Z,W,i,j,tag+'at'),_lt(j,v,tag+'bound'),
                _match(k,A,B,C,D,E,F,G,H,i,j,tag+'match'))


def _sound(k,n,A,B,C,D,i,b,c,tag):
    return _and(_entry(A,B,C,D,i,b,c,tag+'entry'),_bounded(b,c,k,n,tag+'bound'),
                _primitive(n,b,c,k,tag+'primitive'))


def tuple_enumeration_position_match_relation(k,A,B,C,D,E,F,G,H,i,j,*,tag):
    args=(k,A,B,C,D,E,F,G,H,i,j);base._public(args,tag)
    return _match(*args,tag)


def tuple_enumeration_index_map_relation(k,A,B,C,D,E,F,G,H,Z,W,q,v,*,tag):
    args=(k,A,B,C,D,E,F,G,H,Z,W,q,v);base._public(args,tag)
    return _map(*args,tag)


def _position_rows(spec):
    rows=[];args=('k',*CODES,'i','j','b','c','d','e')
    body=_intro(*args,'hl','hr','he','a0','a1','a2','a3','hnewl','hnewr')
    body+=('cases hl','cases hr','cases hnewl','cases hnewr')
    equal=_equal('b','c','d','e','k','position_equal')
    for old,new,code,scale,index,oldhyp,newhyp in (
        ('b','a0','A','B','i','hl_left','hnewl_left'),
        ('c','a1','C','D','i','hl_right','hnewl_right'),
        ('d','a2','E','F','j','hr_left','hnewr_left'),
        ('e','a3','G','H','j','hr_right','hnewr_right')):
        body+=(f'have heq_{old} : {old}={new}',)+_call('beta_at_unique',code,scale,index,old,new)
        body+=('exact '+oldhyp,'exact '+newhyp)
    for old,new in zip(('b','c','d','e'),('a0','a1','a2','a3')):
        body+=_rewrite('heq_'+old,old,equal,'he');equal=equal.replace('('+old+')','('+new+')')
    body+=('exact he',)
    rows.append(spec('jordan_enumeration_position_match_from_entries',_contract(args,
        (_entry(*LEFT,'i','b','c','position_left'),_entry(*RIGHT,'j','d','e','position_right'),
         _equal('b','c','d','e','k','position_equal')),_match('k',*CODES,'i','j','position_result')),
        ('beta_at_unique',),body,
        'Actual outer beta functionality transports chosen tuple equality to every decoding at the same two positions.'))

    args=('k','n',*LEFT,'u',*RIGHT,'v','i')
    body=_intro(*args,'hl','hr','hi')+('cases hl',
        'have hv : exists b c. '+_sound('k','n',*LEFT,'i','b','c','chosen_source'))
    body+=_call('hl_left','i')+('exact hi','cases hv','cases hv_witness')+_parts('hv_witness_witness',3)
    body+=('have hw : '+base._listed('x','x1','k',*RIGHT,'v','chosen_target'),)
    body+=_call('jordan_enumeration_complete','k','n',*RIGHT,'v','x','x1')+(
        'exact hr','exact hv_witness_witness_right_left','exact hv_witness_witness_right_right',
        'cases hw','cases hw_witness','cases hw_witness_witness')+_parts('hw_witness_witness_witness',3)
    body+=('exists x2','split','exact hw_witness_witness_witness_left',)
    body+=_call('jordan_enumeration_position_match_from_entries','k',*CODES,'i','x2','x','x1','x3','x4')+(
        'exact hv_witness_witness_left','exact hw_witness_witness_witness_right_left',
        'exact hw_witness_witness_witness_right_right')
    rows.append(spec('jordan_enumeration_position_match_exists',_contract(args,
        (_enum('k','n',*LEFT,'u','source_enum'),_enum('k','n',*RIGHT,'v','target_enum'),_lt('i','u','source_index')),
        'exists j. '+_and(_lt('j','v','chosen_image_bound'),_match('k',*CODES,'i','j','chosen_image_match'))),
        ('jordan_enumeration_complete','jordan_enumeration_position_match_from_entries'),body,
        'Every actual source position has a bounded target position representing precisely the same coordinate tuple.'))
    return tuple(rows)


def _map_rows(spec):
    rows=[];args=('k',*CODES,'Z','W','v')
    body=_intro(*args,'i','hi')+('exfalso',)+_call('lt_not_le','i','0')+('exact hi',)+_call('zero_le','i')
    rows.append(spec('jordan_enumeration_index_map_empty',_contract(args,(),_map('k',*CODES,'Z','W','0','v','empty_map')),
        ('lt_not_le','zero_le'),body,'The zero-length index map is vacuous, independently of target length.'))

    args=('k',*CODES,'Z','W','q','v','j')
    body=_intro(*args,'hm','hj','hmatch')+('have hext : exists P Q. '+_and(
        _at('P','Q','q','j','append_image'),base._prefix('Z','W','P','Q','q','append_preserves')),)
    body+=_call('beta_prefix_extend','q','Z','W','j')+('cases hext','cases hext_witness','cases hext_witness_witness',
        'exists x','exists x1','intro i','intro hi','have hc : i=q \\/ ('+_lt('i','q','append_old_index')+')')
    body+=_call('finite_lt_succ_eq_or_lt','q','i')+('exact hi','cases hc','exists j','split',
        'rewrite hc_left','rewrite hc_left','exact hext_witness_witness_left','split','exact hj')
    body+=_rewrite('hc_left','i',_match('k',*CODES,'i','j','append_new_match'))+('exact hmatch',
        'have hv : exists r. '+_map_value('k',*CODES,'Z','W','i','r','v','append_previous'))
    body+=_call('hm','i')+('exact hc_right','cases hv',)+_parts('hv_witness',3)
    body+=('exists x2','split')+_call('hext_witness_witness_right','i','x2')+(
        'exact hc_right','exact hv_witness_left','split','exact hv_witness_right_left','exact hv_witness_right_right')
    rows.append(spec('jordan_enumeration_index_map_append',_contract(args,
        (_map('k',*CODES,'Z','W','q','v','append_old'),_lt('j','v','append_bound'),
         _match('k',*CODES,'q','j','append_match')),
        'exists P Q. '+_map('k',*CODES,'P','Q','S q','v','append_result')),
        ('beta_prefix_extend','finite_lt_succ_eq_or_lt'),body,
        'Append one genuine matched target index and preserve all previous mapped positions by beta extension.'))

    tail=('k','n',*LEFT,'u',*RIGHT,'v');args=('q',*tail)
    body=('induction q',)+_intro(*tail,'hl','hr','hq')+('exists 0','exists 0',)
    body+=_call('jordan_enumeration_index_map_empty','k',*CODES,'0','0','v')
    body+=_intro(*tail,'hl','hr','hq')+('have hp : exists Z W. '+_map('k',*CODES,'Z','W','q','v','induction_prefix'),)
    body+=_call('IH',*tail)+('exact hl','exact hr')+_call('le_trans','q','S q','u')
    body+=_call('le_succ_self','q')+('exact hq','cases hp','cases hp_witness',
        'have hm : exists j. '+_and(_lt('j','v','induction_image_bound'),_match('k',*CODES,'q','j','induction_image_match')))
    body+=_call('jordan_enumeration_position_match_exists','k','n',*LEFT,'u',*RIGHT,'v','q')+(
        'exact hl','exact hr','exact hq','cases hm','cases hm_witness')
    body+=_call('jordan_enumeration_index_map_append','k',*CODES,'x','x1','q','v','x2')+(
        'exact hp_witness_witness','exact hm_witness_left','exact hm_witness_right')
    rows.append(spec('jordan_enumeration_index_map_exists',_contract(args,
        (_enum('k','n',*LEFT,'u','exists_source'),_enum('k','n',*RIGHT,'v','exists_target'),_le('q','u','exists_bound')),
        'exists Z W. '+_map('k',*CODES,'Z','W','q','v','exists_map')),
        ('jordan_enumeration_index_map_empty','le_trans','le_succ_self',
         'jordan_enumeration_position_match_exists','jordan_enumeration_index_map_append'),body,
        'Finite induction constructs an actual beta map for every source prefix, with no finite-choice axiom.'))

    args=('k',*CODES,'Z','W','q','v','i','j')
    body=_intro(*args,'hm','hi','hat')+('have hv : exists r. '+_map_value('k',*CODES,'Z','W','i','r','v','actual_map'),)
    body+=_call('hm','i')+('exact hi','cases hv',)+_parts('hv_witness',3)+('have he : x=j',)
    body+=_call('beta_at_unique','Z','W','i','x','j')+('exact hv_witness_left','exact hat','split')
    body+=_rewrite('he','x',_lt('x','v','actual_bound'),'hv_witness_right_left')+('exact hv_witness_right_left',)
    body+=_rewrite('he','x',_match('k',*CODES,'i','x','actual_match'),'hv_witness_right_right')+('exact hv_witness_right_right',)
    rows.append(spec('jordan_enumeration_index_map_entry',_contract(args,
        (_map('k',*CODES,'Z','W','q','v','actual_given_map'),_lt('i','q','actual_index'),_at('Z','W','i','j','actual_value')),
        _and(_lt('j','v','actual_result_bound'),_match('k',*CODES,'i','j','actual_result_match'))),
        ('beta_at_unique',),body,'Every actual decoded map value is bounded and matches the represented source tuple.'))
    return tuple(rows)


def _injective_row(spec):
    args=('k','n',*LEFT,'u',*RIGHT,'v','Z','W')
    body=_intro(*args,'hl','hr','hm')+('split','intro i','intro hi',
        'have hv : exists j. '+_map_value('k',*CODES,'Z','W','i','j','v','bounded_map'))
    body+=_call('hm','i')+('exact hi','cases hv',)+_parts('hv_witness',3)+(
        'exists x','split','exact hv_witness_left','exact hv_witness_right_left')
    body+=_intro('i','j','r','hi','hj','hat','hbt')
    for index,hyp,name in (('i','hat','hmi'),('j','hbt','hmj')):
        body+=(f'have {name} : '+_and(_lt('r','v',name+'bound'),_match('k',*CODES,index,'r',name+'match')),)
        body+=_call('jordan_enumeration_index_map_entry','k',*CODES,'Z','W','u','v',index,'r')+(
            'exact hm','exact h'+index,'exact '+hyp)
    body+=('cases hmi','cases hmj','cases hl','cases hr',
        'have ht : exists b c. '+_sound('k','n',*RIGHT,'r','b','c','target_tuple'))
    body+=_call('hr_left','r')+('exact hmi_left','cases ht','cases ht_witness')+_parts('ht_witness_witness',3)
    body+=('have ha : exists b c. '+_sound('k','n',*LEFT,'i','b','c','first_tuple'),)
    body+=_call('hl_left','i')+('exact hi','cases ha','cases ha_witness')+_parts('ha_witness_witness',3)
    body+=('have hb : exists b c. '+_sound('k','n',*LEFT,'j','b','c','second_tuple'),)
    body+=_call('hl_left','j')+('exact hj','cases hb','cases hb_witness')+_parts('hb_witness_witness',3)
    body+=('have hea : '+_equal('x2','x3','x','x1','k','first_equal_target'),)
    body+=_call('hmi_right','x2','x3','x','x1')+('exact ha_witness_witness_left','exact ht_witness_witness_left',
        'have heb : '+_equal('x4','x5','x','x1','k','second_equal_target'))
    body+=_call('hmj_right','x4','x5','x','x1')+('exact hb_witness_witness_left','exact ht_witness_witness_left',
        'have hrev : '+_equal('x','x1','x4','x5','k','target_equal_second'))
    body+=_call('jordan_tuple_equal_symm','x4','x5','x','x1','k')+('exact heb',
        'have heq : '+_equal('x2','x3','x4','x5','k','source_equal_source'))
    body+=_call('jordan_tuple_equal_trans','x2','x3','x','x1','x4','x5','k')+('exact hea','exact hrev')
    body+=_call('jordan_enumeration_distinct','k','n',*LEFT,'u','i','j','x2','x3','x4','x5')+(
        'exact hl','exact hi','exact hj','exact ha_witness_witness_left','exact hb_witness_witness_left','exact heq')
    return spec('jordan_enumeration_index_map_bounded_injective',_contract(args,
        (_enum('k','n',*LEFT,'u','injective_source'),_enum('k','n',*RIGHT,'v','injective_target'),
         _map('k',*CODES,'Z','W','u','v','injective_map')),
        _and(_bounded('Z','W','u','v','injective_bound'),injective_prefix('Z','W','u',tag='jordan_injective'))),
        ('jordan_enumeration_index_map_entry','jordan_tuple_equal_symm','jordan_tuple_equal_trans','jordan_enumeration_distinct'),
        body,'Equal decoded map indices force coordinate-equal source tuples and hence equal source positions, not equal raw tuple codes.')


def _count_rows(spec):
    rows=[];args=('k','n',*LEFT,'u',*RIGHT,'v')
    left=_enum('k','n',*LEFT,'u','cardinality_left');right=_enum('k','n',*RIGHT,'v','cardinality_right')
    body=_intro(*args,'hl','hr')+('have hm : exists Z W. '+_map('k',*CODES,'Z','W','u','v','cardinality_map'),)
    body+=_call('jordan_enumeration_index_map_exists','u',*args)+('exact hl','exact hr')
    body+=_call('le_refl','u')+('cases hm','cases hm_witness',
        'have hinj : '+_and(_bounded('x','x1','u','v','cardinality_bound'),injective_prefix('x','x1','u',tag='cardinality_inj')))
    body+=_call('jordan_enumeration_index_map_bounded_injective',*args,'x','x1')+(
        'exact hl','exact hr','exact hm_witness_witness','cases hinj',
        'have hc : ('+_le('u','v','cardinality_le')+') \\/ ('+_lt('v','u','cardinality_overflow')+')')
    body+=_call('le_or_lt','u','v')+('cases hc','exact hc_left','exfalso')
    body+=_call('finite_bounded_into_oversized_not_injective','x','x1','u','v')+(
        'exact hinj_left','exact hc_right','exact hinj_right')
    rows.append(spec('jordan_enumeration_cardinality_le',_contract(args,(left,right),_le('u','v','cardinality_result')),
        ('jordan_enumeration_index_map_exists','le_refl','jordan_enumeration_index_map_bounded_injective',
         'le_or_lt','finite_bounded_into_oversized_not_injective'),body,
        'A genuinely constructed bounded injection implies the source count is at most the target count, including empty lists.'))
    body=_intro(*args,'hl','hr')+('have hle : '+_le('u','v','unique_forward'),)
    body+=_call('jordan_enumeration_cardinality_le',*args)+('exact hl','exact hr',
        'have hge : '+_le('v','u','unique_backward'))
    body+=_call('jordan_enumeration_cardinality_le','k','n',*RIGHT,'v',*LEFT,'u')+('exact hr','exact hl')
    body+=_call('le_antisymm','u','v')+('exact hle','exact hge')
    rows.append(spec('jordan_enumeration_cardinality_unique',_contract(args,(left,right),'u=v'),
        ('jordan_enumeration_cardinality_le','le_antisymm'),body,
        'Two complete duplicate-free enumerations of the same primitive coordinate tuples have equal lengths.'))
    body=_intro('k','n','u','v','hl','hr')+_parts('hl',3)+_parts('hr',3)
    body+=('cases hl_right_right','cases hl_right_right_witness','cases hl_right_right_witness_witness',
        'cases hl_right_right_witness_witness_witness','cases hr_right_right','cases hr_right_right_witness',
        'cases hr_right_right_witness_witness','cases hr_right_right_witness_witness_witness')
    body+=_call('jordan_enumeration_cardinality_unique','k','n','x','x1','x2','x3','u','x4','x5','x6','x7','v')+(
        'exact hl_right_right_witness_witness_witness_witness','exact hr_right_right_witness_witness_witness_witness')
    rows.append(spec('jordan_totient_count_unique',_contract(('k','n','u','v'),
        (_jordan('k','n','u','unique_jordan_left'),_jordan('k','n','v','unique_jordan_right')),'u=v'),
        ('jordan_enumeration_cardinality_unique',),body,
        'The independently defined Jordan relation has a unique count, regardless of all chosen beta encodings.'))
    return tuple(rows)


def make_jordan_count_uniqueness_candidate_theorems(spec):
    return _position_rows(spec)+_map_rows(spec)+(_injective_row(spec),)+_count_rows(spec)
