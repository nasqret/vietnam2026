"""Primitive tuples over actual prime powers, in the unchanged HA language.

These additive candidate bodies reuse Jordan's common-divisor predicate and
the existing beta-chain power relation. They introduce no count equation or
new definition. Dependency-curried body checking is separate from closing
the complete proof cone and admitting a theorem.
"""
from .prime_valuation_support_candidate import _prime, _pow
from . import jordan_totient_candidate as base

_call, _intro = base._call, base._intro


def _contract(variables, premises, target):
    return 'forall ' + variables + '. ' + ''.join('(' + p + ') -> ' for p in premises) + target


def make_jordan_prime_power_characterization_candidate_theorems(spec):
    primitive = base._primitive('n', 'b', 'c', 'k', 'power_primitive')
    all_divisible = base._all_dvd('p', 'b', 'c', 'k', 'power_all_divisible')
    not_all = '~(' + all_divisible + ')'
    prime = _prime('p', 'jordan_base')

    avoid = (_intro('p', 'n', 'b', 'c', 'k', 'hp', 'hpn', 'hprimitive', 'hall')
        + ('cases hp', 'apply hp_left')
        + _call('hprimitive', 'p') + ('exact hpn', 'exact hall'))

    converse = _intro('p', 'e', 'n', 'b', 'c', 'k', 'hp', 'hpow', 'hnot')
    converse += ('have hn : ~(n=0)', 'intro hz')
    converse += _call('pow_nonzero_of_one_le', 'p', 'e', 'n')
    converse += _call('one_le_of_ne_zero', 'p')
    converse += ('intro hpzero',) + _call('prime_nonzero', 'p')
    converse += ('exact hp', 'exact hpzero', 'exact hpow', 'exact hz')
    converse += _intro('d', 'hd', 'hall')
    converse += ('specialize eq_decidable d', 'specialize eq_decidable 1',
                 'cases eq_decidable', 'exact eq_decidable_left', 'exfalso', 'apply hnot')
    converse += ('have hdnonzero : ~(d=0)', 'intro hz', 'apply hn', 'cases hd',
                 'trans d*x', 'exact hd_witness', 'rewrite hz')
    converse += _call('mul_zero_left', 'x')
    converse += ('have hprime : exists q. ' + base._and(
        _prime('q', 'jordan_common_prime'), base._dvd('q', 'd', 'jordan_common_divisor')),)
    converse += _call('prime_divisor_exists', 'd')
    converse += ('exact hdnonzero', 'exact eq_decidable_right', 'cases hprime',
                 'cases hprime_witness')
    converse += ('have hqn : ' + base._dvd('x', 'n', 'jordan_modulus_prime'),)
    converse += _call('multiple_trans', 'd', 'x', 'n')
    converse += ('exact hd', 'exact hprime_witness_right', 'have hqp : x=p')
    converse += _call('prime_divisor_of_prime_power', 'p', 'x', 'e', 'n')
    converse += ('exact hp', 'exact hprime_witness_left', 'exact hpow', 'exact hqn',
                 'rewrite <- hqp')
    converse += _call('jordan_tuple_divisor_downward', 'x', 'd', 'b', 'c', 'k')
    converse += ('exact hprime_witness_right', 'exact hall')

    characterization = _intro('p', 'h', 'n', 'b', 'c', 'k', 'hp', 'hpow') + ('split',)
    characterization += ('intro hprimitive', 'intro hall')
    characterization += _call('jordan_primitive_tuple_avoids_prime_common_divisor', 'p', 'n', 'b', 'c', 'k')
    characterization += ('exact hp',)
    characterization += _call('pow_positive_exponent_base_divides', 'p', 'S h', 'n')
    characterization += ('intro hszero',) + _call('succ_ne_zero', 'h')
    characterization += ('exact hszero', 'exact hpow', 'exact hprimitive', 'exact hall', 'intro hnot')
    characterization += _call('jordan_prime_power_tuple_primitive_of_not_all_divisible',
                              'p', 'S h', 'n', 'b', 'c', 'k')
    characterization += ('exact hp', 'exact hpow', 'exact hnot')

    invariant = _intro('p', 'h', 'j', 'm', 'n', 'b', 'c', 'k', 'hp', 'hm', 'hn', 'hprimitive')
    invariant += _call('jordan_prime_power_tuple_primitive_of_not_all_divisible',
                       'p', 'S j', 'n', 'b', 'c', 'k')
    invariant += ('exact hp', 'exact hn', 'intro hall')
    invariant += _call('jordan_primitive_tuple_avoids_prime_common_divisor', 'p', 'm', 'b', 'c', 'k')
    invariant += ('exact hp',)
    invariant += _call('pow_positive_exponent_base_divides', 'p', 'S h', 'm')
    invariant += ('intro hszero',) + _call('succ_ne_zero', 'h')
    invariant += ('exact hszero', 'exact hm', 'exact hprimitive', 'exact hall')

    return (
        spec('jordan_primitive_tuple_avoids_prime_common_divisor',
             _contract('p n b c k', (prime, base._dvd('p', 'n', 'jordan_modulus'), primitive), not_all),
             (), avoid,
             'A prime divisor of the modulus cannot divide every coordinate of a primitive tuple.'),
        spec('jordan_prime_power_tuple_primitive_of_not_all_divisible',
             _contract('p e n b c k', (prime, _pow('p', 'e', 'n', 'jordan_power'), not_all), primitive),
             ('pow_nonzero_of_one_le', 'one_le_of_ne_zero', 'prime_nonzero', 'eq_decidable',
              'mul_zero_left', 'prime_divisor_exists', 'multiple_trans',
              'prime_divisor_of_prime_power', 'jordan_tuple_divisor_downward'), converse,
             'Every nonunit common divisor has an actual prime divisor; prime-power support then forces a forbidden common factor p.'),
        spec('jordan_prime_power_tuple_primitive_characterization',
             _contract('p h n b c k', (prime, _pow('p', 'S h', 'n', 'jordan_positive_power')),
                       base._and('(' + primitive + ') -> (' + not_all + ')',
                                 '(' + not_all + ') -> (' + primitive + ')')),
             ('jordan_primitive_tuple_avoids_prime_common_divisor',
              'pow_positive_exponent_base_divides', 'succ_ne_zero',
              'jordan_prime_power_tuple_primitive_of_not_all_divisible'), characterization,
             'Over every positive power of a prime, a tuple is primitive exactly when p does not divide all its coordinates.'),
        spec('jordan_prime_power_tuple_primitivity_invariant',
             _contract('p h j m n b c k', (prime,
                       _pow('p', 'S h', 'm', 'jordan_first_power'),
                       _pow('p', 'S j', 'n', 'jordan_second_power'),
                       base._primitive('m', 'b', 'c', 'k', 'jordan_first_primitive')), primitive),
             ('jordan_prime_power_tuple_primitive_of_not_all_divisible',
              'jordan_primitive_tuple_avoids_prime_common_divisor',
              'pow_positive_exponent_base_divides', 'succ_ne_zero'), invariant,
             'Primitivity of an actual beta tuple is invariant under changing the positive exponent of its prime-power modulus.'),
    )
