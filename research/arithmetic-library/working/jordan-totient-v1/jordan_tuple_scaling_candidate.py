"""Actual coordinate scaling and division of beta-coded finite tuples.

The scaling relation concerns decoded coordinates, never equality of codes.
This additive HA candidate layer constructs the bijection between the A-box
and the all-p-divisible part of the (p*A)-box for nonzero p. It does not assume
an enumeration, its cardinality, or the Jordan prime-power formula.
"""
import importlib.util
from pathlib import Path

from peano_lab.library.finite_division_prefix_candidate import division_prefix
from peano_lab.library.finite_fold_surface import repeat_relation
from peano_lab.library.finite_pointwise_mul_product_candidate import pointwise_mul_prefix

HERE = Path(__file__).resolve().parent
loader = importlib.util.spec_from_file_location(
    '_jordan_tuple_scaling_base', HERE / 'jordan_totient_candidate.py')
base = importlib.util.module_from_spec(loader)
loader.loader.exec_module(base)
_call, _intro = base._call, base._intro
_and, _at, _lt = base._and, base._at, base._lt


def _scale(p, b, c, d, e, k, tag):
    i, a, z = base._fresh(tag, (p, b, c, d, e, k), 'index', 'source', 'target')
    return (f'forall {i} {a} {z}. ({_lt(i,k,tag+"index")}) -> '
            f'({_at(b,c,i,a,tag+"source")}) -> ({_at(d,e,i,z,tag+"target")}) -> '
            f'{z}=({p})*{a}')


def tuple_scaling_relation(multiplier, code, scale, image_code, image_scale, length, *, tag):
    """Conservative, capture-rejecting first-order abbreviation for scaling."""
    arguments = (multiplier, code, scale, image_code, image_scale, length)
    base._public(arguments, tag)
    return _scale(*arguments, tag)


def _contract(variables, premises, target):
    return 'forall ' + variables + '. ' + ''.join('(' + p + ') -> ' for p in premises) + target


def _entry(name, code, scale, index, tag):
    """Choose a real beta entry; the caller controls the fresh witness name."""
    return ((f'have {name} : exists a. {_at(code,scale,index,"a",tag)}',)
            + _call('beta_at_exists', code, scale, index) + ('cases ' + name,))


def make_jordan_tuple_scaling_candidate_theorems(spec):
    result = []
    def add(name, variables, premises, target, dependencies, script, description):
        result.append(spec(name, _contract(variables, premises, target), dependencies, script, description))

    # Strict bounds are witnessed order statements in the original signature.
    preserve = _intro('p', 'a', 'A', 'hp', 'ha')
    preserve += _call('lt_of_lt_of_le', 'p*a', 'p*S a', 'p*A')
    preserve += _call('mul_lt_mul_succ_left_nonzero', 'p', 'a') + ('exact hp',)
    preserve += _call('mul_le_mul_left', 'S a', 'A', 'p') + ('exact ha',)
    add('jordan_scale_coordinate_strict_bound', 'p a A',
        ('~(p=0)', _lt('a','A','coord_before')), _lt('p*a','p*A','coord_after'),
        ('lt_of_lt_of_le', 'mul_lt_mul_succ_left_nonzero', 'mul_le_mul_left'), preserve,
        'Positive coordinate scaling preserves the actual strict box bound.')

    reflect = _intro('p', 'a', 'A', 'h')
    reflect += ('specialize le_or_lt A', 'specialize le_or_lt a', 'cases le_or_lt', 'exfalso')
    reflect += _call('lt_not_le', 'p*a', 'p*A') + ('exact h',)
    reflect += _call('mul_le_mul_left', 'A', 'a', 'p')
    reflect += ('exact le_or_lt_left', 'exact le_or_lt_right')
    add('jordan_scale_coordinate_strict_bound_reflect', 'p a A',
        (_lt('p*a','p*A','coord_reflect_before'),), _lt('a','A','coord_reflect_after'),
        ('le_or_lt', 'lt_not_le', 'mul_le_mul_left'), reflect,
        'A strict bound between two scaled coordinates reflects to their factors; no extra positivity assumption is needed.')

    # A constant prefix multiplied pointwise by the source constructs the image.
    exists = _intro('p', 'b', 'c', 'k')
    exists += ('have hr : exists rb rc. ' + repeat_relation('rb','rc','p','k',tag='jts_repeat'),)
    exists += _call('beta_repeat_exists', 'p', 'k') + ('cases hr', 'cases hr_witness')
    exists += ('have hm : exists d e. ' + pointwise_mul_prefix('x','x1','b','c','d','e','k',tag='jts_pointwise'),)
    exists += _call('beta_pointwise_mul_prefix_exists', 'x', 'x1', 'b', 'c', 'k')
    exists += ('cases hm', 'cases hm_witness', 'exists x2', 'exists x3')
    exists += _intro('i', 'a', 'z', 'hi', 'ha', 'hz')
    exists += _call('hm_witness_witness', 'i', 'p', 'a', 'z') + ('exact hi',)
    exists += _call('hr_witness_witness', 'i') + ('exact hi', 'exact ha', 'exact hz')
    add('jordan_tuple_scaling_exists', 'p b c k', (),
        'exists d e. ' + _scale('p','b','c','d','e','k','scale_exists'),
        ('beta_repeat_exists', 'beta_pointwise_mul_prefix_exists'), exists,
        'Every finite beta tuple has an actual beta-coded coordinatewise multiple, including width zero and multiplier zero.')

    divisible = _intro('p', 'b', 'c', 'd', 'e', 'k', 'hs', 'i', 'z', 'hi', 'hz')
    divisible += _entry('ha', 'b', 'c', 'i', 'div_source') + ('exists x',)
    divisible += _call('hs', 'i', 'x', 'z') + ('exact hi', 'exact ha_witness', 'exact hz')
    add('jordan_tuple_scaling_all_divisible', 'p b c d e k',
        (_scale('p','b','c','d','e','k','scale_div'),), base._all_dvd('p','d','e','k','image_div'),
        ('beta_at_exists',), divisible,
        'Every decoded coordinate in a scaled tuple has its source coordinate as a divisibility witness.')

    # Source equality, not raw code equality, determines the scaled tuple.
    respect = _intro('p','b','c','d','e','f','g','u','v','k','hleft','hright','heq',
                     'i','a','z','hi','ha','hz')
    respect += _entry('hx','b','c','i','respect_left')
    respect += _entry('hy','d','e','i','respect_right')
    respect += ('have hxy : x=x1',) + _call('heq','i','x','x1')
    respect += ('exact hi','exact hx_witness','exact hy_witness')
    respect += ('have hax : a=p*x',) + _call('hleft','i','x','a')
    respect += ('exact hi','exact hx_witness','exact ha')
    respect += ('have hzy : z=p*x1',) + _call('hright','i','x1','z')
    respect += ('exact hi','exact hy_witness','exact hz',
                'trans p*x','exact hax','trans p*x1','congr','refl','exact hxy','symm','exact hzy')
    add('jordan_tuple_scaling_respects_tuple_equality', 'p b c d e f g u v k',
        (_scale('p','b','c','f','g','k','respect_first'),
         _scale('p','d','e','u','v','k','respect_second'), base._equal('b','c','d','e','k','respect_source')),
        base._equal('f','g','u','v','k','respect_image'), ('beta_at_exists',), respect,
        'Equal decoded source tuples have equal decoded images under arbitrary beta recodings.')

    inject = _intro('p','b','c','d','e','f','g','u','v','k','hp','hleft','hright','heq',
                    'i','a','z','hi','ha','hz')
    inject += _entry('hx','f','g','i','inject_left')
    inject += _entry('hy','u','v','i','inject_right')
    inject += ('have hxy : x=x1',) + _call('heq','i','x','x1')
    inject += ('exact hi','exact hx_witness','exact hy_witness')
    inject += ('have hxa : x=p*a',) + _call('hleft','i','a','x')
    inject += ('exact hi','exact ha','exact hx_witness')
    inject += ('have hyz : x1=p*z',) + _call('hright','i','z','x1')
    inject += ('exact hi','exact hz','exact hy_witness')
    inject += _call('mul_left_cancel_nonzero','p','a','z')
    inject += ('exact hp','trans x','symm','exact hxa','trans x1','exact hxy','exact hyz')
    add('jordan_tuple_scaling_injective', 'p b c d e f g u v k',
        ('~(p=0)', _scale('p','b','c','f','g','k','inject_first'),
         _scale('p','d','e','u','v','k','inject_second'), base._equal('f','g','u','v','k','inject_image')),
        base._equal('b','c','d','e','k','inject_source'), ('beta_at_exists','mul_left_cancel_nonzero'), inject,
        'Nonzero scaling is injective on finite tuples modulo decoded tuple equality, not on their beta codes.')

    # Actual division streams give quotient codes. Divisibility forces every
    # remainder to be zero by uniqueness, rather than by a supplied inverse.
    quotient = _intro('p','b','c','k','hp','hall')
    quotient += ('have hd : exists qb qc rb rc. '
                 + division_prefix('p','b','c','qb','qc','rb','rc','k',tag='jts_division'),)
    quotient += _call('beta_division_prefix_exists','p','b','c','k')
    quotient += ('exact hp','cases hd','cases hd_witness','cases hd_witness_witness',
                 'cases hd_witness_witness_witness','exists x','exists x1')
    quotient += _intro('i','a','z','hi','ha','hz')
    point = _and(_at('b','c','i','v','quot_value'), _at('x','x1','i','q','quot_q'),
                 _at('x2','x3','i','r','quot_r'), 'v=p*q+r', _lt('r','p','quot_bound'))
    quotient += ('have he : exists v q r. ' + point,)
    quotient += _call('hd_witness_witness_witness_witness','i')
    quotient += ('exact hi','cases he','cases he_witness','cases he_witness_witness')
    quotient += base._parts('he_witness_witness_witness',5)
    part = lambda index: 'exact ' + base._part('he_witness_witness_witness',5,index)
    quotient += ('have hvz : x4=z',) + _call('beta_at_unique','b','c','i','x4','z')
    quotient += (part(0),'exact hz','have hqa : x5=a')
    quotient += _call('beta_at_unique','x','x1','i','x5','a') + (part(1),'exact ha')
    quotient += ('have hv : ' + base._dvd('p','x4','quot_divides'),)
    quotient += _call('hall','i','x4') + ('exact hi',part(0),'cases hv')
    quotient += ('have hu : x5=x7 /\\ x6=0',)
    quotient += _call('division_remainder_unique','p','x4','x5','x6','x7','0')
    quotient += (part(3),part(4),'rewrite PA3','exact hv_witness')
    quotient += _call('one_le_of_ne_zero','p') + ('exact hp','cases hu')
    quotient += ('have heq : x4=p*x5', 'have heq0 : x4=p*x5+x6',part(3),
                 'rewrite hu_right at heq0','rewrite PA3 at heq0','exact heq0',
                 'trans x4','symm','exact hvz','trans p*x5','exact heq','congr','refl','exact hqa')
    add('jordan_tuple_all_divisible_quotient_exists', 'p b c k',
        ('~(p=0)', base._all_dvd('p','b','c','k','quot_all')),
        'exists d e. ' + _scale('p','d','e','b','c','k','quot_result'),
        ('beta_division_prefix_exists','beta_at_unique','division_remainder_unique','one_le_of_ne_zero'), quotient,
        'Every all-p-divisible beta tuple has an actual beta-coded quotient tuple for nonzero p.')

    bounded = _intro('p','A','b','c','d','e','k','hp','hb','hs','i','hi')
    bounded += ('have ha : exists a. ' + _and(_at('b','c','i','a','bound_entry'),_lt('a','A','bound_a')),)
    bounded += _call('hb','i') + ('exact hi','cases ha','cases ha_witness')
    bounded += _entry('hz','d','e','i','bound_image')
    bounded += ('have heq : x1=p*x',) + _call('hs','i','x','x1')
    bounded += ('exact hi','exact ha_witness_left','exact hz_witness','exists x1','split',
                'exact hz_witness','rewrite heq')
    bounded += _call('jordan_scale_coordinate_strict_bound','p','x','A')
    bounded += ('exact hp','exact ha_witness_right')
    add('jordan_tuple_scaling_preserves_box_bound', 'p A b c d e k',
        ('~(p=0)',base._bounded('b','c','k','A','box_before'),_scale('p','b','c','d','e','k','box_scale')),
        base._bounded('d','e','k','p*A','box_after'),
        ('beta_at_exists','jordan_scale_coordinate_strict_bound'), bounded,
        'A scaled canonical A-box tuple is canonically bounded by p*A.')

    unbound = _intro('p','A','b','c','d','e','k','hb','hs','i','hi')
    unbound += ('have hz : exists z. ' + _and(_at('d','e','i','z','unbound_entry'),_lt('z','p*A','unbound_z')),)
    unbound += _call('hb','i') + ('exact hi','cases hz','cases hz_witness')
    unbound += _entry('ha','b','c','i','unbound_source')
    unbound += ('have heq : x=p*x1',) + _call('hs','i','x1','x')
    unbound += ('exact hi','exact ha_witness','exact hz_witness_left','exists x1','split',
                'exact ha_witness')
    unbound += _call('jordan_scale_coordinate_strict_bound_reflect','p','x1','A')
    unbound += ('rewrite <- heq','exact hz_witness_right')
    add('jordan_tuple_scaling_reflects_box_bound', 'p A b c d e k',
        (base._bounded('d','e','k','p*A','unbox_before'),_scale('p','b','c','d','e','k','unbox_scale')),
        base._bounded('b','c','k','A','unbox_after'),
        ('beta_at_exists','jordan_scale_coordinate_strict_bound_reflect'), unbound,
        'Every source tuple of an image in the p*A-box lies in the A-box, even without a separate positivity premise.')

    box_image = _intro('p','A','b','c','k','hp','hb')
    box_image += ('have hs : exists d e. ' + _scale('p','b','c','d','e','k','box_witness'),)
    box_image += _call('jordan_tuple_scaling_exists','p','b','c','k')
    box_image += ('cases hs','cases hs_witness','exists x','exists x1','split','exact hs_witness_witness','split')
    box_image += _call('jordan_tuple_scaling_preserves_box_bound','p','A','b','c','x','x1','k')
    box_image += ('exact hp','exact hb','exact hs_witness_witness')
    box_image += _call('jordan_tuple_scaling_all_divisible','p','b','c','x','x1','k') + ('exact hs_witness_witness',)
    add('jordan_box_scaling_divisible_image_exists', 'p A b c k',
        ('~(p=0)',base._bounded('b','c','k','A','box_source')),
        'exists d e. ' + _and(_scale('p','b','c','d','e','k','box_map'),
          base._bounded('d','e','k','p*A','box_target'),base._all_dvd('p','d','e','k','box_divisible')),
        ('jordan_tuple_scaling_exists','jordan_tuple_scaling_preserves_box_bound','jordan_tuple_scaling_all_divisible'),box_image,
        'Construct an actual all-p-divisible p*A-box image of every A-box tuple.')

    box_quotient = _intro('p','A','b','c','k','hp','hb','hall')
    box_quotient += ('have hs : exists d e. ' + _scale('p','d','e','b','c','k','box_quotient_witness'),)
    box_quotient += _call('jordan_tuple_all_divisible_quotient_exists','p','b','c','k')
    box_quotient += ('exact hp','exact hall','cases hs','cases hs_witness','exists x','exists x1','split','exact hs_witness_witness')
    box_quotient += _call('jordan_tuple_scaling_reflects_box_bound','p','A','x','x1','b','c','k')
    box_quotient += ('exact hb','exact hs_witness_witness')
    add('jordan_box_divisible_scaling_preimage_exists', 'p A b c k',
        ('~(p=0)',base._bounded('b','c','k','p*A','box_input'),base._all_dvd('p','b','c','k','box_all')),
        'exists d e. ' + _and(_scale('p','d','e','b','c','k','box_inverse'),base._bounded('d','e','k','A','box_preimage')),
        ('jordan_tuple_all_divisible_quotient_exists','jordan_tuple_scaling_reflects_box_bound'),box_quotient,
        'Every all-p-divisible tuple in the p*A-box has an actual canonical A-box preimage; injectivity proves uniqueness up to tuple equality.')
    return tuple(result)
