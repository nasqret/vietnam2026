"""Primitive finite tuples and their independently specified cardinality.

Jordan(k,n,j) means an actual complete, duplicate-free enumeration of the
primitive canonical k-tuples modulo n.  It does not contain a product formula,
CRT bijection, multiplicativity equation, or supplied totality assumption.
Different beta encodings of the same coordinate tuple are one element.

The factory currently contains predicate-level prerequisites only.  The final
count existence and multiplicativity contracts are exposed for audit, not
inserted as theorem rows before their ordinary HA bodies exist.
"""
from __future__ import annotations

import re

from peano_lab.library.finite_fold_surface import _identifier
from peano_lab.library.finite_sum_theorems import _at as inherited_at


def _fresh(tag, terms, *roles):
    _identifier(tag, 'Jordan definition tag')
    names = tuple('jt_' + role + '_' + tag for role in roles)
    identifiers = set(re.findall(r"[A-Za-z_][A-Za-z_0-9']*", ' '.join(terms)))
    if identifiers.intersection(names):
        raise ValueError('Jordan binder would capture an argument')
    return names


def _public(arguments, tag):
    _identifier(tag, 'Jordan definition tag')
    for term in arguments:
        _identifier(term, 'Jordan relation argument')
        if term.startswith(('jt_', 'fs_', 'ff_')):
            raise ValueError('Jordan argument enters a reserved binder namespace')


def _and(*clauses):
    return clauses[0] if len(clauses) == 1 else f'(({clauses[0]}) /\\ ({_and(*clauses[1:])}))'


def _lt(a, b, tag):
    g, = _fresh(tag, (a, b), 'gap')
    return f'exists {g}. {g}+S ({a})=({b})'


def _dvd(d, a, tag):
    q, = _fresh(tag, (d, a), 'factor')
    return f'exists {q}. ({a})=({d})*{q}'


def _cop(a, b, tag):
    d, = _fresh(tag, (a, b), 'divisor')
    return f'forall {d}. ({_dvd(d,a,tag+"a")}) -> ({_dvd(d,b,tag+"b")}) -> {d}=1'


def _mod(n, a, z, tag):
    u,v = _fresh(tag,(n,a,z),'left','right')
    return f'exists {u} {v}. ({a})+({n})*{u}=({z})+({n})*{v}'


def _pointwise_mod(n, b, c, d, e, k, tag):
    i,a,z = _fresh(tag,(n,b,c,d,e,k),'index','left','right')
    return (f'forall {i} {a} {z}. ({_lt(i,k,tag+"index")}) -> '
            f'({_at(b,c,i,a,tag+"left")}) -> ({_at(d,e,i,z,tag+"right")}) -> '
            f'({_mod(n,a,z,tag+"mod")})')


def _at(b, c, i, x, tag):
    return inherited_at(b, c, i, x, tag='jt_' + tag)


def _bounded(b, c, k, n, tag):
    i, a = _fresh(tag, (b, c, k, n), 'index', 'value')
    return (f'forall {i}. ({_lt(i,k,tag+"index")}) -> exists {a}. '
            + _and(_at(b,c,i,a,tag+'at'), _lt(a,n,tag+'value')))


def _equal(b, c, d, e, k, tag):
    i, a, z = _fresh(tag, (b,c,d,e,k), 'index','left','right')
    return (f'forall {i} {a} {z}. ({_lt(i,k,tag+"index")}) -> '
            f'({_at(b,c,i,a,tag+"left")}) -> ({_at(d,e,i,z,tag+"right")}) -> {a}={z}')


def _all_dvd(d, b, c, k, tag):
    i, a = _fresh(tag, (d,b,c,k), 'index','value')
    return (f'forall {i} {a}. ({_lt(i,k,tag+"index")}) -> '
            f'({_at(b,c,i,a,tag+"at")}) -> ({_dvd(d,a,tag+"divides")})')


def _primitive(n, b, c, k, tag):
    d, = _fresh(tag, (n,b,c,k), 'divisor')
    return (f'forall {d}. ({_dvd(d,n,tag+"modulus")}) -> '
            f'({_all_dvd(d,b,c,k,tag+"coordinates")}) -> {d}=1')


def _divisor_test(n, b, c, k, d, tag):
    return (f'({_dvd(d,n,tag+"modulus")}) -> '
            f'({_all_dvd(d,b,c,k,tag+"coordinates")}) -> ({d})=1')


def _primitive_up_to(n, b, c, k, length, tag):
    d, = _fresh(tag,(n,b,c,k,length),'divisor')
    return f'forall {d}. ({_lt(d,length,tag+"bound")}) -> ({_divisor_test(n,b,c,k,d,tag+"test")})'


def _enumeration(k, n, B, C, D, E, j, tag):
    """Outer streams B/C and D/E list the inner tuple codes and scales."""
    i, h, b, c, d, e = _fresh(tag,(k,n,B,C,D,E,j),'i','h','b','c','d','e')
    def entry(index, code, scale, suffix):
        return _and(_at(B,C,index,code,tag+suffix+'code'),
                    _at(D,E,index,scale,tag+suffix+'scale'))
    sound = (f'forall {i}. ({_lt(i,j,tag+"soundindex")}) -> exists {b} {c}. '
             + _and(entry(i,b,c,'sound'), _bounded(b,c,k,n,tag+'bound'),
                    _primitive(n,b,c,k,tag+'primitive')))
    complete = (f'forall {b} {c}. ({_bounded(b,c,k,n,tag+"inputbound")}) -> '
                f'({_primitive(n,b,c,k,tag+"inputprimitive")}) -> exists {i} {d} {e}. '
                + _and(_lt(i,j,tag+'completeindex'), entry(i,d,e,'complete'),
                       _equal(b,c,d,e,k,tag+'represented')))
    distinct = (f'forall {i} {h} {b} {c} {d} {e}. '
                f'({_lt(i,j,tag+"firstindex")}) -> ({_lt(h,j,tag+"secondindex")}) -> '
                f'({entry(i,b,c,"first")}) -> ({entry(h,d,e,"second")}) -> '
                f'({_equal(b,c,d,e,k,tag+"same")}) -> {i}={h}')
    return _and(sound, complete, distinct)


def _jordan(k, n, j, tag):
    B,C,D,E = _fresh(tag,(k,n,j),'codes','code_scale','scales','scale_scale')
    return _and(f'~(({k})=0)', f'~(({n})=0)',
                f'exists {B} {C} {D} {E}. {_enumeration(k,n,B,C,D,E,j,tag+"enum")}')


def primitive_tuple_relation(modulus, code, scale, length, *, tag):
    _public((modulus,code,scale,length),tag)
    return _primitive(modulus,code,scale,length,tag)


def tuple_equal_relation(code, scale, other_code, other_scale, length, *, tag):
    _public((code,scale,other_code,other_scale,length),tag)
    return _equal(code,scale,other_code,other_scale,length,tag)


def jordan_totient_relation(order, modulus, count, *, tag):
    _public((order,modulus,count),tag)
    return _jordan(order,modulus,count,tag)


def multiplicativity_contract():
    """Requested final contract, deliberately not an unproved theorem row."""
    return ('forall k a b. ' + _and('~(k=0)','~(a=0)','~(b=0)',_cop('a','b','targetcop'))
            + ' -> exists u v w. ' + _and(_jordan('k','a','u','targeta'),
              _jordan('k','b','v','targetb'),_jordan('k','a*b','w','targetab'),'w=u*v'))


def _call(name, *arguments):
    return (*(f'specialize {name} ({argument})' for argument in arguments), f'apply {name}')


def _intro(*names):
    return tuple('intro '+name for name in names)


def _parts(name, count):
    return tuple('cases '+name+'_right'*i for i in range(count-1))


def _part(name, count, index):
    return name+'_right'*index+('_left' if index<count-1 else '')


def _product_rows(spec):
    pair = _and('~(r=0)','~(s=0)',_dvd('r','a','paira'),_dvd('s','b','pairb'),'d=r*s')
    proof = _intro('a','b','B','C','k','ha','hb','hc','hpa','hpb','d','hd','hall')
    proof += ('have hn : ~(a*b=0)','intro hproductzero')+_call('mul_ne_zero','a','b')
    proof += ('exact ha','exact hb','exact hproductzero')
    proof += ('have hdpos : ~(d=0)','intro hz','apply hn','cases hd',
              'have hzero : d*x=0','rewrite hz')+_call('mul_zero_left','x')
    proof += ('trans d*x','exact hd_witness','exact hzero')
    proof += (f'have hp : exists r s. {pair}',)
    proof += _call('coprime_divisor_factor_pair_exists','a','b','d')
    proof += ('exact hdpos','exact hc','exact hd','cases hp','cases hp_witness')
    proof += _parts('hp_witness_witness',5)
    for name, value, parent, index, other, comm in (
            ('hr','x','hpa',2,'x1',False),('hs','x1','hpb',3,'x',True)):
        proof += (f'have {name} : {value}=1',)+_call(parent,value)
        proof += ('exact '+_part('hp_witness_witness',5,index),)
        proof += _call('jordan_tuple_divisor_downward',value,'d','B','C','k')
        proof += ('exists '+other,)
        if comm:
            proof += ('have hcomm : x*x1=x1*x',)+_call('mul_comm','x','x1')
            proof += ('trans x*x1','exact '+_part('hp_witness_witness',5,4),'exact hcomm')
        else:
            proof += ('exact '+_part('hp_witness_witness',5,4),)
        proof += ('exact hall',)
    proof += ('trans x*x1','exact '+_part('hp_witness_witness',5,4),'rewrite hr','rewrite hs')
    proof += _call('one_mul','1')
    return (
        spec('jordan_primitive_tuple_coprime_product',
             f'forall a b B C k. ~(a=0) -> ~(b=0) -> ({_cop("a","b","productcop")}) -> '
             f'({_primitive("a","B","C","k","producta")}) -> '
             f'({_primitive("b","B","C","k","productb")}) -> '
             f'({_primitive("a*b","B","C","k","productab")})',
             ('mul_ne_zero','mul_zero_left','coprime_divisor_factor_pair_exists',
              'jordan_tuple_divisor_downward','mul_comm','one_mul'),proof,
             'Actual coprime divisor decomposition proves primitivity for the product modulus.'),
        spec('jordan_primitive_tuple_product_components',
             f'forall a b B C k. ({_primitive("a*b","B","C","k","componentab")}) -> '
             +_and(_primitive('a','B','C','k','componenta'),_primitive('b','B','C','k','componentb')),
             ('jordan_primitive_tuple_divisor_modulus','mul_comm'),
             _intro('a','b','B','C','k','h')+('split',)
             +_call('jordan_primitive_tuple_divisor_modulus','a','a*b','B','C','k')
             +('exists b','refl','exact h')
             +_call('jordan_primitive_tuple_divisor_modulus','b','a*b','B','C','k')
             +('exists a',)+_call('mul_comm','a','b')+('exact h',),
             'Both primitive projections follow even without coprimality of the moduli.'),
        spec('jordan_divisibility_congruence_transport',
             f'forall n d a z. ({_dvd("d","n","congdivisor")}) -> '
             f'({_dvd("d","a","congsource")}) -> ({_mod("n","a","z","congmod")}) -> '
             f'({_dvd("d","z","congtarget")})',
             ('linear_congruence_zero_residue_divides','mod_eq_trans','mod_eq_symm',
              'mod_eq_of_mod_eq_multiple','dvd_to_mod_zero'),
             _intro('n','d','a','z','hdn','hda','hm')
             +_call('linear_congruence_zero_residue_divides','d','z')
             +_call('mod_eq_trans','d','z','a','0')+_call('mod_eq_symm','d','a','z')
             +_call('mod_eq_of_mod_eq_multiple','d','n','a','z')
             +('exact hdn','exact hm')+_call('dvd_to_mod_zero','d','a')+('exact hda',),
             'A genuine common modulus divisor survives balanced congruence, including divisor zero.'),
        spec('jordan_tuple_congruence_symm',
             f'forall n b c d e k. ({_pointwise_mod("n","b","c","d","e","k","msource")}) -> '
             f'({_pointwise_mod("n","d","e","b","c","k","mtarget")})',('mod_eq_symm',),
             _intro('n','b','c','d','e','k','h','i','a','z','hi','ha','hz')
             +_call('mod_eq_symm','n','z','a')+_call('h','i','z','a')
             +('exact hi','exact hz','exact ha'),
             'Pointwise balanced congruence is symmetric on every finite prefix.'),
        spec('jordan_primitive_tuple_congruence_transport',
             f'forall n b c d e k. ({_pointwise_mod("n","b","c","d","e","k","primmod")}) -> '
             f'({_primitive("n","b","c","k","primmodsource")}) -> '
             f'({_primitive("n","d","e","k","primmodtarget")})',
             ('beta_at_exists','jordan_divisibility_congruence_transport','mod_eq_symm'),
             _intro('n','b','c','d','e','k','hm','hp','q','hqn','hall')
             +_call('hp','q')+('exact hqn',)+_intro('i','a','hi','ha')
             +(f'have hz : exists z. {_at("d","e","i","z","primmodactual")}',)
             +_call('beta_at_exists','d','e','i')+('cases hz',)
             +_call('jordan_divisibility_congruence_transport','n','q','x','a')
             +('exact hqn',)+_call('hall','i','x')+('exact hi','exact hz_witness')
             +_call('mod_eq_symm','n','a','x')+_call('hm','i','a','x')
             +('exact hi','exact ha','exact hz_witness'),
             'Primitivity is invariant under actual coordinatewise residue transport, not field evaluation.'),
    )


def _decision_rows(spec):
    empty = _intro('d','b','c','i','a','hi','ha')+('exfalso',)
    empty += _call('lt_not_le','i','0')+('exact hi',)+_call('zero_le','i')

    extend = _intro('d','b','c','k','a','hprefix','ha','hda','i','z','hi','hz')
    extend += (f'have hcases : i=k \\/ ({_lt("i","k","allcases")})',)
    extend += _call('finite_lt_succ_eq_or_lt','k','i')+('exact hi','cases hcases','have heq : z=a')
    extend += _call('beta_at_unique','b','c','k','z','a')
    extend += ('rewrite hcases_left at hz','rewrite hcases_left at hz','exact hz','exact ha','rewrite <- heq at hda','exact hda')
    extend += _call('hprefix','i','z')+('exact hcases_right','exact hz')

    decision = _intro('d','b','c')+('induction k','left',)+_call('jordan_tuple_all_divisible_empty','d','b','c')
    decision += (f'have ha : exists a. {_at("b","c","k","a","alllast")}',)
    decision += _call('beta_at_exists','b','c','k')+('cases ha',)
    decision += (f'have hd : ({_dvd("d","x","allyes")}) \\/ ~({_dvd("d","x","allno")})',)
    decision += _call('multiple_decidable','d','x')+('cases IH','cases hd','left')
    decision += _call('jordan_tuple_all_divisible_extend','d','b','c','k','x')
    decision += ('exact IH_left','exact ha_witness','exact hd_left','right','intro h','apply hd_right')
    decision += _call('h','k','x')+_call('le_refl','S k')+('exact ha_witness','right','intro h','apply IH_right')
    decision += _intro('i','a','hi','hat')+_call('h','i','a')+_call('le_succ','S i','k')+('exact hi','exact hat')

    leaf = _intro('n','b','c','k','d')+('have heq : d=1 \\/ ~(d=1)',)
    leaf += _call('eq_decidable','d','1')+('cases heq','left',)+_intro('hd','hall')+('exact heq_left',)
    leaf += (f'have hd : ({_dvd("d","n","leafyes")}) \\/ ~({_dvd("d","n","leafno")})',)
    leaf += _call('multiple_decidable','d','n')+('cases hd',)
    leaf += (f'have hall : ({_all_dvd("d","b","c","k","leafallyes")}) \\/ ~({_all_dvd("d","b","c","k","leafallno")})',)
    leaf += _call('jordan_tuple_all_divisible_decidable','d','b','c','k')+('cases hall','right','intro h','apply heq_right','apply h','exact hd_left','exact hall_left')
    leaf += ('left',)+_intro('hdiv','hcoords')+('exfalso','apply hall_right','exact hcoords')
    leaf += ('left',)+_intro('hdiv','hcoords')+('exfalso','apply hd_right','exact hdiv')

    bounded = _intro('n','b','c','k')+('induction L','left',)+_intro('d','hd','hdiv','hall')
    bounded += ('exfalso',)+_call('lt_not_le','d','0')+('exact hd',)+_call('zero_le','d')
    bounded += (f'have ht : ({_divisor_test("n","b","c","k","L","boundedyes")}) \\/ ~({_divisor_test("n","b","c","k","L","boundedno")})',)
    bounded += _call('jordan_tuple_divisor_test_decidable','n','b','c','k','L')+('cases IH','cases ht','left',)
    bounded += _intro('d','hd')+(f'have hc : d=L \\/ ({_lt("d","L","boundedcases")})',)
    bounded += _call('finite_lt_succ_eq_or_lt','L','d')+('exact hd','cases hc',)
    # Rewriting the value in a divisor test has one occurrence in its modulus
    # divisor, one in the conclusion and one in each coordinate-divisor clause.
    bounded += _intro('hdiv','hall')+('have heq : L=1','apply ht_left','rewrite <- hc_left','exact hdiv')
    # The next goal is L|a; carry the actual d=L equality explicitly.
    bounded += _intro('i','a','hi','ha')+('rewrite <- hc_left',)+_call('hall','i','a')+('exact hi','exact ha','trans L','exact hc_left','exact heq')
    bounded += _intro('hdiv','hall')+_call('IH_left','d')+('exact hc_right','exact hdiv','exact hall')
    bounded += ('right','intro h','apply ht_right')+_intro('hdiv','hall')
    bounded += _call('h','L')+_call('le_refl','S L')+('exact hdiv','exact hall')
    bounded += ('right','intro h','apply IH_right')+_intro('d','hd','hdiv','hall')
    bounded += _call('h','d')+_call('le_succ','S d','L')+('exact hd','exact hdiv','exact hall')

    primitive = _intro('n','b','c','k','hn')
    primitive += (f'have hd : ({_primitive_up_to("n","b","c","k","S n","primitiveyes")}) \\/ ~({_primitive_up_to("n","b","c","k","S n","primitiveno")})',)
    primitive += _call('jordan_tuple_primitive_bounded_decidable','n','b','c','k','S n')+('cases hd','left',)+_intro('d','hdiv','hall')
    primitive += _call('hd_left','d')
    primitive += ('have hb : exists g. g+d=n',)+_call('divisor_le_nonzero','d','n')+('exact hn','exact hdiv','cases hb','exists x','trans S (x+d)','rewrite PA4','refl','congr','exact hb_witness','exact hdiv','exact hall')
    primitive += ('right','intro hp','apply hd_right')+_intro('d','hbound','hdiv','hall')
    primitive += _call('hp','d')+('exact hdiv','exact hall')
    return (
        spec('jordan_tuple_all_divisible_empty',f'forall d b c. {_all_dvd("d","b","c","0","allempty")}',('lt_not_le','zero_le'),empty,
             'Every divisor vacuously divides all entries of an empty tuple.'),
        spec('jordan_tuple_all_divisible_extend',
             f'forall d b c k a. ({_all_dvd("d","b","c","k","allprefix")}) -> '
             f'({_at("b","c","k","a","allentry")}) -> ({_dvd("d","a","allvalue")}) -> '
             f'({_all_dvd("d","b","c","S k","allsuccessor")})',
             ('finite_lt_succ_eq_or_lt','beta_at_unique'),extend,
             'Adjoining an actually decoded divisible entry preserves common divisibility.'),
        spec('jordan_tuple_all_divisible_decidable',
             f'forall d b c k. ({_all_dvd("d","b","c","k","alldecyes")}) \\/ ~({_all_dvd("d","b","c","k","alldecno")})',
             ('jordan_tuple_all_divisible_empty','beta_at_exists','multiple_decidable','jordan_tuple_all_divisible_extend','le_refl','le_succ'),decision,
             'Finite induction decides common divisibility from genuine beta entries; no bounded-code oracle.'),
        spec('jordan_tuple_divisor_test_decidable',
             f'forall n b c k d. ({_divisor_test("n","b","c","k","d","leaftestyes")}) \\/ ~({_divisor_test("n","b","c","k","d","leaftestno")})',
             ('eq_decidable','multiple_decidable','jordan_tuple_all_divisible_decidable'),leaf,
             'Decide each actual common-divisor-one implication constructively.'),
        spec('jordan_tuple_primitive_bounded_decidable',
             f'forall n b c k L. ({_primitive_up_to("n","b","c","k","L","bounddec_yes")}) \\/ ~({_primitive_up_to("n","b","c","k","L","bounddec_no")})',
             ('lt_not_le','zero_le','jordan_tuple_divisor_test_decidable','finite_lt_succ_eq_or_lt','le_refl','le_succ'),bounded,
             'A finite sweep decides the primitive common-divisor condition up to any natural bound.'),
        spec('jordan_primitive_tuple_decidable',
             f'forall n b c k. ~(n=0) -> ({_primitive("n","b","c","k","decprimitiveyes")}) \\/ ~({_primitive("n","b","c","k","decprimitiveno")})',
             ('jordan_tuple_primitive_bounded_decidable','divisor_le_nonzero'),primitive,
             'At positive modulus every possible common divisor lies below S n, giving genuine tuple-predicate decidability.'),
    )


def make_jordan_totient_candidate_theorems(spec):
    return (
        spec('jordan_tuple_equal_refl',
             f'forall b c k. {_equal("b","c","b","c","k","refl")}',
             ('beta_at_unique',),
             _intro('b','c','k','i','a','z','hi','ha','hz')
             +_call('beta_at_unique','b','c','i','a','z')+('exact ha','exact hz'),
             'Equality is equality of decoded coordinates, not equality of beta codes.'),
        spec('jordan_tuple_equal_symm',
             f'forall b c d e k. ({_equal("b","c","d","e","k","symmsource")}) -> '
             f'({_equal("d","e","b","c","k","symmtarget")})', (),
             _intro('b','c','d','e','k','h','i','a','z','hi','ha','hz')
             +('have hreverse : z=a',)+_call('h','i','z','a')
             +('exact hi','exact hz','exact ha','symm','exact hreverse'),
             'Coordinate equality is symmetric without selecting canonical codes.'),
        spec('jordan_tuple_equal_trans',
             f'forall b c d e f g k. ({_equal("b","c","d","e","k","transfirst")}) -> '
             f'({_equal("d","e","f","g","k","transsecond")}) -> '
             f'({_equal("b","c","f","g","k","transresult")})', ('beta_at_exists',),
             _intro('b','c','d','e','f','g','k','h','hnext','i','a','z','hi','ha','hz')
             +(f'have hm : exists t. {_at("d","e","i","t","middle")}',)
             +_call('beta_at_exists','d','e','i')+('cases hm','have hleft : a=x')
             +_call('h','i','a','x')+('exact hi','exact ha','exact hm_witness')
             +('have hright : x=z',)+_call('hnext','i','x','z')
             +('exact hi','exact hm_witness','exact hz','trans x','exact hleft','exact hright'),
             'A real decoded middle coordinate witnesses transitivity.'),
        spec('jordan_tuple_common_divisor_transport',
             f'forall q b c d e k. ({_equal("b","c","d","e","k","dvd_equal")}) -> '
             f'({_all_dvd("q","b","c","k","dvdsource")}) -> '
             f'({_all_dvd("q","d","e","k","dvdtarget")})',('beta_at_exists',),
             _intro('q','b','c','d','e','k','heq','hdiv','i','z','hi','hz')
             +(f'have ha : exists a. {_at("b","c","i","a","dvdactual")}',)
             +_call('beta_at_exists','b','c','i')+('cases ha','have hval : x=z')
             +_call('heq','i','x','z')+('exact hi','exact ha_witness','exact hz','rewrite <- hval')
             +_call('hdiv','i','x')+('exact hi','exact ha_witness'),
             'Divisibility of all coordinates is extensional across tuple encodings.'),
        spec('jordan_primitive_tuple_transport',
             f'forall n b c d e k. ({_equal("b","c","d","e","k","pr_equal")}) -> '
             f'({_primitive("n","b","c","k","prsource")}) -> '
             f'({_primitive("n","d","e","k","prtarget")})',
             ('jordan_tuple_common_divisor_transport','jordan_tuple_equal_symm'),
             _intro('n','b','c','d','e','k','heq','hp','q','hq','hall')
             +_call('hp','q')+('exact hq',)
             +_call('jordan_tuple_common_divisor_transport','q','d','e','b','c','k')
             +_call('jordan_tuple_equal_symm','b','c','d','e','k')+('exact heq','exact hall'),
             'Primitive means common-divisor one and is independent of beta presentation.'),
        spec('jordan_primitive_tuple_divisor_modulus',
             f'forall n m b c k. ({_dvd("n","m","smalldivisor")}) -> '
             f'({_primitive("m","b","c","k","largemod")}) -> '
             f'({_primitive("n","b","c","k","smallmod")})',('multiple_trans',),
             _intro('n','m','b','c','k','hnm','hp','q','hqn','hall')
             +_call('hp','q')+_call('multiple_trans','n','q','m')
             +('exact hnm','exact hqn','exact hall'),
             'Primitivity descends from a modulus to a genuine divisor of it.'),
        spec('jordan_tuple_divisor_downward',
             f'forall q r b c k. ({_dvd("q","r","downfactor")}) -> '
             f'({_all_dvd("r","b","c","k","downsource")}) -> '
             f'({_all_dvd("q","b","c","k","downtarget")})',('multiple_trans',),
             _intro('q','r','b','c','k','hqr','hall','i','a','hi','ha')
             +_call('multiple_trans','r','q','a')+_call('hall','i','a')
             +('exact hi','exact ha','exact hqr'),
             'A divisor of a common coordinate divisor is again a common divisor.'),
        spec('jordan_primitive_tuple_modulus_one',
             f'forall b c k. {_primitive("1","b","c","k","one")}',('divisor_one',),
             _intro('b','c','k','q','hq','hall')+_call('divisor_one','q')+('exact hq',),
             'Every finite tuple is primitive modulo one, including the zero tuple.'),
        spec('jordan_order_zero_excluded',f'forall n j. ~({_jordan("0","n","j","zeroorder")})',(),
             _intro('n','j','h')+('cases h','apply h_left','refl'),
             'Jordan is intentionally restricted to positive tuple order.'),
        spec('jordan_modulus_zero_excluded',f'forall k j. ~({_jordan("k","0","j","zeromod")})',(),
             _intro('k','j','h')+('cases h','cases h_right','apply h_right_left','refl'),
             'Jordan never counts a purported finite complete residue system modulo zero.'),
    ) + _product_rows(spec) + _decision_rows(spec)


def _listed(b, c, k, B, C, D, E, j, tag):
    """An actual list position represents the tuple; codes need not agree."""
    i,d,e = _fresh(tag,(b,c,k,B,C,D,E,j),'index','code','scale')
    return (f'exists {i} {d} {e}. '+_and(_lt(i,j,tag+'index'),
        _and(_at(B,C,i,d,tag+'code'),_at(D,E,i,e,tag+'scale')),
        _equal(b,c,d,e,k,tag+'equal')))


def _scan(k, n, c, limit, B, C, D, E, j, tag):
    """A duplicate-free list covering admissible fixed-scale codes below limit.

    This is an induction invariant, not the definition of Jordan and not a
    claim that an enumeration exists. No count/product equation occurs here.
    """
    i,h,b,e,d,f,z = _fresh(tag,(k,n,c,limit,B,C,D,E,j),
                          'i','h','b','e','d','f','z')
    def entry(index, code, scale, suffix):
        return _and(_at(B,C,index,code,tag+suffix+'code'),
                    _at(D,E,index,scale,tag+suffix+'scale'))
    sound=(f'forall {i}. ({_lt(i,j,tag+"soundindex")}) -> exists {b} {e}. '+
        _and(entry(i,b,e,'sound'),_bounded(b,e,k,n,tag+'bound'),
             _primitive(n,b,e,k,tag+'primitive')))
    distinct=(f'forall {i} {h} {b} {e} {d} {f}. '
        f'({_lt(i,j,tag+"firstindex")}) -> ({_lt(h,j,tag+"secondindex")}) -> '
        f'({entry(i,b,e,"first")}) -> ({entry(h,d,f,"second")}) -> '
        f'({_equal(b,e,d,f,k,tag+"same")}) -> {i}={h}')
    cover=(f'forall {z}. ({_lt(z,limit,tag+"codeindex")}) -> '
        f'({_bounded(z,c,k,n,tag+"inputbound")}) -> '
        f'({_primitive(n,z,c,k,tag+"inputprimitive")}) -> '
        f'({_listed(z,c,k,B,C,D,E,j,tag+"listed")})')
    return _and(sound,distinct,cover)


def tuple_listed_relation(code, scale, order, codes, codes_scale,
                          scales, scales_scale, length, *, tag):
    args=(code,scale,order,codes,codes_scale,scales,scales_scale,length)
    _public(args,tag)
    return _listed(*args,tag)


def tuple_scan_relation(order, modulus, fixed_scale, limit, codes,
                        codes_scale, scales, scales_scale, length, *, tag):
    args=(order,modulus,fixed_scale,limit,codes,codes_scale,scales,scales_scale,length)
    _public(args,tag)
    return _scan(*args,tag)


def make_jordan_enumeration_candidate_theorems(spec):
    """New finite-sweep prerequisites; scripts remain conditional candidates."""
    empty=_intro('b','c','d','e','i','a','z','hi','ha','hz')+('exfalso',)
    empty+=_call('lt_not_le','i','0')+('exact hi',)+_call('zero_le','i')

    drop=_intro('b','c','d','e','k','h','i','a','z','hi','ha','hz')
    drop+=_call('h','i','a','z')+_call('le_succ','S i','k')
    drop+=('exact hi','exact ha','exact hz')

    extend=_intro('b','c','d','e','k','a','z','hp','ha','hz','heq','i','r','s','hi','hr','hs')
    extend+=(f'have hc : i=k \\/ ({_lt("i","k","eqextendcases")})',)
    extend+=_call('finite_lt_succ_eq_or_lt','k','i')+('exact hi','cases hc')
    extend+=('have hleft : r=a',)+_call('beta_at_unique','b','c','k','r','a')
    extend+=('rewrite hc_left at hr','rewrite hc_left at hr','exact hr','exact ha')
    extend+=('have hright : s=z',)+_call('beta_at_unique','d','e','k','s','z')
    extend+=('rewrite hc_left at hs','rewrite hc_left at hs','exact hs','exact hz')
    extend+=('rewrite hleft','rewrite hright','exact heq')
    extend+=_call('hp','i','r','s')+('exact hc_right','exact hr','exact hs')

    decision=_intro('b','c','d','e')+('induction k','left',)
    decision+=_call('jordan_tuple_equal_empty','b','c','d','e')
    decision+=(f'have ha : exists a. {_at("b","c","k","a","eqdecisiona")}',)
    decision+=_call('beta_at_exists','b','c','k')+('cases ha',)
    decision+=(f'have hz : exists z. {_at("d","e","k","z","eqdecisionz")}',)
    decision+=_call('beta_at_exists','d','e','k')+('cases hz','have heq : x=x1 \\/ ~(x=x1)')
    decision+=_call('eq_decidable','x','x1')+('cases IH','cases heq','left')
    decision+=_call('jordan_tuple_equal_extend','b','c','d','e','k','x','x1')
    decision+=('exact IH_left','exact ha_witness','exact hz_witness','exact heq_left')
    decision+=('right','intro h','apply heq_right')+_call('h','k','x','x1')
    decision+=_call('le_refl','S k')+('exact ha_witness','exact hz_witness')
    decision+=('right','intro h','apply IH_right')
    decision+=_call('jordan_tuple_equal_drop_last','b','c','d','e','k')+('exact h',)

    listed_empty=_intro('b','c','k','B','C','D','E','h')
    listed_empty+=('cases h','cases h_witness','cases h_witness_witness')
    listed_empty+=_parts('h_witness_witness_witness',3)
    listed_empty+=_call('lt_not_le','x','0')+('exact h_witness_witness_witness_left',)
    listed_empty+=_call('zero_le','x')

    listed_lift=_intro('b','c','k','B','C','D','E','j','h')
    listed_lift+=('cases h','cases h_witness','cases h_witness_witness')
    listed_lift+=_parts('h_witness_witness_witness',3)
    listed_lift+=('exists x','exists x1','exists x2','split')
    listed_lift+=_call('le_succ','S x','j')+('exact h_witness_witness_witness_left',)
    listed_lift+=('split','exact h_witness_witness_witness_right_left',
                  'exact h_witness_witness_witness_right_right')

    listed_decide=_intro('b','c','k','B','C','D','E')+('induction j','right','intro hempty')
    listed_decide+=_call('jordan_tuple_listed_empty','b','c','k','B','C','D','E')+('exact hempty',)
    listed_decide+=('cases IH','left',)
    listed_decide+=_call('jordan_tuple_listed_lift','b','c','k','B','C','D','E','j')+('exact IH_left',)
    listed_decide+=(f'have hd : exists d. {_at("B","C","j","d","listedlastcode")}',)
    listed_decide+=_call('beta_at_exists','B','C','j')+('cases hd',)
    listed_decide+=(f'have he : exists e. {_at("D","E","j","e","listedlastscale")}',)
    listed_decide+=_call('beta_at_exists','D','E','j')+('cases he',)
    listed_decide+=(f'have heq : ({_equal("b","c","x","x1","k","listedyes")}) \\/ ~({_equal("b","c","x","x1","k","listedno")})',)
    listed_decide+=_call('jordan_tuple_equal_decidable','b','c','x','x1','k')+('cases heq','left',)
    listed_decide+=('exists j','exists x','exists x1','split')+_call('le_refl','S j')
    listed_decide+=('split','split','exact hd_witness','exact he_witness','exact heq_left')
    listed_decide+=('right','intro h','cases h','cases h_witness','cases h_witness_witness')
    listed_decide+=_parts('h_witness_witness_witness',3)
    listed_decide+=(f'have hc : x2=j \\/ ({_lt("x2","j","listedcase")})',)
    listed_decide+=_call('finite_lt_succ_eq_or_lt','j','x2')
    listed_decide+=('exact h_witness_witness_witness_left','cases hc',
                    'cases h_witness_witness_witness_right_left','have hdval : x3=x')
    listed_decide+=_call('beta_at_unique','B','C','j','x3','x')
    listed_decide+=('rewrite hc_left at h_witness_witness_witness_right_left_left',)*2
    listed_decide+=('exact h_witness_witness_witness_right_left_left','exact hd_witness','have heval : x4=x1')
    listed_decide+=_call('beta_at_unique','D','E','j','x4','x1')
    listed_decide+=('rewrite hc_left at h_witness_witness_witness_right_left_right',)*2
    listed_decide+=('exact h_witness_witness_witness_right_left_right','exact he_witness','apply heq_right')
    # Code and scale occur only in the right-hand actual beta clause.
    listed_decide+=('rewrite hdval at h_witness_witness_witness_right_right',
                    'rewrite heval at h_witness_witness_witness_right_right',
                    'rewrite heval at h_witness_witness_witness_right_right')
    listed_decide+=('exact h_witness_witness_witness_right_right','apply IH_right',
                    'exists x2','exists x3','exists x4','split','exact hc_right','split',
                    'exact h_witness_witness_witness_right_left','exact h_witness_witness_witness_right_right')

    scan_empty=_intro('k','n','c','B','C','D','E')+('split',)+_intro('i','hi')+('exfalso',)
    scan_empty+=_call('lt_not_le','i','0')+('exact hi',)+_call('zero_le','i')+('split',)
    scan_empty+=_intro('i','h','b','e','d','f','hi','hh','he','hf','heq')+('exfalso',)
    scan_empty+=_call('lt_not_le','i','0')+('exact hi',)+_call('zero_le','i')
    scan_empty+=_intro('z','hz','hb','hp')+('exfalso',)
    scan_empty+=_call('lt_not_le','z','0')+('exact hz',)+_call('zero_le','z')

    return (
        spec('jordan_tuple_equal_empty',f'forall b c d e. {_equal("b","c","d","e","0","eqempty")}',
             ('lt_not_le','zero_le'),empty,'All actual empty tuples are coordinatewise equal.'),
        spec('jordan_tuple_equal_drop_last',f'forall b c d e k. ({_equal("b","c","d","e","S k","eqdropsource")}) -> ({_equal("b","c","d","e","k","eqdroptarget")})',
             ('le_succ',),drop,'Restrict coordinate equality to the actual predecessor prefix.'),
        spec('jordan_tuple_equal_extend',f'forall b c d e k a z. ({_equal("b","c","d","e","k","eqextendprefix")}) -> ({_at("b","c","k","a","eqextendleft")}) -> ({_at("d","e","k","z","eqextendright")}) -> a=z -> ({_equal("b","c","d","e","S k","eqextendtarget")})',
             ('finite_lt_succ_eq_or_lt','beta_at_unique'),extend,'Extend equal prefixes using two actual equal last entries.'),
        spec('jordan_tuple_equal_decidable',f'forall b c d e k. ({_equal("b","c","d","e","k","eqyes")}) \\/ ~({_equal("b","c","d","e","k","eqno")})',
             ('jordan_tuple_equal_empty','beta_at_exists','eq_decidable','jordan_tuple_equal_extend','le_refl','jordan_tuple_equal_drop_last'),decision,
             'Inductively decide decoded coordinate equality, never equality of beta codes.'),
        spec('jordan_tuple_listed_empty',f'forall b c k B C D E. ~({_listed("b","c","k","B","C","D","E","0","listedempty")})',
             ('lt_not_le','zero_le'),listed_empty,'An empty actual outer list contains no representative.'),
        spec('jordan_tuple_listed_lift',f'forall b c k B C D E j. ({_listed("b","c","k","B","C","D","E","j","listedliftold")}) -> ({_listed("b","c","k","B","C","D","E","S j","listedliftnew")})',
             ('le_succ',),listed_lift,'An existing list position remains below the successor bound.'),
        spec('jordan_tuple_listed_decidable',f'forall b c k B C D E j. ({_listed("b","c","k","B","C","D","E","j","listedyes")}) \\/ ~({_listed("b","c","k","B","C","D","E","j","listedno")})',
             ('jordan_tuple_listed_empty','jordan_tuple_listed_lift','beta_at_exists','jordan_tuple_equal_decidable','le_refl','finite_lt_succ_eq_or_lt','beta_at_unique'),listed_decide,
             'Finite list membership is decided by actual outer entries and coordinate equality.'),
        spec('jordan_tuple_scan_empty',f'forall k n c B C D E. {_scan("k","n","c","0","B","C","D","E","0","scanempty")}',
             ('lt_not_le','zero_le'),scan_empty,'Empty scan has soundness, no duplicate positions, and vacuous code coverage.'),
    )


def _prefix(b,c,d,e,k,tag):
    i,a=_fresh(tag,(b,c,d,e,k),'index','value')
    return (f'forall {i} {a}. ({_lt(i,k,tag+"index")}) -> '
            f'({_at(b,c,i,a,tag+"old")}) -> ({_at(d,e,i,a,tag+"new")})')


def _representatives(k,n,c,T,tag):
    b,e,z=_fresh(tag,(k,n,c,T),'code','scale','representative')
    return (f'forall {b} {e}. ({_bounded(b,e,k,n,tag+"bound")}) -> exists {z}. '
            +_and(_lt(z,T,tag+'index'),_equal(b,e,z,c,k,tag+'equal')))


def make_jordan_enumeration_bridge_candidate_theorems(spec):
    """Actual prefix extensions and the scan-to-Jordan cardinality bridge.

    In particular the conditional scan-completion lemma does not assert that
    the required scan exists. That totality remains a separate native goal.
    """
    prefix=_intro('b','c','d','e','k','h','i','a','z','hi','ha','hz')
    prefix+=_call('beta_at_unique','d','e','i','a','z')
    prefix+=_call('h','i','a')+('exact hi','exact ha','exact hz')

    entry=_intro('b','c','d','e','k','i','a','h','hi','ha')
    entry+=(f'have hz : exists z. {_at("d","e","i","z","equalentry")}',)
    entry+=_call('beta_at_exists','d','e','i')+('cases hz','have heq : a=x')
    entry+=_call('h','i','a','x')+('exact hi','exact ha','exact hz_witness',
                                  'rewrite heq','rewrite heq','exact hz_witness')

    bounded=_intro('b','c','d','e','k','n','heq','hb','i','hi')
    bounded+=(f'have ha : exists a. {_and(_at("b","c","i","a","boundtransport"),_lt("a","n","boundvalue"))}',)
    bounded+=_call('hb','i')+('exact hi','cases ha','cases ha_witness','exists x','split')
    bounded+=_call('jordan_tuple_equal_entry','b','c','d','e','k','i','x')
    bounded+=('exact heq','exact hi','exact ha_witness_left','exact ha_witness_right')

    outer=_intro('B','C','D','E','j','b','c')
    outer+=(f'have hc : exists u v. {_and(_at("u","v","j","b","appendcode"),_prefix("B","C","u","v","j","appendcodeprefix"))}',)
    outer+=_call('beta_prefix_extend','j','B','C','b')+('cases hc','cases hc_witness','cases hc_witness_witness')
    outer+=(f'have hs : exists u v. {_and(_at("u","v","j","c","appendscale"),_prefix("D","E","u","v","j","appendscaleprefix"))}',)
    outer+=_call('beta_prefix_extend','j','D','E','c')+('cases hs','cases hs_witness','cases hs_witness_witness')
    outer+=('exists x','exists x1','exists x2','exists x3','split')
    outer+=_call('jordan_tuple_prefix_equal','B','C','x','x1','j')+('exact hc_witness_witness_right','split')
    outer+=_call('jordan_tuple_prefix_equal','D','E','x2','x3','j')
    outer+=('exact hs_witness_witness_right','split','exact hc_witness_witness_left','exact hs_witness_witness_left')

    listed=_intro('b','c','d','e','k','B','C','D','E','j','heq','hl')
    listed+=('cases hl','cases hl_witness','cases hl_witness_witness')
    listed+=_parts('hl_witness_witness_witness',3)
    listed+=('exists x','exists x1','exists x2','split','exact hl_witness_witness_witness_left',
             'split','exact hl_witness_witness_witness_right_left')
    listed+=_call('jordan_tuple_equal_trans','b','c','d','e','x1','x2','k')
    listed+=('exact heq','exact hl_witness_witness_witness_right_right')

    skip=_intro('k','n','c','t','B','C','D','E','j','hscan','hcurrent')
    skip+=_parts('hscan',3)+('split','exact hscan_left','split','exact hscan_right_left')
    skip+=_intro('z','hz','hb','hp')+(f'have hc : z=t \\/ ({_lt("z","t","scanskipcase")})',)
    skip+=_call('finite_lt_succ_eq_or_lt','t','z')+('exact hz','cases hc','rewrite hc_left',
              'apply hcurrent','rewrite hc_left at hb','exact hb','rewrite hc_left at hp','exact hp')
    skip+=_call('hscan_right_right','z')+('exact hc_right','exact hb','exact hp')

    finish=_intro('k','n','c','T','B','C','D','E','j','hbox','hscan')
    finish+=_parts('hscan',3)+('split','exact hscan_left','split')
    finish+=_intro('b','e','hb','hp')
    finish+=(f'have hz : exists z. {_and(_lt("z","T","finishbound"),_equal("b","e","z","c","k","finishequal"))}',)
    finish+=_call('hbox','b','e')+('exact hb','cases hz','cases hz_witness')
    finish+=_call('jordan_tuple_listed_equal_transport','b','e','x','c','k','B','C','D','E','j')
    finish+=('exact hz_witness_right',)+_call('hscan_right_right','x')+('exact hz_witness_left',)
    finish+=_call('jordan_tuple_bounded_transport','b','e','x','c','k','n')
    finish+=('exact hz_witness_right','exact hb')
    finish+=_call('jordan_primitive_tuple_transport','n','b','e','x','c','k')
    finish+=('exact hz_witness_right','exact hp','exact hscan_right_left')

    pack=_intro('k','n','c','T','B','C','D','E','j','hk','hn','hbox','hscan')
    pack+=('split','exact hk','split','exact hn','exists B','exists C','exists D','exists E')
    pack+=_call('jordan_tuple_scan_complete','k','n','c','T','B','C','D','E','j')
    pack+=('exact hbox','exact hscan')

    return (
        spec('jordan_tuple_prefix_equal',f'forall b c d e k. ({_prefix("b","c","d","e","k","prefixsource")}) -> ({_equal("b","c","d","e","k","prefixtarget")})',
             ('beta_at_unique',),prefix,'An actual one-way beta prefix extension preserves decoded coordinates.'),
        spec('jordan_tuple_equal_entry',f'forall b c d e k i a. ({_equal("b","c","d","e","k","entryequal")}) -> ({_lt("i","k","entryindex")}) -> ({_at("b","c","i","a","entrysource")}) -> ({_at("d","e","i","a","entrytarget")})',
             ('beta_at_exists',),entry,'Coordinate equality transports an actual beta entry with unchanged value.'),
        spec('jordan_tuple_bounded_transport',f'forall b c d e k n. ({_equal("b","c","d","e","k","boundequal")}) -> ({_bounded("b","c","k","n","boundsource")}) -> ({_bounded("d","e","k","n","boundtarget")})',
             ('jordan_tuple_equal_entry',),bounded,'The canonical coordinate bound is independent of tuple encoding.'),
        spec('jordan_tuple_outer_append_exists',f'forall B C D E j b c. exists U V W X. '+_and(
             _equal('B','C','U','V','j','outercodes'),_equal('D','E','W','X','j','outerscales'),
             _at('U','V','j','b','outerlastcode'),_at('W','X','j','c','outerlastscale')),
             ('beta_prefix_extend','jordan_tuple_prefix_equal'),outer,
             'Construct both outer beta streams after an append; no list witness is assumed.'),
        spec('jordan_tuple_listed_equal_transport',f'forall b c d e k B C D E j. ({_equal("b","c","d","e","k","listedtransport")}) -> ({_listed("d","e","k","B","C","D","E","j","listedsource")}) -> ({_listed("b","c","k","B","C","D","E","j","listedtarget")})',
             ('jordan_tuple_equal_trans',),listed,'List membership is a property of the represented coordinate tuple.'),
        spec('jordan_tuple_scan_skip',f'forall k n c t B C D E j. ({_scan("k","n","c","t","B","C","D","E","j","skipsource")}) -> '
             f'(({_bounded("t","c","k","n","skipcurrentbound")}) -> ({_primitive("n","t","c","k","skipcurrentprimitive")}) -> ({_listed("t","c","k","B","C","D","E","j","skipcurrentlisted")})) -> '
             f'({_scan("k","n","c","S t","B","C","D","E","j","skiptarget")})',
             ('finite_lt_succ_eq_or_lt',),skip,'Skip precisely when the current admissible tuple is already represented.'),
        spec('jordan_tuple_scan_complete',f'forall k n c T B C D E j. ({_representatives("k","n","c","T","completebox")}) -> ({_scan("k","n","c","T","B","C","D","E","j","completescan")}) -> ({_enumeration("k","n","B","C","D","E","j","completeenum")})',
             ('jordan_tuple_listed_equal_transport','jordan_tuple_bounded_transport','jordan_primitive_tuple_transport'),finish,
             'A completed duplicate-free scan of a genuine representative box is the independent enumeration graph.'),
        spec('jordan_totient_from_complete_scan',f'forall k n c T B C D E j. ~(k=0) -> ~(n=0) -> ({_representatives("k","n","c","T","jordanbox")}) -> ({_scan("k","n","c","T","B","C","D","E","j","jordanscan")}) -> ({_jordan("k","n","j","jordancount")})',
             ('jordan_tuple_scan_complete',),pack,'Package a genuinely completed scan as a Jordan cardinality, without assuming totality.'),
    )


def make_jordan_scan_candidate_theorems(spec):
    """The finite duplicate-removing scan and unconditional Jordan totality.

    These are draft ordinary scripts, not accepted facts. They must be replayed
    under the original kernel before any closure or multiplicativity use.
    """
    proof=_intro('k','n','c','t','B','C','D','E','j','hscan','hb','hp','hfresh')
    extension=_and(_equal('B','C','U','V','j','scanappendcodes'),
                   _equal('D','E','W','X','j','scanappendscales'),
                   _at('U','V','j','t','scanappendlastcode'),
                   _at('W','X','j','c','scanappendlastscale'))
    proof+=(f'have hext : exists U V W X. {extension}',)
    proof+=_call('jordan_tuple_outer_append_exists','B','C','D','E','j','t','c')
    proof+=('cases hext','cases hext_witness','cases hext_witness_witness','cases hext_witness_witness_witness')
    node='hext_witness_witness_witness_witness'
    proof+=_parts(node,4)+_parts('hscan',3)
    codes,scales,lastcode,lastscale=(_part(node,4,i) for i in range(4))
    proof+=(f'have hcodesback : {_equal("x","x1","B","C","j","scanappendcodesback")}',)
    proof+=_call('jordan_tuple_equal_symm','B','C','x','x1','j')+('exact '+codes,)
    proof+=(f'have hscalesback : {_equal("x2","x3","D","E","j","scanappendscalesback")}',)
    proof+=_call('jordan_tuple_equal_symm','D','E','x2','x3','j')+('exact '+scales,)

    def transfer(index,b,e,bound,entry,back=False):
        args=(('x','x1','B','C','hcodesback'),('x2','x3','D','E','hscalesback')) if back else (
              ('B','C','x','x1',codes),('D','E','x2','x3',scales))
        result=('split',)
        for (u,v,w,z,heq),value,suffix in zip(args,(b,e),('_left','_right')):
            result+=_call('jordan_tuple_equal_entry',u,v,w,z,'j',index,value)
            result+=('exact '+heq,'exact '+bound,'exact '+entry+suffix)
        return result

    proof+=('exists x','exists x1','exists x2','exists x3','split')
    # Soundness: an old index transports its two actual entries; the new
    # index has the explicitly appended code and scale.
    proof+=_intro('i','hi')+(f'have hic : i=j \\/ ({_lt("i","j","appendindex")})',)
    proof+=_call('finite_lt_succ_eq_or_lt','j','i')+('exact hi','cases hic','exists t','exists c','split','split')
    proof+=('rewrite hic_left','rewrite hic_left','exact '+lastcode,
             'rewrite hic_left','rewrite hic_left','exact '+lastscale,'split','exact hb','exact hp')
    soundvalue=_and(_and(_at('B','C','i','b','appendoldcode'),_at('D','E','i','e','appendoldscale')),
                    _bounded('b','e','k','n','appendoldbound'),_primitive('n','b','e','k','appendoldprimitive'))
    proof+=(f'have hvalue : exists b e. {soundvalue}',)+_call('hscan_left','i')
    proof+=('exact hic_right','cases hvalue','cases hvalue_witness')
    proof+=_parts('hvalue_witness_witness',3)+('cases hvalue_witness_witness_left','exists x4','exists x5','split')
    proof+=transfer('i','x4','x5','hic_right','hvalue_witness_witness_left')
    proof+=('split','exact hvalue_witness_witness_right_left','exact hvalue_witness_witness_right_right','split')

    # Distinctness splits the two index bounds. A mixed old/new pair would
    # witness the forbidden old membership of the appended tuple.
    proof+=_intro('i','h','b','e','d','f','hi','hh','hfirst','hsecond','heq')
    proof+=('cases hfirst','cases hsecond',f'have hic : i=j \\/ ({_lt("i","j","appendfirstcase")})')
    proof+=_call('finite_lt_succ_eq_or_lt','j','i')+('exact hi',)
    proof+=(f'have hhc : h=j \\/ ({_lt("h","j","appendsecondcase")})',)
    proof+=_call('finite_lt_succ_eq_or_lt','j','h')+('exact hh','cases hic','cases hhc')
    proof+=('trans j','exact hic_left','symm','exact hhc_left')

    def last_value(index,value,stream_code,stream_scale,entry,last,eqname,indexeq):
        target='t' if stream_code=='x' else 'c'
        return (f'have {eqname} : {value}={target}',)+_call(
            'beta_at_unique',stream_code,stream_scale,'j',value,target)+(
            f'rewrite {indexeq} at {entry}',f'rewrite {indexeq} at {entry}',
            'exact '+entry,'exact '+last)

    proof+=last_value('i','b','x','x1','hfirst_left',lastcode,'hbval','hic_left')
    proof+=last_value('i','e','x2','x3','hfirst_right',lastscale,'heval','hic_left')
    proof+=('exfalso','apply hfresh','exists h','exists d','exists f','split','exact hhc_right','split')
    proof+=transfer('h','d','f','hhc_right','hsecond',True)
    proof+=('rewrite hbval at heq','rewrite heval at heq','rewrite heval at heq','exact heq')

    proof+=('cases hhc',)
    proof+=last_value('h','d','x','x1','hsecond_left',lastcode,'hdval','hhc_left')
    proof+=last_value('h','f','x2','x3','hsecond_right',lastscale,'hfval','hhc_left')
    proof+=('exfalso','apply hfresh','exists i','exists b','exists e','split','exact hic_right','split')
    proof+=transfer('i','b','e','hic_right','hfirst',True)
    proof+=_call('jordan_tuple_equal_symm','b','e','t','c','k')
    proof+=('rewrite hdval at heq','rewrite hfval at heq','rewrite hfval at heq','exact heq')
    proof+=_call('hscan_right_left','i','h','b','e','d','f')+('exact hic_right','exact hhc_right')
    proof+=transfer('i','b','e','hic_right','hfirst',True)
    proof+=transfer('h','d','f','hhc_right','hsecond',True)+('exact heq',)

    # Coverage: the new code uses the last position; every older covered code
    # keeps its actual old position through the fresh outer encodings.
    proof+=_intro('z','hz','hzb','hzp')+(f'have hzc : z=t \\/ ({_lt("z","t","appendcovercase")})',)
    proof+=_call('finite_lt_succ_eq_or_lt','t','z')+('exact hz','cases hzc','rewrite hzc_left')
    proof+=('exists j','exists t','exists c','split')+_call('le_refl','S j')
    proof+=('split','split','exact '+lastcode,'exact '+lastscale)
    proof+=_call('jordan_tuple_equal_refl','t','c','k')
    proof+=(f'have hold : {_listed("z","c","k","B","C","D","E","j","appendoldlisted")}',)
    proof+=_call('hscan_right_right','z')+('exact hzc_right','exact hzb','exact hzp')
    proof+=('cases hold','cases hold_witness','cases hold_witness_witness')
    proof+=_parts('hold_witness_witness_witness',3)+('cases hold_witness_witness_witness_right_left',)
    proof+=('exists x4','exists x5','exists x6','split')+_call('le_succ','S x4','j')
    proof+=('exact hold_witness_witness_witness_left','split')
    proof+=transfer('x4','x5','x6','hold_witness_witness_witness_left','hold_witness_witness_witness_right_left')
    proof+=('exact hold_witness_witness_witness_right_right',)

    total=_intro('k','n','c','hn')+('induction t',)
    total+=('exists 0',)*5+_call('jordan_tuple_scan_empty','k','n','c','0','0','0','0')
    total+=('cases IH','cases IH_witness','cases IH_witness_witness','cases IH_witness_witness_witness','cases IH_witness_witness_witness_witness')
    old='IH_witness_witness_witness_witness_witness'
    total+=(f'have hb : ({_bounded("t","c","k","n","scantotalyes")}) \\/ ~({_bounded("t","c","k","n","scantotalno")})',)
    total+=_call('matrix_rank_bounded_prefix_decidable','t','c','k','n')+('cases hb',)
    total+=(f'have hp : ({_primitive("n","t","c","k","scanprimyes")}) \\/ ~({_primitive("n","t","c","k","scanprimno")})',)
    total+=_call('jordan_primitive_tuple_decidable','n','t','c','k')+('exact hn','cases hp')
    total+=(f'have hl : ({_listed("t","c","k","x","x1","x2","x3","x4","scanlistedyes")}) \\/ ~({_listed("t","c","k","x","x1","x2","x3","x4","scanlistedno")})',)
    total+=_call('jordan_tuple_listed_decidable','t','c','k','x','x1','x2','x3','x4')+('cases hl',)
    def skip_current(kind):
        result=tuple('exists '+v for v in ('x','x1','x2','x3','x4'))
        result+=_call('jordan_tuple_scan_skip','k','n','c','t','x','x1','x2','x3','x4')+('exact '+old,)
        result+=_intro('hbound','hprimitive')
        if kind=='listed':return result+('exact hl_left',)
        if kind=='primitive':return result+('exfalso','apply hp_right','exact hprimitive')
        return result+('exfalso','apply hb_right','exact hbound')
    total+=skip_current('listed')
    total+=(f'have hnew : exists U V W X. {_scan("k","n","c","S t","U","V","W","X","S x4","scantotalnew")}',)
    total+=_call('jordan_tuple_scan_append','k','n','c','t','x','x1','x2','x3','x4')
    total+=('exact '+old,'exact hb_left','exact hp_left','exact hl_right')
    total+=('cases hnew','cases hnew_witness','cases hnew_witness_witness','cases hnew_witness_witness_witness')
    total+=tuple('exists '+v for v in ('x5','x6','x7','x8','S x4'))+('exact hnew_witness_witness_witness_witness',)
    total+=skip_current('primitive')+skip_current('bound')

    # This is the exact existing box theorem's one-way prefix statement,
    # followed by a proved conversion to coordinate equality.
    boxclause=('forall b e. ('+_bounded('b','e','k','n','boxinput')+') -> exists z. '+
               _and(_lt('z','T','boxindex'),_prefix('b','e','z','c','k','boxprefix')))
    box=_intro('k','n')+(f'have hbox : exists c T. {_and("~(T=0)",boxclause)}',)
    box+=_call('matrix_rank_uniform_beta_prefix_box_exists','k','n')
    box+=('cases hbox','cases hbox_witness','cases hbox_witness_witness','exists x','exists x1')
    box+=_intro('b','e','hb')
    box+=(f'have hz : exists z. {_and(_lt("z","x1","recodeindex"),_prefix("b","e","z","x","k","recodeprefix"))}',)
    box+=_call('hbox_witness_witness_right','b','e')+('exact hb','cases hz','cases hz_witness','exists x2','split','exact hz_witness_left')
    box+=_call('jordan_tuple_prefix_equal','b','e','x2','x','k')+('exact hz_witness_right',)

    jordan=_intro('k','n','hk','hn')
    jordan+=(f'have hbox : exists c T. {_representatives("k","n","c","T","totalbox")}',)
    jordan+=_call('jordan_tuple_representatives_exists','k','n')+('cases hbox','cases hbox_witness')
    jordan+=(f'have hfamily : forall t. exists B C D E j. {_scan("k","n","x","t","B","C","D","E","j","totalfamily")}',)
    jordan+=_call('jordan_tuple_scan_exists','k','n','x')+('exact hn',)
    jordan+=(f'have hs : exists B C D E j. {_scan("k","n","x","x1","B","C","D","E","j","totalscan")}',)
    jordan+=_call('hfamily','x1')
    jordan+=('cases hs','cases hs_witness','cases hs_witness_witness','cases hs_witness_witness_witness','cases hs_witness_witness_witness_witness','exists x6')
    jordan+=_call('jordan_totient_from_complete_scan','k','n','x','x1','x2','x3','x4','x5','x6')
    jordan+=('exact hk','exact hn','exact hbox_witness_witness','exact hs_witness_witness_witness_witness_witness')

    return (
        spec('jordan_tuple_scan_append',f'forall k n c t B C D E j. ({_scan("k","n","c","t","B","C","D","E","j","appendinvariant")}) -> ({_bounded("t","c","k","n","appendbound")}) -> ({_primitive("n","t","c","k","appendprimitive")}) -> ~({_listed("t","c","k","B","C","D","E","j","appendfresh")}) -> exists U V W X. {_scan("k","n","c","S t","U","V","W","X","S j","appendresult")}',
             ('jordan_tuple_outer_append_exists','jordan_tuple_equal_symm','finite_lt_succ_eq_or_lt',
              'jordan_tuple_equal_entry','beta_at_unique','le_refl','jordan_tuple_equal_refl','le_succ'),proof,
             'Append an actually absent primitive tuple and prove full soundness, distinctness and prefix coverage.'),
        spec('jordan_tuple_scan_exists',f'forall k n c. ~(n=0) -> forall t. exists B C D E j. {_scan("k","n","c","t","B","C","D","E","j","scanexists")}',
             ('jordan_tuple_scan_empty','matrix_rank_bounded_prefix_decidable','jordan_primitive_tuple_decidable',
              'jordan_tuple_listed_decidable','jordan_tuple_scan_skip','jordan_tuple_scan_append'),total,
             'Construct the duplicate-free finite scan by HA induction and three genuine finite decisions.'),
        spec('jordan_tuple_representatives_exists',f'forall k n. exists c T. {_representatives("k","n","c","T","representativesexists")}',
             ('matrix_rank_uniform_beta_prefix_box_exists','jordan_tuple_prefix_equal'),box,
             'Extract an actual finite coordinate-representative box from the existing beta recoding theorem.'),
        spec('jordan_totient_exists',f'forall k n. ~(k=0) -> ~(n=0) -> exists j. {_jordan("k","n","j","jordanexists")}',
             ('jordan_tuple_representatives_exists','jordan_tuple_scan_exists','jordan_totient_from_complete_scan'),jordan,
             'Obtain an actual finite tuple cardinality from independently constructed duplicate-free enumeration.'),
    )


def _crt_tuple(m,n,b,c,d,e,f,g,k,tag):
    i,a,z,w=_fresh(tag,(m,n,b,c,d,e,f,g,k),'index','left','right','output')
    return (f'forall {i}. ({_lt(i,k,tag+"index")}) -> exists {a} {z} {w}. '+
        _and(_at(b,c,i,a,tag+'left'),_at(d,e,i,z,tag+'right'),_at(f,g,i,w,tag+'output'),
             _mod(m,w,a,tag+'modleft'),_mod(n,w,z,tag+'modright')))


def make_jordan_crt_tuple_candidate_theorems(spec):
    """Coordinatewise CRT witnesses before canonical reduction or counting."""
    empty=_intro('m','n','b','c','d','e','f','g','i','hi')+('exfalso',)
    empty+=_call('lt_not_le','i','0')+('exact hi',)+_call('zero_le','i')

    extend=_intro('m','n','b','c','d','e','f','g','k','a','z','w','hprefix','ha','hz','hm','hn')
    extend+=(f'have hext : exists u v. {_and(_at("u","v","k","w","crtextendlast"),_prefix("f","g","u","v","k","crtextendprefix"))}',)
    extend+=_call('beta_prefix_extend','k','f','g','w')+('cases hext','cases hext_witness','cases hext_witness_witness','exists x','exists x1')
    extend+=_intro('i','hi')+(f'have hc : i=k \\/ ({_lt("i","k","crtextendcase")})',)
    extend+=_call('finite_lt_succ_eq_or_lt','k','i')+('exact hi','cases hc','exists a','exists z','exists w','split')
    extend+=('rewrite hc_left','rewrite hc_left','exact ha','split',
              'rewrite hc_left','rewrite hc_left','exact hz','split',
              'rewrite hc_left','rewrite hc_left','exact hext_witness_witness_left',
              'split','exact hm','exact hn')
    old=_and(_at('b','c','i','a','crtoldleft'),_at('d','e','i','z','crtoldright'),
             _at('f','g','i','w','crtoldoutput'),_mod('m','w','a','crtoldmodleft'),_mod('n','w','z','crtoldmodright'))
    extend+=(f'have hvalue : exists a z w. {old}',)+_call('hprefix','i')
    extend+=('exact hc_right','cases hvalue','cases hvalue_witness','cases hvalue_witness_witness')
    v='hvalue_witness_witness_witness'
    extend+=_parts(v,5)+('exists x2','exists x3','exists x4','split','exact '+_part(v,5,0),
                        'split','exact '+_part(v,5,1),'split')
    extend+=_call('hext_witness_witness_right','i','x4')+('exact hc_right','exact '+_part(v,5,2),
                 'split','exact '+_part(v,5,3),'exact '+_part(v,5,4))

    total=_intro('m','n','b','c','d','e','hm','hn','hcop')+('induction k','exists 0','exists 0')
    total+=_call('jordan_crt_tuple_empty','m','n','b','c','d','e','0','0')
    total+=('cases IH','cases IH_witness',f'have ha : exists a. {_at("b","c","k","a","crttotalleft")}',)
    total+=_call('beta_at_exists','b','c','k')+('cases ha',)
    total+=(f'have hz : exists z. {_at("d","e","k","z","crttotalright")}',)
    total+=_call('beta_at_exists','d','e','k')+('cases hz',)
    total+=(f'have hw : exists w. {_and(_mod("m","w","x2","crttotalmodleft"),_mod("n","w","x3","crttotalmodright"))}',)
    total+=_call('binary_crt','m','n','x2','x3')+('exact hm','exact hn','exact hcop','cases hw','cases hw_witness')
    total+=_call('jordan_crt_tuple_extend','m','n','b','c','d','e','x','x1','k','x2','x3','x4')
    total+=('exact IH_witness_witness','exact ha_witness','exact hz_witness','exact hw_witness_left','exact hw_witness_right')

    projections=[]
    for side,modulus,inputcode,inputscale,position in (('left','m','b','c',0),('right','n','d','e',1)):
        proof=_intro('m','n','b','c','d','e','f','g','k','h','i','w','a','hi','hw','ha')
        point=_and(_at('b','c','i','u','crtpointleft'),_at('d','e','i','v','crtpointright'),
                   _at('f','g','i','q','crtpointoutput'),_mod('m','q','u','crtpointmodleft'),_mod('n','q','v','crtpointmodright'))
        proof+=(f'have ht : exists u v q. {point}',)+_call('h','i')
        proof+=('exact hi','cases ht','cases ht_witness','cases ht_witness_witness')
        node='ht_witness_witness_witness'
        proof+=_parts(node,5)+('have hout : x2=w',)+_call('beta_at_unique','f','g','i','x2','w')
        proof+=('exact '+_part(node,5,2),'exact hw',f'have hin : {"x" if position==0 else "x1"}=a')
        proof+=_call('beta_at_unique',inputcode,inputscale,'i','x' if position==0 else 'x1','a')
        proof+=('exact '+_part(node,5,position),'exact ha','rewrite hout at '+_part(node,5,3+position),
                'rewrite hin at '+_part(node,5,3+position),'exact '+_part(node,5,3+position))
        projections.append(spec('jordan_crt_tuple_'+side,
            f'forall m n b c d e f g k. ({_crt_tuple("m","n","b","c","d","e","f","g","k","crt"+side)}) -> '
            f'({_pointwise_mod(modulus,"f","g",inputcode,inputscale,"k","crtprojection"+side)})',
            ('beta_at_unique',),proof,'Every actual output coordinate has the required '+side+' congruence.'))
    return (
        spec('jordan_crt_tuple_empty',f'forall m n b c d e f g. {_crt_tuple("m","n","b","c","d","e","f","g","0","crtempty")}',
             ('lt_not_le','zero_le'),empty,'The empty simultaneous coordinate congruence has no missing witness.'),
        spec('jordan_crt_tuple_extend',f'forall m n b c d e f g k a z w. ({_crt_tuple("m","n","b","c","d","e","f","g","k","crtprefix")}) -> '
             f'({_at("b","c","k","a","crtlastleft")}) -> ({_at("d","e","k","z","crtlastright")}) -> '
             f'({_mod("m","w","a","crtlastmodleft")}) -> ({_mod("n","w","z","crtlastmodright")}) -> '
             f'exists u v. {_crt_tuple("m","n","b","c","d","e","u","v","S k","crtextended")}',
             ('beta_prefix_extend','finite_lt_succ_eq_or_lt'),extend,
             'Append one genuine scalar CRT solution using an actual beta prefix extension.'),
        spec('jordan_crt_tuple_exists',f'forall m n b c d e. ~(m=0) -> ~(n=0) -> ({_cop("m","n","crtcoprime")}) -> forall k. exists f g. {_crt_tuple("m","n","b","c","d","e","f","g","k","crtexists")}',
             ('jordan_crt_tuple_empty','beta_at_exists','binary_crt','jordan_crt_tuple_extend'),total,
             'Construct simultaneous residue representatives coordinate by coordinate, without any tuple totality premise.'),
    )+tuple(projections)


def _normalization(n,b,c,d,e,k,tag):
    i,a,r=_fresh(tag,(n,b,c,d,e,k),'index','input','output')
    return (f'forall {i}. ({_lt(i,k,tag+"index")}) -> exists {a} {r}. '+
        _and(_at(b,c,i,a,tag+'input'),_at(d,e,i,r,tag+'output'),
             _and(_lt(r,n,tag+'bound'),_mod(n,a,r,tag+'mod'))))


def _canonical_crt(m,n,b,c,d,e,f,g,k,tag):
    return _and(_bounded(f,g,k,f'{m}*{n}',tag+'bound'),
        _pointwise_mod(m,f,g,b,c,k,tag+'left'),_pointwise_mod(n,f,g,d,e,k,tag+'right'))


def make_jordan_canonical_crt_candidate_theorems(spec):
    normalize=_intro('n','b','c','k','hn')
    normalize+=(f'have hnorm : exists d e. {_normalization("n","b","c","d","e","k","normalizeactual")}',)
    normalize+=_call('prime_field_polynomial_normalization_exists','n','b','c','k')+('exact hn','cases hnorm','cases hnorm_witness','exists x','exists x1','split')
    normalize+=_call('prime_field_polynomial_normalization_bounded','n','b','c','x','x1','k')+('exact hnorm_witness_witness',)
    normalize+=_intro('i','a','r','hi','ha','hr')
    normalize+=(f'have hvalue : {_and(_lt("r","n","normalizeresiduebound"),_mod("n","a","r","normalizeresiduemod"))}',)
    normalize+=_call('prime_field_polynomial_normalization_entry','n','b','c','x','x1','k','i','a','r')
    normalize+=('exact hnorm_witness_witness','exact hi','exact ha','exact hr','cases hvalue','exact hvalue_right')

    trans=_intro('n','b','c','d','e','f','g','k','hleft','hright','i','a','z','hi','ha','hz')
    trans+=(f'have hx : exists x. {_at("d","e","i","x","modtransmiddle")}',)
    trans+=_call('beta_at_exists','d','e','i')+('cases hx',)
    trans+=_call('mod_eq_trans','n','a','x','z')
    trans+=_call('hleft','i','a','x')+('exact hi','exact ha','exact hx_witness')
    trans+=_call('hright','i','x','z')+('exact hi','exact hx_witness','exact hz')

    divisor=_intro('m','n','b','c','d','e','k','hdiv','hmod','i','a','z','hi','ha','hz')
    divisor+=_call('mod_eq_of_mod_eq_multiple','m','n','a','z')+('exact hdiv',)
    divisor+=_call('hmod','i','a','z')+('exact hi','exact ha','exact hz')

    canonical=_intro('m','n','b','c','d','e','k','hm','hn','hcop')
    canonical+=(f'have hfamily : forall L. exists f g. {_crt_tuple("m","n","b","c","d","e","f","g","L","canonicalfamily")}',)
    canonical+=_call('jordan_crt_tuple_exists','m','n','b','c','d','e')+('exact hm','exact hn','exact hcop')
    canonical+=(f'have hraw : exists f g. {_crt_tuple("m","n","b","c","d","e","f","g","k","canonicalraw")}',)
    canonical+=_call('hfamily','k')+('cases hraw','cases hraw_witness','have hproduct : ~(m*n=0)','intro hz')
    canonical+=_call('mul_ne_zero','m','n')+('exact hm','exact hn','exact hz')
    canonical+=(f'have hnorm : exists u v. {_and(_bounded("u","v","k","m*n","canonicalbound"),_pointwise_mod("m*n","x","x1","u","v","k","canonicalmod"))}',)
    canonical+=_call('jordan_tuple_normalize_exists','m*n','x','x1','k')
    canonical+=('exact hproduct','cases hnorm','cases hnorm_witness','cases hnorm_witness_witness','exists x2','exists x3','split','exact hnorm_witness_witness_left','split')
    for side,modulus,inputcode,inputscale in (('left','m','b','c'),('right','n','d','e')):
        canonical+=(f'have hsmall : {_pointwise_mod(modulus,"x","x1","x2","x3","k","canonicalsmall"+side)}',)
        canonical+=_call('jordan_tuple_congruence_divisor',modulus,'m*n','x','x1','x2','x3','k')
        canonical+=('exists '+('n' if side=='left' else 'm'),)
        canonical+=('refl',) if side=='left' else _call('mul_comm','m','n')
        canonical+=('exact hnorm_witness_witness_right',)
        canonical+=_call('jordan_tuple_congruence_trans',modulus,'x2','x3','x','x1',inputcode,inputscale,'k')
        canonical+=_call('jordan_tuple_congruence_symm',modulus,'x','x1','x2','x3','k')+('exact hsmall',)
        canonical+=_call('jordan_crt_tuple_'+side,'m','n','b','c','d','e','x','x1','k')+('exact hraw_witness_witness',)

    primitive=_intro('m','n','b','c','d','e','k','hm','hn','hcop','hleft','hright')
    primitive+=(f'have hcrt : exists f g. {_canonical_crt("m","n","b","c","d","e","f","g","k","primitivecrtactual")}',)
    primitive+=_call('jordan_canonical_crt_tuple_exists','m','n','b','c','d','e','k')
    primitive+=('exact hm','exact hn','exact hcop','cases hcrt','cases hcrt_witness')
    primitive+=_parts('hcrt_witness_witness',3)+('exists x','exists x1','split')
    primitive+=('split','exact hcrt_witness_witness_left','split','exact hcrt_witness_witness_right_left','exact hcrt_witness_witness_right_right')
    primitive+=_call('jordan_primitive_tuple_coprime_product','m','n','x','x1','k')
    primitive+=('exact hm','exact hn','exact hcop')
    for side,modulus,inputcode,inputscale,clause in (
        ('left','m','b','c','hcrt_witness_witness_right_left'),
        ('right','n','d','e','hcrt_witness_witness_right_right')):
        primitive+=_call('jordan_primitive_tuple_congruence_transport',modulus,inputcode,inputscale,'x','x1','k')
        primitive+=_call('jordan_tuple_congruence_symm',modulus,'x','x1',inputcode,inputscale,'k')
        primitive+=('exact '+clause,'exact h'+side)
    return (
        spec('jordan_tuple_normalize_exists',f'forall n b c k. ~(n=0) -> exists d e. '+_and(
             _bounded('d','e','k','n','normalizebound'),_pointwise_mod('n','b','c','d','e','k','normalizemod')),
             ('prime_field_polynomial_normalization_exists','prime_field_polynomial_normalization_bounded','prime_field_polynomial_normalization_entry'),normalize,
             'Canonical coordinate reduction works for every nonzero modulus, not just fields.'),
        spec('jordan_tuple_congruence_trans',f'forall n b c d e f g k. ({_pointwise_mod("n","b","c","d","e","k","modtransfirst")}) -> ({_pointwise_mod("n","d","e","f","g","k","modtranssecond")}) -> ({_pointwise_mod("n","b","c","f","g","k","modtransresult")})',
             ('beta_at_exists','mod_eq_trans'),trans,'Actual decoded middle entries witness transitivity of coordinate congruence.'),
        spec('jordan_tuple_congruence_divisor',f'forall m n b c d e k. ({_dvd("m","n","moddivisor")}) -> ({_pointwise_mod("n","b","c","d","e","k","modlarger")}) -> ({_pointwise_mod("m","b","c","d","e","k","modsmaller")})',
             ('mod_eq_of_mod_eq_multiple',),divisor,'Coordinate congruence descends along actual divisibility of moduli.'),
        spec('jordan_canonical_crt_tuple_exists',f'forall m n b c d e k. ~(m=0) -> ~(n=0) -> ({_cop("m","n","canonicalcrtcoprime")}) -> exists f g. {_canonical_crt("m","n","b","c","d","e","f","g","k","canonicalcrtexists")}',
             ('jordan_crt_tuple_exists','mul_ne_zero','jordan_tuple_normalize_exists','jordan_tuple_congruence_divisor',
              'mul_comm','jordan_tuple_congruence_trans','jordan_tuple_congruence_symm','jordan_crt_tuple_left','jordan_crt_tuple_right'),canonical,
             'Construct an actual tuple bounded by the product modulus with both prescribed residue tuples.'),
        spec('jordan_primitive_crt_tuple_exists',f'forall m n b c d e k. ~(m=0) -> ~(n=0) -> ({_cop("m","n","primitivecrtcoprime")}) -> ({_primitive("m","b","c","k","primitivecrtleft")}) -> ({_primitive("n","d","e","k","primitivecrtright")}) -> exists f g. '+_and(
             _canonical_crt('m','n','b','c','d','e','f','g','k','primitivecrtresult'),_primitive('m*n','f','g','k','primitivecrtproduct')),
             ('jordan_canonical_crt_tuple_exists','jordan_primitive_tuple_coprime_product','jordan_primitive_tuple_congruence_transport','jordan_tuple_congruence_symm'),primitive,
             'The constructed canonical CRT tuple is primitive collectively, by coprime common-divisor decomposition.'),
    )
