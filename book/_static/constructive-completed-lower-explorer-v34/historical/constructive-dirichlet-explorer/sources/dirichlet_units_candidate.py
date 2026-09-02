"""Actual signed constant-one and delta tables, with proved convolution laws.

The two table graphs constrain only positive indices through N.  Their zeroth
entries are arbitrary canonical signed codes, and the constructors preserve
any requested value there.  Codes 2 and 0 represent the integers one and zero.
Neither graph contains a convolution, divisor-sum, unit or inversion identity.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_table_extension_candidate import _extension
from .dirichlet_convolution_candidate import _convolution, _convolution_table, _entry, _prefix
from .divisor_mask_candidate import _divisor_sum, _entry as _mask_entry, _mask, _positive_equal
from .divisor_sum_table_candidate import _signed_sum, _table, _table_at, _table_equal
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _dvd, _intro, _le, _lt, _parts, _public, _rewrite,
)
from .signed_finite_support_candidate import _zero_window
from .signed_table_operations_candidate import _mul_code


def _one(N: str, U: str, tag: str) -> str:
    n, z = 'du_index_' + tag, 'du_value_' + tag
    return _and(_table(N,U,tag+'table'),
                f'forall {n} {z}. ~({n}=0) -> ({_le(n,N,tag+"bound")}) -> '
                f'({_table_at(U,n,z,tag+"entry")}) -> {z}=2')


def _delta_value(n: str, z: str) -> str:
    return _and(f'({n})=1 -> ({z})=2', f'~(({n})=1) -> ({z})=0')


def _delta(N: str, E: str, tag: str) -> str:
    n, z = 'du_index_' + tag, 'du_value_' + tag
    return _and(_table(N,E,tag+'table'),
                f'forall {n} {z}. ~({n}=0) -> ({_le(n,N,tag+"bound")}) -> '
                f'({_table_at(E,n,z,tag+"entry")}) -> ({_delta_value(n,z)})')


def dirichlet_constant_one_table_relation(
    N: str, U: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """A genuine signed table whose entries at 0<n<=N are the code 2."""
    return _public(_one,(N,U),tag=tag,variables=variables)


def dirichlet_kronecker_delta_table_relation(
    N: str, E: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """A genuine signed table with delta(1)=2 and delta(n)=0 for n>1."""
    return _public(_delta,(N,E),tag=tag,variables=variables)


def _lookup_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    one = _intro('N','U','n','z','hu','hn','hb','hz')+('cases hu',)
    one += _call('hu_right','n','z')+('exact hn','exact hb','exact hz')
    at_one = _intro('N','E','z','he','hb','hz')+('cases he',
                f'have hv : {_delta_value("1","z")}')
    at_one += _call('he_right','1','z')+('intro hn','apply PA1','exact hn','exact hb','exact hz','cases hv','apply hv_left','refl')
    other = _intro('N','E','n','z','he','hn','hnotone','hb','hz')+('cases he',
                f'have hv : {_delta_value("n","z")}')
    other += _call('he_right','n','z')+('exact hn','exact hb','exact hz','cases hv','apply hv_right','exact hnotone')
    return (
        spec('dirichlet_constant_one_table_value',
             f"forall N U n z. ({_one('N','U','one_lookup_table')}) -> ~(n=0) -> ({_le('n','N','one_lookup_bound')}) -> "
             f"({_table_at('U','n','z','one_lookup_entry')}) -> z=2",(),one,
             'Every actual positive in-domain lookup in a constant-one table is canonical signed one, independently of its zero entry.'),
        spec('dirichlet_kronecker_delta_table_one_value',
             f"forall N E z. ({_delta('N','E','delta_one_table')}) -> ({_le('1','N','delta_one_bound')}) -> "
             f"({_table_at('E','1','z','delta_one_entry')}) -> z=2",(),at_one,
             'The actual entry at index one is signed one whenever that index lies in the finite table domain.'),
        spec('dirichlet_kronecker_delta_table_other_value',
             f"forall N E n z. ({_delta('N','E','delta_other_table')}) -> ~(n=0) -> ~(n=1) -> "
             f"({_le('n','N','delta_other_bound')}) -> ({_table_at('E','n','z','delta_other_entry')}) -> z=0",(),other,
             'Every other positive in-domain delta entry is canonical zero; the omitted index-zero case remains unrestricted.'),
    )


def _append_body(graph: Callable[..., str], *, delta: bool) -> tuple[str, ...]:
    body = _intro('N','F') + (_intro('z','hf','hz') if delta else _intro('hf'))
    value = 'z' if delta else '2'
    body += ('cases hf',f"have hx : exists G. ({_extension('F','G','S N',value,'append_actual')})")
    body += _call('arithmetic_signed_table_append','N','F',value)+('exact hf_left','cases hx')
    body += _parts('hx_witness',3)+('exists x','split','split','exact hx_witness_left')
    body += _intro('i','a','hi','hb','ha')
    body += (f"have hc : i=S N \\/ ({_lt('i','S N','append_cases')})",)
    body += _call('le_eq_or_lt','i','S N')+('exact hb','cases hc')
    body += _rewrite('hc_left',_table_at('x','i','a','append_last_lookup'),'i','ha')
    body += (f'have hv : a={value}',)+_call('divisor_signed_table_at_functional','x','S N','a',value)
    body += ('exact ha','exact hx_witness_right_right')
    if delta:
        body += _rewrite('hc_left',_delta_value('i','a'),'i')
        body += _rewrite('hv',_delta_value('S N','a'),'a')+('exact hz',)
    else:
        body += ('exact hv',)
    body += (f"have hib : {_le('i','N','append_old_bound')}",)
    body += _call('le_of_succ_le_succ','i','N')+('exact hc_right',
                f"have hv : exists v. ({_table_at('F','i','v','append_old_lookup')})")
    body += _call('divisor_signed_table_lookup','N','F','i')+('exact hf_left','exact hib','cases hv','have heq : x1=a')
    body += _call('hx_witness_right_left','i','x1','a')+('exact hc_right','exact hv_witness','exact ha')
    body += _rewrite('heq',_table_at('F','i','x1','append_old_rewrite'),'x1','hv_witness')
    body += _call('hf_right','i','a')+('exact hi','exact hib','exact hv_witness','exact hx_witness_right_left')
    return body


def _exists_body(graph: Callable[..., str], append: str, *, delta: bool) -> tuple[str, ...]:
    body = _intro('N')+('induction N',)+_intro('w')
    body += (f"have hz : exists F. ({_table('0','F','base_actual')}) /\\ ({_table_at('F','0','w','base_zero')})",)
    body += _call('arithmetic_signed_table_singleton','w')+('cases hz','cases hz_witness','exists x','split','split','exact hz_witness_left')
    body += _intro('i','z','hi','hb','he')+('exfalso','apply hi')+_call('le_zero','i')
    body += ('exact hb','exact hz_witness_right')+_intro('w')
    previous = _and(graph('N','F','exists_previous'),_table_at('F','0','w','exists_zero'))
    body += (f'have hp : exists F. ({previous})',)+_call('IH','w')+('cases hp','cases hp_witness')
    if delta:
        body += (f'have hv : exists z. ({_delta_value("S N","z")})',)
        body += _call('dirichlet_kronecker_delta_value_exists','S N')+('cases hv',)
        output = 'x2'
        args = ('N','x','x1')
    else:
        output = 'x1'
        args = ('N','x')
    extension = _and(graph('S N','G','exists_next'),_table_equal('x','G','S N','exists_preserved'))
    body += (f'have he : exists G. ({extension})',)+_call(append,*args)+('exact hp_witness_left',)
    if delta:
        body += ('exact hv_witness',)
    body += ('cases he','cases he_witness','cases he_witness_left',f'exists {output}','split','exact he_witness_left')
    body += _call('arithmetic_signed_table_equal_entry_transport','S N','x',output,'S N','0','w')
    body += ('exact he_witness_left_left','exact he_witness_right')+_call('zero_le','S N')
    body += _call('succ_le_succ','0','N')+_call('zero_le','N')+('exact hp_witness_right',)
    return body


def _construction_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec('dirichlet_kronecker_delta_value_exists',
             f'forall n. exists z. ({_delta_value("n","z")})',('eq_decidable',),
             _intro('n')+('have hc : n=1 \\/ ~(n=1)',)+_call('eq_decidable','n','1')
             +('cases hc','exists 2','split','intro he','refl','intro he','exfalso','apply he','exact hc_left',
               'exists 0','split','intro he','exfalso','apply hc_right','exact he','intro he','refl'),
             'Constructively decide whether an index is one, obtaining its actual zero-or-one signed value before extending any table.'),
        spec('dirichlet_constant_one_table_append',
             f"forall N U. ({_one('N','U','one_append_input')}) -> exists V. "
             f"({_one('S N','V','one_append_output')}) /\\ ({_table_equal('U','V','S N','one_append_prefix')})",
             ('arithmetic_signed_table_append','le_eq_or_lt','divisor_signed_table_at_functional',
              'le_of_succ_le_succ','divisor_signed_table_lookup'),_append_body(_one,delta=False),
             'Actually append signed one at the next positive index by paired beta recoding, preserving the full previous prefix including zero.'),
        spec('dirichlet_kronecker_delta_table_append',
             f"forall N E z. ({_delta('N','E','delta_append_input')}) -> ({_delta_value('S N','z')}) -> exists D. "
             f"({_delta('S N','D','delta_append_output')}) /\\ ({_table_equal('E','D','S N','delta_append_prefix')})",
             ('arithmetic_signed_table_append','le_eq_or_lt','divisor_signed_table_at_functional',
              'le_of_succ_le_succ','divisor_signed_table_lookup'),_append_body(_delta,delta=True),
             'Append the separately chosen actual delta value, preserving every earlier signed entry rather than assuming a table oracle.'),
        spec('dirichlet_constant_one_table_exists',
             f"forall N w. exists U. ({_one('N','U','one_exists_table')}) /\\ ({_table_at('U','0','w','one_exists_zero')})",
             ('arithmetic_signed_table_singleton','le_zero','dirichlet_constant_one_table_append',
              'arithmetic_signed_table_equal_entry_transport','zero_le','succ_le_succ'),
             _exists_body(_one,'dirichlet_constant_one_table_append',delta=False),
             'For every finite bound, construct a genuine constant-one table retaining any prescribed signed value at zero, including the empty positive domain.'),
        spec('dirichlet_kronecker_delta_table_exists',
             f"forall N w. exists E. ({_delta('N','E','delta_exists_table')}) /\\ ({_table_at('E','0','w','delta_exists_zero')})",
             ('arithmetic_signed_table_singleton','le_zero','dirichlet_kronecker_delta_value_exists','dirichlet_kronecker_delta_table_append',
              'arithmetic_signed_table_equal_entry_transport','zero_le','succ_le_succ'),
             _exists_body(_delta,'dirichlet_kronecker_delta_table_append',delta=True),
             'Finite constructive equality decisions and actual beta extensions build the delta table for every N, preserving any zero entry.'),
    )


def _representation_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    result = []
    for graph, stem in ((_one,'constant_one'),(_delta,'kronecker_delta')):
        transport = _intro('N','F','G','hf','hg','he')+('cases hf','split','exact hg')
        transport += _intro('i','z','hi','hb','hz')
        transport += (f"have hv : exists v. ({_table_at('F','i','v',stem+'transport_lookup')})",)
        transport += _call('divisor_signed_table_lookup','N','F','i')+('exact hf_left','exact hb','cases hv','have heq : x=z')
        transport += _call('he','i','x','z')+('exact hi','exact hb','exact hv_witness','exact hz')
        if graph is _one:
            transport += ('trans x','symm','exact heq')+_call('hf_right','i','x')
            transport += ('exact hi','exact hb','exact hv_witness')
        else:
            transport += (f'have hd : {_delta_value("i","x")}',)+_call('hf_right','i','x')
            transport += ('exact hi','exact hb','exact hv_witness')
            transport += _rewrite('heq',_delta_value('i','x'),'x','hd')+('exact hd',)
        result.append(spec('dirichlet_'+stem+'_table_reencoding',
            f"forall N F G. ({graph('N','F',stem+'transport_source')}) -> ({_table('N','G',stem+'transport_valid')}) -> "
            f"({_positive_equal('F','G','N',stem+'transport_equal')}) -> ({graph('N','G',stem+'transport_result')})",
            ('divisor_signed_table_lookup',),transport,
            'Equal represented positive values preserve this table graph without equating table codes, component representatives or their arbitrary zero entries.'))
        if graph is _one:
            unique = _intro('N','F','G','hf','hg','i','a','b','hi','hb','ha','hbv')
            unique += ('trans 2','apply dirichlet_constant_one_table_value')
            unique += ('exact hf','exact hi','exact hb','exact ha','symm')
            unique += ('apply dirichlet_constant_one_table_value',)
            unique += ('exact hg','exact hi','exact hb','exact hbv')
            dependencies = ('dirichlet_constant_one_table_value',)
        else:
            unique = _intro('N','F','G','hf','hg')+('cases hf','cases hg')+_intro('i','a','b','hi','hb','ha','hbv')
            unique += (f'have hfa : {_delta_value("i","a")}',)+_call('hf_right','i','a')
            unique += ('exact hi','exact hb','exact ha',f'have hgb : {_delta_value("i","b")}')
            unique += _call('hg_right','i','b')+('exact hi','exact hb','exact hbv','cases hfa','cases hgb',
                      'have hc : i=1 \\/ ~(i=1)')+_call('eq_decidable','i','1')
            unique += ('cases hc','trans 2','apply hfa_left','exact hc_left','symm','apply hgb_left','exact hc_left',
                       'trans 0','apply hfa_right','exact hc_right','symm','apply hgb_right','exact hc_right')
            dependencies = ('eq_decidable',)
        result.append(spec('dirichlet_'+stem+'_table_positive_unique',
            f"forall N F G. ({graph('N','F',stem+'unique_first')}) -> ({graph('N','G',stem+'unique_second')}) -> "
            f"({_positive_equal('F','G','N',stem+'unique_result')})",dependencies,unique,
            'All constructed representations agree at every positive in-domain entry; neither equality at zero nor equality of arbitrary table encodings is asserted.'))
    return tuple(result)


def _quotient_guards(n: str, d: str, q: str, equation: str, *, bound: str) -> tuple[str, ...]:
    """Emit only ordinary uses of existing factor nonzero/divisor-bound proofs."""
    body = (f'have hqpositive : ~({q}=0)','intro hqzero')
    body += _call('factor_nonzero_right',n,d,q)+('exact hn','exact '+equation,'exact hqzero',
                f"have hqbound : {_le(q,'N','quotient_domain')}")
    body += _call('le_trans',q,n,'N')+_call('divisor_le_nonzero',q,n)
    body += ('exact hn',f'exists {d}',f'trans ({d})*({q})','exact '+equation,'apply mul_comm','exact '+bound)
    return body


def _delta_entry_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    p = 'he_left_right_witness_witness_witness'
    before = _intro('N','F','E','n','d','z','hd','hn','hb','hbefore','he')+('cases he','cases he_left')
    before += _cases('he_left_right',3)+_parts(p,4)
    before += _quotient_guards('n','d','x',p+'_left',bound='hb')
    before += ('have hqnotone : ~(x=1)','intro hqone','have heq : n=d','trans d*x','exact '+p+'_left',
               'trans d*1','rewrite hqone','refl','apply mul_one')
    before += _call('lt_not_le','d','n')+('exact hbefore',)
    before += _rewrite('heq',_le('n','d','before_contradiction'),'n')+_call('le_refl','d')
    before += ('have hzero : x2=0',)+_call('dirichlet_kronecker_delta_table_other_value','N','E','x','x2')
    before += ('exact hd','exact hqpositive','exact hqnotone','exact hqbound','exact '+p+'_right_right_left')
    before += _rewrite('hzero',_mul_code('x1','x2','z','before_zero_product'),'x2',p+'_right_right_right')
    before += _call('signed_mul_functional','x1','0','z','0')+('exact '+p+'_right_right_right',)
    before += _call('signed_mul_zero_right','x1')+('cases he_right','exact he_right_right')

    last = _intro('N','F','E','n','a','hd','hn','hb','ha')+('cases hd',
                 f"have hbound : {_le('1','N','last_one_bound')}")
    last += _call('le_trans','1','n','N')+_call('one_le_of_ne_zero','n')+('exact hn','exact hb',
                 f"have hx : exists x. ({_table_at('E','1','x','last_one_lookup')})")
    last += _call('divisor_signed_table_lookup','N','E','1')+('exact hd_left','exact hbound','cases hx','have hv : x=2')
    last += _call('dirichlet_kronecker_delta_table_one_value','N','E','x')+('exact hd','exact hbound','exact hx_witness')
    last += _rewrite('hv',_table_at('E','1','x','last_one_rewrite'),'x','hx_witness')
    last += _call('dirichlet_convolution_entry_from_quotient','F','E','n','n','1','a','2','a')
    last += ('exact hn','symm','apply mul_one','exact ha','exact hx_witness')+_call('signed_mul_one_right','a')
    return (
        spec('dirichlet_delta_right_entry_before_input',
             f"forall N F E n d z. ({_delta('N','E','before_delta')}) -> ~(n=0) -> ({_le('n','N','before_domain')}) -> "
             f"({_lt('d','n','before_index')}) -> ({_entry('F','E','n','d','z','before_entry')}) -> z=0",
             ('factor_nonzero_right','le_trans','divisor_le_nonzero','mul_comm','mul_one','lt_not_le','le_refl',
              'dirichlet_kronecker_delta_table_other_value','signed_mul_functional','signed_mul_zero_right'),before,
             'Every actual summand before n vanishes: a real complementary quotient is positive and cannot be one, while omitted indices are already zero.'),
        spec('dirichlet_delta_right_last_entry',
             f"forall N F E n a. ({_delta('N','E','last_delta')}) -> ~(n=0) -> ({_le('n','N','last_domain')}) -> "
             f"({_table_at('F','n','a','last_source')}) -> ({_entry('F','E','n','n','a','last_result')})",
             ('le_trans','one_le_of_ne_zero','divisor_signed_table_lookup','dirichlet_kronecker_delta_table_one_value',
              'dirichlet_convolution_entry_from_quotient','mul_one','signed_mul_one_right'),last,
             'At the final divisor n, actually read delta(1), use the quotient n=n*1, and multiply F(n) by signed one.'),
    )


def _delta_law_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    value = _intro('N','F','E','n','a','z','hd','hb','ha','hc')
    value += ('cases hc','cases hc_right','cases hc_right_witness',
              f"have hzero : {_zero_window('x','0','n','unit_zero_prefix')}")
    value += _intro('i','v','hi','hib','hv')
    value += _call('dirichlet_delta_right_entry_before_input','N','F','E','n','i','v')
    value += ('exact hd','exact hc_left','exact hb','exact hib')
    value += _call('dirichlet_convolution_prefix_lookup','F','E','n','n','x','i','v')
    value += ('exact hc_right_witness_left',)+_call('le_trans','i','S i','n')
    value += _call('le_succ_self','i')+('exact hib','exact hv',
              f"have hlast : {_table_at('x','n','a','unit_last_entry')}")
    value += _call('dirichlet_convolution_prefix_value_from_entry','F','E','n','n','x','n','a')
    value += ('exact hc_right_witness_left',)+_call('le_refl','n')
    value += _call('dirichlet_delta_right_last_entry','N','F','E','n','a')
    value += ('exact hd','exact hc_left','exact hb','exact ha')
    value += _call('signed_prefix_sum_last_value','x','n','a','z')
    value += ('exact hzero','exact hlast','exact hc_right_witness_right')

    actual = _intro('N','F','E','n','a','hf','hd','hn','hb','ha')+('cases hd',
              f"have hc : exists z. ({_convolution('F','E','n','z','unit_actual_sum')})")
    actual += _call('dirichlet_convolution_sum_exists','N','F','E','n')
    actual += ('exact hf','exact hd_left','exact hn','exact hb','cases hc','have he : x=a')
    actual += _call('dirichlet_delta_right_sum_value','N','F','E','n','a','x')
    actual += ('exact hd','exact hb','exact ha','exact hc_witness')
    actual += _rewrite('he',_convolution('F','E','n','x','unit_actual_rewrite'),'x','hc_witness')+('exact hc_witness',)

    table = _intro('N','F','E','hf','hd')+('cases hd','split','exact hf','split','exact hd_left','split','exact hf')
    table += _intro('n','z','hn','hb','hz')+_call('dirichlet_delta_right_sum','N','F','E','n','z')
    table += ('exact hf','exact hd','exact hn','exact hb','exact hz')

    witness = _intro('N','F','w','hf')+(f"have he : exists E. ({_delta('N','E','unit_exists_delta')}) /\\ ({_table_at('E','0','w','unit_exists_zero')})",)
    witness += _call('dirichlet_kronecker_delta_table_exists','N','w')+('cases he','cases he_witness','exists x',
               'split','exact he_witness_left','split','exact he_witness_right','split')
    for name in ('dirichlet_delta_right_table','dirichlet_delta_left_table'):
        witness += _call(name,'N','F','x')+('exact hf','exact he_witness_left')
    return (
        spec('dirichlet_delta_right_sum_value',
             f"forall N F E n a z. ({_delta('N','E','unit_value_delta')}) -> ({_le('n','N','unit_value_bound')}) -> "
             f"({_table_at('F','n','a','unit_value_source')}) -> ({_convolution('F','E','n','z','unit_value_convolution')}) -> z=a",
             ('dirichlet_delta_right_entry_before_input','dirichlet_convolution_prefix_lookup','le_trans','le_succ_self',
              'dirichlet_convolution_prefix_value_from_entry','le_refl','dirichlet_delta_right_last_entry','signed_prefix_sum_last_value'),value,
             'The actual zero-prefix/last-entry fold proves (F*delta)(n)=F(n), with positivity supplied by the convolution itself.'),
        spec('dirichlet_delta_right_sum',
             f"forall N F E n a. ({_table('N','F','unit_sum_input')}) -> ({_delta('N','E','unit_sum_delta')}) -> ~(n=0) -> "
             f"({_le('n','N','unit_sum_bound')}) -> ({_table_at('F','n','a','unit_sum_source')}) -> ({_convolution('F','E','n','a','unit_sum_result')})",
             ('dirichlet_convolution_sum_exists','dirichlet_delta_right_sum_value'),actual,
             'Construct a genuine convolution fold and prove its value equals the given actual F(n), rather than postulating the desired unit identity.'),
        spec('dirichlet_delta_right_table',
             f"forall N F E. ({_table('N','F','unit_table_input')}) -> ({_delta('N','E','unit_table_delta')}) -> "
             f"({_convolution_table('N','F','E','F','unit_table_result')})",('dirichlet_delta_right_sum',),table,
             'The original represented table F is a genuine whole-table right-unit convolution output on every positive input through N.'),
        spec('dirichlet_delta_left_table',
             f"forall N F E. ({_table('N','F','left_unit_input')}) -> ({_delta('N','E','left_unit_delta')}) -> "
             f"({_convolution_table('N','E','F','F','left_unit_result')})",
             ('dirichlet_convolution_table_commutative','dirichlet_delta_right_table'),
             _intro('N','F','E','hf','hd')+_call('dirichlet_convolution_table_commutative','N','F','E','F')
             +_call('dirichlet_delta_right_table','N','F','E')+('exact hf','exact hd'),
             'Actual divisor-complement commutativity turns the proved right-unit table into the left-unit table without imposing a zero-entry condition.'),
        spec('dirichlet_delta_unit_exists',
             f"forall N F w. ({_table('N','F','unit_exists_input')}) -> exists E. "+_and(
                 _delta('N','E','unit_exists_result'),_table_at('E','0','w','unit_exists_prescribed_zero'),
                 _convolution_table('N','F','E','F','unit_exists_right'),_convolution_table('N','E','F','F','unit_exists_left')),
             ('dirichlet_kronecker_delta_table_exists','dirichlet_delta_right_table','dirichlet_delta_left_table'),witness,
             'Every actual finite signed arithmetic table has a constructed two-sided convolution unit, with any requested unrelated value at index zero.'),
    )


def _one_entry_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    p = 'he_left_right_witness_witness_witness'
    forward = _intro('N','F','U','n','d','z','hu','hn','hb','he')+('cases he','cases he_left')
    forward += _cases('he_left_right',3)+_parts(p,4)
    forward += _quotient_guards('n','d','x',p+'_left',bound='hb')
    forward += ('have hv : x2=2',)+_call('dirichlet_constant_one_table_value','N','U','x','x2')
    forward += ('exact hu','exact hqpositive','exact hqbound','exact '+p+'_right_right_left')
    forward += _rewrite('hv',_mul_code('x1','x2','z','ones_forward_product'),'x2',p+'_right_right_right')
    forward += ('have heq : z=x1',)+_call('signed_mul_functional','x1','2','z','x1')
    forward += ('exact '+p+'_right_right_right',)+_call('signed_mul_one_right','x1')
    forward += ('left','split','exact he_left_left','exists x','split','exact '+p+'_left')
    forward += _rewrite('heq',_table_at('F','d','z','ones_forward_input'),'z')
    forward += ('exact '+p+'_right_left','cases he_right','right','exact he_right')

    p = 'he_left_right_witness'
    backward = _intro('N','F','U','n','d','z','hu','hn','hb','he')
    backward += ('cases he','cases he_left','cases he_left_right','cases '+p)
    backward += _quotient_guards('n','d','x',p+'_left',bound='hb')
    backward += ('cases hu',f"have hv : exists v. ({_table_at('U','x','v','ones_reverse_lookup')})")
    backward += _call('divisor_signed_table_lookup','N','U','x')+('exact hu_left','exact hqbound','cases hv','have heq : x1=2')
    backward += _call('dirichlet_constant_one_table_value','N','U','x','x1')
    backward += ('exact hu','exact hqpositive','exact hqbound','exact hv_witness')
    backward += _rewrite('heq',_table_at('U','x','x1','ones_reverse_rewrite'),'x1','hv_witness')
    backward += _call('dirichlet_convolution_entry_from_quotient','F','U','n','d','x','z','2','z')
    backward += ('exact he_left_left','exact '+p+'_left','exact '+p+'_right','exact hv_witness')
    backward += _call('signed_mul_one_right','z')+('cases he_right','right','exact he_right')
    common = ('factor_nonzero_right','le_trans','divisor_le_nonzero','mul_comm','dirichlet_constant_one_table_value')
    return (
        spec('dirichlet_constant_one_entry_to_divisor_mask',
             f"forall N F U n d z. ({_one('N','U','ones_entry_source')}) -> ~(n=0) -> ({_le('n','N','ones_entry_bound')}) -> "
             f"({_entry('F','U','n','d','z','ones_entry_convolution')}) -> ({_mask_entry('F','n','d','z','ones_entry_mask')})",
             common+('signed_mul_functional','signed_mul_one_right'),forward,
             'At every actual positive divisor the complementary one-table factor is signed one, so the convolution entry is precisely the existing divisor-mask entry.'),
        spec('dirichlet_constant_one_entry_from_divisor_mask',
             f"forall N F U n d z. ({_one('N','U','ones_reverse_source')}) -> ~(n=0) -> ({_le('n','N','ones_reverse_bound')}) -> "
             f"({_mask_entry('F','n','d','z','ones_reverse_mask')}) -> ({_entry('F','U','n','d','z','ones_reverse_convolution')})",
             common+('divisor_signed_table_lookup','dirichlet_convolution_entry_from_quotient','signed_mul_one_right'),backward,
             'Construct the actual bounded complementary lookup and its signed product from a genuine divisor-mask entry; omitted zero/nondivisor entries stay zero.'),
    )


def _one_prefix_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    result = []
    for reverse in (False,True):
        source = _mask('F','n','l','M','one_prefix_source') if reverse else _prefix('F','U','n','l','M','one_prefix_source')
        target = _prefix('F','U','n','l','M','one_prefix_result') if reverse else _mask('F','n','l','M','one_prefix_result')
        direction = 'from' if reverse else 'to'
        entry = 'dirichlet_constant_one_entry_'+direction+'_divisor_mask'
        body = _intro('N','F','U','n','l','M','hu','hn','hb','hp')+('cases hp','split','exact hp_left')
        body += _intro('d','z','hd','hz')+_call(entry,'N','F','U','n','d','z')
        body += ('exact hu','exact hn','exact hb')+_call('hp_right','d','z')+('exact hd','exact hz')
        result.append(spec('dirichlet_constant_one_prefix_'+direction+'_divisor_mask',
            f"forall N F U n l M. ({_one('N','U','one_prefix_ones')}) -> ~(n=0) -> ({_le('n','N','one_prefix_bound')}) -> "
            f'({source}) -> ({target})',(entry,),body,
            'The same actual signed prefix represents the weighted convolution mask and the existing divisor mask; this preserves all witnesses and arbitrary prefix lengths.'))
    return tuple(result)


def _one_iff(F: str, U: str, n: str, z: str, tag: str) -> str:
    convolution = _convolution(F,U,n,z,tag+'convolution')
    divisor = _divisor_sum(F,n,z,tag+'divisor')
    return _and(f'({convolution}) -> ({divisor})',f'({divisor}) -> ({convolution})')


def _one_law_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    equivalence = _intro('N','F','U','n','z','hf','hu','hn','hb')+('split',)
    for direction in ('to','from'):
        equivalence += ('intro hs','cases hs','cases hs_right','cases hs_right_witness','split','exact hn','exists x','split')
        equivalence += _call('dirichlet_constant_one_prefix_'+direction+'_divisor_mask','N','F','U','n','n','x')
        equivalence += ('exact hu','exact hn','exact hb','exact hs_right_witness_left','exact hs_right_witness_right')

    law = f"forall n z. ~(n=0) -> ({_le('n','N','ones_exists_bound')}) -> ({_one_iff('F','U','n','z','ones_exists_law')})"
    witness = _intro('N','F','w','hf')
    witness += (f"have hu : exists U. ({_one('N','U','ones_exists_construct')}) /\\ ({_table_at('U','0','w','ones_exists_zero')})",)
    witness += _call('dirichlet_constant_one_table_exists','N','w')+('cases hu','cases hu_witness','exists x',
                'split','exact hu_witness_left','split','exact hu_witness_right')
    witness += _intro('n','z','hn','hb')+_call('dirichlet_constant_one_sum_iff','N','F','x','n','z')
    witness += ('exact hf','exact hu_witness_left','exact hn','exact hb')
    return (
        spec('dirichlet_constant_one_sum_iff',
             f"forall N F U n z. ({_table('N','F','ones_sum_input')}) -> ({_one('N','U','ones_sum_ones')}) -> ~(n=0) -> "
             f"({_le('n','N','ones_sum_bound')}) -> ({_one_iff('F','U','n','z','ones_sum_result')})",
             ('dirichlet_constant_one_prefix_to_divisor_mask','dirichlet_constant_one_prefix_from_divisor_mask'),equivalence,
             'Actual convolution with a constant-one table is equivalent to the independently defined signed divisor sum, with exactly the same constructed mask and fold.'),
        spec('dirichlet_constant_one_realizes_divisor_sum',
             f"forall N F w. ({_table('N','F','ones_exists_input')}) -> exists U. "+_and(
                 _one('N','U','ones_exists_result'),_table_at('U','0','w','ones_exists_prescribed_zero'),law),
             ('dirichlet_constant_one_table_exists','dirichlet_constant_one_sum_iff'),witness,
             'Construct an actual constant-one table with any chosen zero entry, and prove simultaneously at every positive in-domain input that its convolution is the existing divisor transform.'),
    )


def make_dirichlet_units_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_lookup_rows(spec)+_construction_rows(spec)+_representation_rows(spec)
            +_delta_entry_rows(spec)+_delta_law_rows(spec)+_one_entry_rows(spec)
            +_one_prefix_rows(spec)+_one_law_rows(spec))


__all__ = [
    'dirichlet_constant_one_table_relation', 'dirichlet_kronecker_delta_table_relation',
    'make_dirichlet_units_candidate_theorems',
]
