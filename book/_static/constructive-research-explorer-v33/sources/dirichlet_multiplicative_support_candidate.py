"""Construct the honest support bijection for coprime Dirichlet products.

The source has (m+1)(n+1) slots and the target mn+1 slots. Only genuinely
nonzero summands are matched. Inactive collisions and unequal window lengths
are allowed; the map is never asserted to be a whole-prefix permutation.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_multiplicative_candidate import _multiplicative
from .coprime_divisor_decomposition_candidate import _pair, _pair_bounds
from .dirichlet_convolution_candidate import _entry, _prefix
from .divisor_pair_index_candidate import _map
from .divisor_sum_table_candidate import _table, _table_at
from .prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _dvd, _intro, _le, _lt, _part, _parts, _public, _rewrite,
)
from .signed_cartesian_product_candidate import _product
from .signed_support_reindex_candidate import (
    _cover, _injective, _preserve, _reindex,
)
from .signed_table_operations_candidate import _mul_code
from .squarefree_decomposition_candidate import _cop


PARAMETERS = ('N','F','G','m','n','A','B','T','Q','r','s')


def _length(m: str, n: str) -> str:
    return f'(S ({m}))*(S ({n}))'


def _index(n: str, d: str, e: str) -> str:
    return f'(S ({n}))*({d})+({e})'


def _data(N: str, F: str, G: str, m: str, n: str, A: str, B: str,
          T: str, Q: str, r: str, s: str, tag: str) -> str:
    return _and(
        _multiplicative(N,F,tag+'F'), _multiplicative(N,G,tag+'G'),
        f'~(({m})=0)', f'~(({n})=0)', _le(f'({m})*({n})',N,tag+'bound'),
        _cop(m,n,tag+'coprime'), _prefix(F,G,m,m,A,tag+'left'),
        _prefix(F,G,n,n,B,tag+'right'), _product(A,B,T,f'S ({m})',f'S ({n})',tag+'cartesian'),
        _prefix(F,G,f'({m})*({n})',f'({m})*({n})',Q,tag+'target'),
        _map(f'S ({n})',_length(m,n),r,s,tag+'map'))


def _grid(F: str, G: str, m: str, n: str, i: str, z: str,
          d: str, e: str, a: str, b: str, tag: str) -> str:
    return _and(
        f'({i})=({_index(n,d,e)})', _lt(d,f'S ({m})',tag+'row'), _lt(e,f'S ({n})',tag+'column'),
        _pair(m,n,f'({d})*({e})',d,e,tag+'pair'),
        _entry(F,G,m,d,a,tag+'left'), _entry(F,G,n,e,b,tag+'right'), _mul_code(a,b,z,tag+'product'))


def dirichlet_coprime_product_data_relation(
    N: str, F: str, G: str, m: str, n: str, A: str, B: str,
    T: str, Q: str, r: str, s: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """Actual input masks, product table and beta map; no sum or bijection law."""
    return _public(_data,(N,F,G,m,n,A,B,T,Q,r,s),tag=tag,variables=variables)


def dirichlet_divisor_grid_witness_relation(
    F: str, G: str, m: str, n: str, i: str, z: str,
    d: str, e: str, a: str, b: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """Actual positive divisor coordinates, their two summands and signed product."""
    return _public(_grid,(F,G,m,n,i,z,d,e,a,b),tag=tag,variables=variables)


def _context(tag: str) -> str:
    return _data(*PARAMETERS,tag)


def _field(index: int, name: str = 'hd') -> str:
    return _part(name,11,index)


def _grid_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body = _intro(*PARAMETERS,'i','z','hd','hi','hz','hnz') + _parts('hd',11)
    coordinates = _and('i=(S n)*d+e',_lt('d','S m','active_row'),_lt('e','S n','active_column'),
                       _table_at('A','d','a','active_first'),_table_at('B','e','b','active_second'),
                       _mul_code('a','b','z','active_product'))
    body += (f'have hv : exists d e a b. ({coordinates})',)
    body += _call('signed_cartesian_product_flat_lookup','A','B','T','S m','S n','i','z')
    body += ('exact '+_field(8),'exact hi','exact hz') + _cases('hv',4) + _parts('hv_witness_witness_witness_witness',6)
    p = lambda k: _part('hv_witness_witness_witness_witness',6,k)
    for name, number, index, value, prefix, bound, lookup in (
        ('hl','m','x','x2',_field(6),p(1),p(3)),
        ('hr','n','x1','x3',_field(7),p(2),p(4)),
    ):
        body += (f'have {name} : {_entry("F","G",number,index,value,name+"entry")}',)
        body += _call('dirichlet_convolution_prefix_lookup','F','G',number,number,'A' if name=='hl' else 'B',index,value)
        body += ('exact '+prefix,) + _call('le_of_succ_le_succ',index,number) + ('exact '+bound,'exact '+lookup)
    body += ('have hvalues : ~(x2=0) /\\ ~(x3=0)',) + _call('signed_mul_nonzero_factors','x2','x3','z')
    body += ('exact '+p(5),'exact hnz','cases hvalues')
    for name, number, index, value, hypothesis, nonzero in (
        ('hsleft','m','x','x2','hl','hvalues_left'),
        ('hsright','n','x1','x3','hr','hvalues_right'),
    ):
        body += (f'have {name} : '+_and(f'~({index}=0)',_dvd(index,number,name+'divisor')),)
        body += _call('dirichlet_convolution_entry_nonzero_support','F','G',number,index,value)
        body += ('exact '+hypothesis,'exact '+nonzero,'cases '+name)
    body += ('exists x','exists x1','exists x2','exists x3','split','exact '+p(0),
             'split','exact '+p(1),'split','exact '+p(2),'split',
             'split','exact hsleft_left','split','exact hsright_left','split','exact hsleft_right',
             'split','exact hsright_right','refl','split','exact hl','split','exact hr','exact '+p(5))
    return (spec(
        'dirichlet_coprime_grid_nonzero_coordinates',
        f'forall {" ".join(PARAMETERS)} i z. ({_context("active_data")}) -> '
        f'({_lt("i",_length("m","n"),"active_index")}) -> ({_table_at("T","i","z","active_lookup")}) -> ~(z=0) -> '
        f'exists d e a b. ({_grid("F","G","m","n","i","z","d","e","a","b","active_result")})',
        ('signed_cartesian_product_flat_lookup','dirichlet_convolution_prefix_lookup','le_of_succ_le_succ',
         'signed_mul_nonzero_factors','dirichlet_convolution_entry_nonzero_support'), body,
        'Every genuinely nonzero product-table entry decodes to a positive divisor pair and two actual nonzero convolution summands; zero and nondivisor collisions are excluded constructively.'),)


def _preservation_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body = _intro(*PARAMETERS,'hd') + _parts('hd',11) + _intro('i','z','hi','hz','hnz')
    body += (f'have hg : exists d e a b. ({_grid("F","G","m","n","i","z","d","e","a","b","preserve_grid")})',)
    body += _call('dirichlet_coprime_grid_nonzero_coordinates',*PARAMETERS,'i','z')
    body += ('exact hd','exact hi','exact hz','exact hnz') + _cases('hg',4) + _parts('hg_witness_witness_witness_witness',7)
    p = lambda k: _part('hg_witness_witness_witness_witness',7,k)
    body += (f'have hb : {_le("x*x1","m*n","preserve_product_bound")}',)
    body += _call('mul_le_mul','x','m','x1','n')
    body += _call('le_of_succ_le_succ','x','m') + ('exact '+p(1),)
    body += _call('le_of_succ_le_succ','x1','n') + ('exact '+p(2),'exists x*x1','split')
    body += _call('divisor_pair_index_map_lookup','S n',_length('m','n'),'r','s','i','x','x1')
    body += ('exact '+_field(10),'exact hi','exact '+p(2),'exact '+p(0),'split')
    body += _call('succ_le_succ','x*x1','m*n') + ('exact hb',)
    body += _call('dirichlet_convolution_prefix_value_from_entry','F','G','m*n','m*n','Q','x*x1','z')
    body += ('exact '+_field(9),'exact hb')
    body += _call('dirichlet_multiplicative_pair_entry','N','F','G','m','n','x','x1','x2','x3','z')
    body += tuple('exact '+_field(k) for k in range(6))
    body += ('exact '+p(3),'exact '+p(4),'exact '+p(5),'exact '+p(6))
    return (spec(
        'dirichlet_coprime_grid_support_preserving',
        f'forall {" ".join(PARAMETERS)}. ({_context("preserve_data")}) -> '
        f'({_preserve("T","Q","r","s",_length("m","n"),"S (m*n)","preserve_result")})',
        ('dirichlet_coprime_grid_nonzero_coordinates','mul_le_mul','le_of_succ_le_succ',
         'divisor_pair_index_map_lookup','succ_le_succ','dirichlet_convolution_prefix_value_from_entry',
         'dirichlet_multiplicative_pair_entry'), body,
        'Each nonzero source slot has its actual beta image in the shorter target window and exactly the same signed value, by proved summand factorization.'),)


def _injectivity_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body = _intro(*PARAMETERS,'hd') + _parts('hd',11)
    body += _intro('i','k','j','a','b','hi','hk','ha','hanz','hb','hbnz','hij','hkj')
    for name, index, value, bound, lookup, nonzero in (
        ('hg','i','a','hi','ha','hanz'), ('hh','k','b','hk','hb','hbnz'),
    ):
        body += (f'have {name} : exists d e u v. ({_grid("F","G","m","n",index,value,"d","e","u","v",name+"grid")})',)
        body += _call('dirichlet_coprime_grid_nonzero_coordinates',*PARAMETERS,index,value)
        body += ('exact hd','exact '+bound,'exact '+lookup,'exact '+nonzero)
        body += _cases(name,4) + _parts(name+'_witness'*4,7)
    p = lambda k: _part('hg_witness_witness_witness_witness',7,k)
    q = lambda k: _part('hh_witness_witness_witness_witness',7,k)
    for name, index, first, second, bound, column, equation, beta in (
        ('heqi','i','x','x1','hi',p(2),p(0),'hij'),
        ('heqk','k','x4','x5','hk',q(2),q(0),'hkj'),
    ):
        body += (f'have {name} : j={first}*{second}',)
        body += _call('divisor_pair_index_map_value','S n',_length('m','n'),'r','s',index,first,second,'j')
        body += ('exact '+_field(10),'exact '+bound,'exact '+column,'exact '+equation,'exact '+beta)
    for name, first, second, equation, pair in (
        ('hpi','x','x1','heqi',p(3)), ('hpk','x4','x5','heqk',q(3)),
    ):
        target = _pair('m','n','j',first,second,name+'same_image')
        body += (f'have {name} : {target}',) + _rewrite(equation,target,'j') + ('exact '+pair,)
    body += ('have heq : x=x4 /\\ x1=x5',)
    body += _call('coprime_divisor_factor_pair_unique','m','n','j','x','x1','x4','x5')
    body += ('exact '+_field(5),'exact hpi','exact hpk','cases heq',
             'trans (S n)*x+x1','exact '+p(0),'trans (S n)*x4+x5',
             'congr','congr','refl','exact heq_left','exact heq_right','symm','exact '+q(0))
    return (spec(
        'dirichlet_coprime_grid_support_injective',
        f'forall {" ".join(PARAMETERS)}. ({_context("injective_data")}) -> '
        f'({_injective("T","r","s",_length("m","n"),"injective_result")})',
        ('dirichlet_coprime_grid_nonzero_coordinates','divisor_pair_index_map_value',
         'coprime_divisor_factor_pair_unique'), body,
        'Equal beta images of two genuinely nonzero source slots give the same positive divisor pair by gcd uniqueness, hence the same flattened index; inactive collisions remain permitted.'),)


def _coverage_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body = _intro(*PARAMETERS,'hd') + _parts('hd',11) + _parts(_field(8),4)
    body += _intro('j','z','hj','hz','hnz')
    body += (f'have ht : {_entry("F","G","m*n","j","z","cover_target_entry")}',)
    body += _call('dirichlet_convolution_prefix_lookup','F','G','m*n','m*n','Q','j','z')
    body += ('exact '+_field(9),) + _call('le_of_succ_le_succ','j','m*n') + ('exact hj','exact hz')
    body += (f'have hs : {_and("~(j=0)",_dvd("j","m*n","cover_target_divisor"))}',)
    body += _call('dirichlet_convolution_entry_nonzero_support','F','G','m*n','j','z')
    body += ('exact ht','exact hnz','cases hs')
    body += (f'have hp : exists d e. ({_pair("m","n","j","d","e","cover_actual_pair")})',)
    body += _call('coprime_divisor_factor_pair_exists','m','n','j')
    body += ('exact hs_left','exact '+_field(5),'exact hs_right') + _cases('hp',2) + _parts('hp_witness_witness',5)
    pair = 'hp_witness_witness'
    pair_field = lambda k: _part(pair,5,k)
    body += (f'have hb : {_pair_bounds("m","n","x","x1","cover_pair_bounds")}',)
    body += _call('coprime_divisor_factor_pair_bounds','m','n','j','x','x1')
    body += ('exact '+_field(2),'exact '+_field(3),'exact '+_field(5),'exact '+pair) + _parts('hb',3)
    body += (f'have hi : {_lt(_index("n","x","x1"),_length("m","n"),"cover_source_bound")}',
             'have hcomm : (S n)*x=x*(S n)','apply mul_comm','rewrite hcomm')
    body += _call('matrix_integer_rectangular_index_bound','S m','S n','x','x1')
    body += _call('succ_le_succ','x','m') + ('exact hb_left',)
    body += _call('succ_le_succ','x1','n') + ('exact hb_right_left',)
    cart = _field(8)
    for name, table, domain, index, hypothesis in (
        ('hlv','A','0','x',_part(cart,4,0)),
        ('hrv','B','0','x1',_part(cart,4,1)),
        ('hwv','T',_length('m','n'),_index('n','x','x1'),_part(cart,4,2)),
    ):
        body += (f'have {name} : exists value. ({_table_at(table,index,"value",name+"actual")})',)
        body += _call('signed_table_lookup_any',domain,table,index) + ('exact '+hypothesis,'cases '+name)
    for name, number, index, value, prefix, bound, lookup in (
        ('hl','m','x','x2',_field(6),'hb_left','hlv_witness'),
        ('hr','n','x1','x3',_field(7),'hb_right_left','hrv_witness'),
    ):
        body += (f'have {name} : {_entry("F","G",number,index,value,name+"cover_entry")}',)
        body += _call('dirichlet_convolution_prefix_lookup','F','G',number,number,'A' if name=='hl' else 'B',index,value)
        body += ('exact '+prefix,'exact '+bound,'exact '+lookup)
    body += (f'have hproduct : {_mul_code("x2","x3","x4","cover_actual_product")}',)
    body += _call(_part(cart,4,3),'x','x1','x2','x3','x4')
    body += _call('succ_le_succ','x','m') + ('exact hb_left',)
    body += _call('succ_le_succ','x1','n') + ('exact hb_right_left','exact hlv_witness','exact hrv_witness','exact hwv_witness')
    body += (f'have hpair : {_pair("m","n","x*x1","x","x1","cover_pair_product")}',
             'split','exact '+pair_field(0),'split','exact '+pair_field(1),
             'split','exact '+pair_field(2),'split','exact '+pair_field(3),'refl')
    body += _rewrite(pair_field(4),_entry('F','G','m*n','j','z','cover_target_rewrite'),'j','ht')
    body += ('have heq : x4=z',) + _call('signed_mul_functional','x2','x3','x4','z') + ('exact hproduct',)
    body += _call('dirichlet_multiplicative_pair_factorization','N','F','G','m','n','x','x1','x2','x3','z')
    body += tuple('exact '+_field(k) for k in range(6)) + ('exact hpair','exact hl','exact hr','exact ht')
    body += _rewrite('heq',_table_at('T',_index('n','x','x1'),'x4','cover_value_rewrite'),'x4','hwv_witness')
    body += ('exists (S n)*x+x1','split','exact hi','split')
    body += _rewrite(pair_field(4),_at('r','s',_index('n','x','x1'),'j','cover_map_rewrite'),'j')
    body += _call('divisor_pair_index_map_lookup','S n',_length('m','n'),'r','s',_index('n','x','x1'),'x','x1')
    body += ('exact '+_field(10),'exact hi') + _call('succ_le_succ','x1','n')
    body += ('exact hb_right_left','refl','exact hwv_witness')
    return (spec(
        'dirichlet_coprime_grid_support_covering',
        f'forall {" ".join(PARAMETERS)}. ({_context("cover_data")}) -> '
        f'({_cover("T","Q","r","s",_length("m","n"),"S (m*n)","cover_result")})',
        ('dirichlet_convolution_prefix_lookup','le_of_succ_le_succ','dirichlet_convolution_entry_nonzero_support',
         'coprime_divisor_factor_pair_exists','coprime_divisor_factor_pair_bounds','mul_comm',
         'matrix_integer_rectangular_index_bound','succ_le_succ','signed_table_lookup_any','signed_mul_functional',
         'dirichlet_multiplicative_pair_factorization','divisor_pair_index_map_lookup'), body,
        'Every nonzero target summand has a genuine bounded source slot: construct its unique positive divisor pair, both input summands and the product-table lookup, then prove exact value preservation.'),)


def _assembly_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    reindex = _intro(*PARAMETERS,'hd') + _parts('hd',11) + _parts(_field(8),4) + ('cases '+_field(9),'split')
    reindex += _call('signed_table_domain_resize',_length('m','n'),'0','T') + ('exact '+_part(_field(8),4,2),'split')
    reindex += _call('signed_table_domain_resize','m*n','0','Q') + ('exact '+_field(9)+'_left','split')
    reindex += _call('dirichlet_coprime_grid_support_preserving',*PARAMETERS) + ('exact hd','split')
    reindex += _call('dirichlet_coprime_grid_support_injective',*PARAMETERS) + ('exact hd',)
    reindex += _call('dirichlet_coprime_grid_support_covering',*PARAMETERS) + ('exact hd',)

    construct = _intro('N','F','G','m','n','A','B','Q','hF','hG','hm','hn','hb','hc','hA','hB','hQ')
    construct += ('cases hA','cases hB',f'have ht : exists T. ({_product("A","B","T","S m","S n","data_product")})')
    construct += _call('signed_cartesian_product_exists','A','B','S m','S n')
    construct += _call('signed_table_domain_resize','m','0','A') + ('exact hA_left',)
    construct += _call('signed_table_domain_resize','n','0','B') + ('exact hB_left','cases ht')
    construct += (f'have hp : exists r s. ({_map("S n",_length("m","n"),"r","s","data_map")})',)
    construct += _call('divisor_pair_index_map_exists','S n',_length('m','n')) + _call('succ_ne_zero','n') + _cases('hp',2)
    construct += ('exists x','exists x1','exists x2')
    for hypothesis in ('hF','hG','hm','hn','hb','hc','hA','hB','ht_witness','hQ'):
        construct += ('split','exact '+hypothesis)
    construct += ('exact hp_witness_witness',)
    input_clauses = (
        _multiplicative('N','F','data_source_F'), _multiplicative('N','G','data_source_G'),
        '~(m=0)', '~(n=0)', _le('m*n','N','data_source_bound'), _cop('m','n','data_source_coprime'),
        _prefix('F','G','m','m','A','data_source_left'), _prefix('F','G','n','n','B','data_source_right'),
        _prefix('F','G','m*n','m*n','Q','data_source_target'),
        f'exists T r s. ({_context("data_constructed")})')
    return (
        spec('dirichlet_coprime_grid_support_reindex',
             f'forall {" ".join(PARAMETERS)}. ({_context("reindex_data")}) -> '
             f'({_reindex("T","Q","r","s",_length("m","n"),"S (m*n)","reindex_result")})',
             ('signed_table_domain_resize','dirichlet_coprime_grid_support_preserving',
              'dirichlet_coprime_grid_support_injective','dirichlet_coprime_grid_support_covering'), reindex,
             'The actual native-beta divisor-product map is a value-preserving bijection of nonzero support between two unequal finite windows; no whole-window permutation is asserted.'),
        spec('dirichlet_coprime_product_data_construct',
             'forall N F G m n A B Q. '+' -> '.join('('+clause+')' for clause in input_clauses),
             ('signed_cartesian_product_exists','signed_table_domain_resize','divisor_pair_index_map_exists','succ_ne_zero'),
             construct,
             'From the actual three summand prefixes construct the Cartesian product table and native-beta index map, with no assumed table, map, sum or reindexing conclusion.'),
    )


def make_dirichlet_multiplicative_support_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (_grid_rows(spec) + _preservation_rows(spec) + _injectivity_rows(spec)
            + _coverage_rows(spec) + _assembly_rows(spec))


__all__ = ['dirichlet_coprime_product_data_relation','dirichlet_divisor_grid_witness_relation',
           'make_dirichlet_multiplicative_support_candidate_theorems']
