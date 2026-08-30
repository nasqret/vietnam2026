"""Independent G009 support/closure contracts and hostile original-HA checks.

Finite beta models diagnose the exact signed, positive-prefix semantics.
Conditional body checks do not themselves confer dependency-closed proof,
Alpha admission, or publication authority.
"""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import importlib
import math
from pathlib import Path
import re

import pytest

from peano_lab.library import (
    dirichlet_multiplicative_support_candidate as support,
    dirichlet_multiplicative_candidate as candidate,
)
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_dirichlet_convolution_candidate import (
    expected_at, expected_convolution, expected_convolution_table, expected_dvd,
    expected_le, expected_entry, expected_positive_equal, expected_prefix,
    expected_signed_multiply, expected_table,
)
from tests.test_dirichlet_inverse_candidate import expected_inverse
from tests.test_divisor_sum_reindex_candidate import _encode_beta, _unpair
from tests.test_signed_rectangular_slice_candidate import actual_sum_trace
from tests.test_signed_table_operations_candidate import (
    decode_signed, encode_signed, model_at, model_table,
)


SOURCE_PINS = {
    'dirichlet_multiplicative_support_candidate.py':
        '56e9f8ccaa7c795e42b33984bc2346182ba3a1f820883ba884e571b89091d4a5',
    'dirichlet_multiplicative_candidate.py':
        'bb1342735115781fd8f0107d3876c95098e0b6dc459f31981ffb2c16432eab77',
}
FACTORIES = (
    'arithmetic_multiplicative', 'coprime_divisor_decomposition', 'divisor_pair_index',
    'signed_block_sum', 'signed_cartesian_product', 'signed_support_reindex',
    'dirichlet_multiplicative_entry', 'dirichlet_multiplicative_support',
    'dirichlet_multiplicative',
)
NAMES = (
    'dirichlet_coprime_grid_nonzero_coordinates',
    'dirichlet_coprime_grid_support_preserving',
    'dirichlet_coprime_grid_support_injective',
    'dirichlet_coprime_grid_support_covering',
    'dirichlet_coprime_grid_support_reindex',
    'dirichlet_coprime_product_data_construct',
    'dirichlet_convolution_multiplicative_values',
    'dirichlet_convolution_multiplicative_table',
    'dirichlet_convolution_multiplicative_exists_unique',
    'dirichlet_multiplicative_function_invertible',
)
METRICS = ((369,53),(229,53),(294,61),(1085,64),(303,100),(76,38),
           (173,47),(216,51),(48,22),(47,26))
PARAMETERS = ('N','F','G','m','n','A','B','T','Q','r','s')


def conjoin(*clauses):
    result = clauses[-1]
    for clause in reversed(clauses[:-1]):
        result = f'({clause}) /\\ ({result})'
    return result


def expected_lt(a,b,tag):
    gap = 'independent_strict_gap_'+tag
    return f'exists {gap}. {gap}+S ({a})=({b})'


def expected_beta(r,s,i,j,tag):
    gap,quotient = 'independent_beta_gap_'+tag,'independent_beta_quotient_'+tag
    modulus = f'S ((S ({i}))*({s}))'
    return conjoin(f'exists {gap}. {gap}+S ({j})={modulus}',
                   f'exists {quotient}. ({r})={quotient}*{modulus}+({j})')


def expected_coprime(a,b,tag):
    divisor = 'independent_common_divisor_'+tag
    return (f'forall {divisor}. ({expected_dvd(divisor,a,tag+"first")}) -> '
            f'({expected_dvd(divisor,b,tag+"second")}) -> {divisor}=1')


def expected_multiplicative(N,F,tag):
    a,b,x,y,z = ('independent_law_'+role+'_'+tag
                 for role in ('left','right','first','second','product'))
    law = (f'forall {a} {b} {x} {y} {z}. ~({a}=0) -> ~({b}=0) -> '
           f'({expected_le(a+"*"+b,N,tag+"bound")}) -> '
           f'({expected_coprime(a,b,tag+"coprime")}) -> '
           f'({expected_at(F,a,x,tag+"first")}) -> ({expected_at(F,b,y,tag+"second")}) -> '
           f'({expected_at(F,a+"*"+b,z,tag+"product")}) -> '
           f'({expected_signed_multiply(x,y,z,tag+"multiply")})')
    return conjoin(f'~(({N})=0)',expected_table(N,F,tag+'table'),
                   expected_at(F,'1','2',tag+'normalization'),law)


def expected_pair(m,n,k,d,e,tag):
    return conjoin(f'~(({d})=0)',f'~(({e})=0)',expected_dvd(d,m,tag+'first'),
                   expected_dvd(e,n,tag+'second'),f'({k})=({d})*({e})')


def expected_product(F,G,T,m,n,tag):
    i,j,a,b,c = ('independent_cartesian_'+role+'_'+tag
                 for role in ('row','column','left','right','value'))
    law = (f'forall {i} {j} {a} {b} {c}. ({expected_lt(i,m,tag+"row")}) -> '
           f'({expected_lt(j,n,tag+"column")}) -> ({expected_at(F,i,a,tag+"first")}) -> '
           f'({expected_at(G,j,b,tag+"second")}) -> '
           f'({expected_at(T,f"({n})*{i}+{j}",c,tag+"output")}) -> '
           f'({expected_signed_multiply(a,b,c,tag+"multiply")})')
    return conjoin(expected_table('0',F,tag+'F'),expected_table('0',G,tag+'G'),
                   expected_table(f'({m})*({n})',T,tag+'T'),law)


def expected_map(V,L,r,s,tag):
    i,d,e = ('independent_map_'+role+'_'+tag for role in ('index','row','column'))
    return conjoin(f'~(({V})=0)',
        f'forall {i} {d} {e}. ({expected_lt(i,L,tag+"index")}) -> '
        f'({expected_lt(e,V,tag+"column")}) -> {i}=({V})*{d}+{e} -> '
        f'({expected_beta(r,s,i,d+"*"+e,tag+"product")})')


def expected_preserving(A,B,r,s,L,M,tag):
    i,a,j = ('independent_preserve_'+name+'_'+tag for name in ('i','a','j'))
    return (f'forall {i} {a}. ({expected_lt(i,L,tag+"source_bound")}) -> '
        f'({expected_at(A,i,a,tag+"source_value")}) -> ~({a}=0) -> exists {j}. '+
        conjoin(expected_beta(r,s,i,j,tag+'image'),expected_lt(j,M,tag+'image_bound'),
                expected_at(B,j,a,tag+'preserved_value')))


def expected_injective(A,r,s,L,tag):
    i,k,j,a,b = ('independent_injective_'+name+'_'+tag for name in ('i','k','j','a','b'))
    return (f'forall {i} {k} {j} {a} {b}. ({expected_lt(i,L,tag+"first_bound")}) -> '
        f'({expected_lt(k,L,tag+"second_bound")}) -> ({expected_at(A,i,a,tag+"first_value")}) -> ~({a}=0) -> '
        f'({expected_at(A,k,b,tag+"second_value")}) -> ~({b}=0) -> '
        f'({expected_beta(r,s,i,j,tag+"first_map")}) -> '
        f'({expected_beta(r,s,k,j,tag+"second_map")}) -> {i}={k}')


def expected_covering(A,B,r,s,L,M,tag):
    j,b,i = ('independent_cover_'+name+'_'+tag for name in ('j','b','i'))
    return (f'forall {j} {b}. ({expected_lt(j,M,tag+"target_bound")}) -> '
        f'({expected_at(B,j,b,tag+"target_value")}) -> ~({b}=0) -> exists {i}. '+
        conjoin(expected_lt(i,L,tag+'preimage_bound'),expected_beta(r,s,i,j,tag+'preimage_map'),
                expected_at(A,i,b,tag+'preimage_value')))


def expected_reindex(A,B,r,s,L,M,tag):
    return conjoin(expected_table('0',A,tag+'A'),expected_table('0',B,tag+'B'),
        expected_preserving(A,B,r,s,L,M,tag+'preserve'),expected_injective(A,r,s,L,tag+'injective'),
        expected_covering(A,B,r,s,L,M,tag+'cover'))


def expected_data(N,F,G,m,n,A,B,T,Q,r,s,tag):
    return conjoin(
        expected_multiplicative(N,F,tag+'F'),expected_multiplicative(N,G,tag+'G'),
        f'~(({m})=0)',f'~(({n})=0)',expected_le(f'({m})*({n})',N,tag+'bound'),
        expected_coprime(m,n,tag+'coprime'),expected_prefix(F,G,m,m,A,tag+'left'),
        expected_prefix(F,G,n,n,B,tag+'right'),
        expected_product(A,B,T,f'S ({m})',f'S ({n})',tag+'cartesian'),
        expected_prefix(F,G,f'({m})*({n})',f'({m})*({n})',Q,tag+'target'),
        expected_map(f'S ({n})',f'(S ({m}))*(S ({n}))',r,s,tag+'map'))


def expected_grid(F,G,m,n,i,z,d,e,a,b,tag):
    return conjoin(
        f'({i})=(S ({n}))*({d})+({e})',expected_lt(d,f'S ({m})',tag+'row'),
        expected_lt(e,f'S ({n})',tag+'column'),expected_pair(m,n,f'({d})*({e})',d,e,tag+'pair'),
        expected_entry(F,G,m,d,a,tag+'left'),expected_entry(F,G,n,e,b,tag+'right'),
        expected_signed_multiply(a,b,z,tag+'product'))


def format_contract(names,premises,target):
    return 'forall '+names+'. '+' -> '.join('('+part+')' for part in (*premises,target))


def contracts():
    count = 0
    def tagged(function):
        def call(*args):
            nonlocal count
            count += 1
            return function(*args,tag='closure_contract_'+str(count))
        return call
    D,X,L,LT,A,MP,CP,P,C,CT,PE,I,M = map(tagged,(
        expected_data,expected_grid,expected_le,expected_lt,expected_at,expected_multiplicative,
        expected_coprime,expected_prefix,expected_convolution,expected_convolution_table,
        expected_positive_equal,expected_inverse,expected_signed_multiply))
    data = D(*PARAMETERS)
    length = '(S m)*(S n)'
    names = ' '.join(PARAMETERS)
    result = {
        NAMES[0]:(names+' i z',(data,LT('i',length),A('T','i','z'),'~(z=0)'),
                  'exists d e a b. '+X('F','G','m','n','i','z','d','e','a','b')),
        NAMES[1]:(names,(data,),expected_preserving('T','Q','r','s',length,'S (m*n)','preserve')),
        NAMES[2]:(names,(data,),expected_injective('T','r','s',length,'injective')),
        NAMES[3]:(names,(data,),expected_covering('T','Q','r','s',length,'S (m*n)','cover')),
        NAMES[4]:(names,(data,),expected_reindex('T','Q','r','s',length,'S (m*n)','reindex')),
        NAMES[5]:('N F G m n A B Q',(
            MP('N','F'),MP('N','G'),'~(m=0)','~(n=0)',L('m*n','N'),CP('m','n'),
            P('F','G','m','m','A'),P('F','G','n','n','B'),P('F','G','m*n','m*n','Q')),
            'exists T r s. '+D(*PARAMETERS)),
        NAMES[6]:('N F G m n a b c',(
            MP('N','F'),MP('N','G'),'~(m=0)','~(n=0)',L('m*n','N'),CP('m','n'),
            C('F','G','m','a'),C('F','G','n','b'),C('F','G','m*n','c')),M('a','b','c')),
        NAMES[7]:('N F G H',(MP('N','F'),MP('N','G'),CT('N','F','G','H')),MP('N','H')),
        NAMES[8]:('N F G',(MP('N','F'),MP('N','G')),
            'exists H. '+conjoin(CT('N','F','G','H'),MP('N','H'),
                f'forall K. ({CT("N","F","G","K")}) -> ({PE("H","K","N")})')),
        NAMES[9]:('N F w',(MP('N','F'),),'exists G. '+conjoin(I('N','F','G'),A('G','0','w'))),
    }
    assert tuple(result) == NAMES
    return result


def exact_ast(statement):
    return FormulaArena().freeze(_closed_formula(statement)).to_json()


def instantiate(template,replacements,tag):
    bound = tuple(dict.fromkeys(name for clause in re.findall(
        r'\b(?:forall|exists)\s+([^.]*)\.',template) for name in clause.split()))
    renamed = {name:'independent_instance_'+tag+'_'+str(index) for index,name in enumerate(bound)}
    pattern = r"\b[A-Za-z_][A-Za-z_0-9']*"
    template = re.sub(pattern,lambda match:renamed.get(match.group(),match.group()),template)
    return re.sub(pattern,lambda match:'('+replacements[match.group()]+')'
                  if match.group() in replacements else match.group(),template)


@lru_cache(maxsize=1)
def rows():
    return (support.make_dirichlet_multiplicative_support_candidate_theorems(TheoremSpec)+
            candidate.make_dirichlet_multiplicative_candidate_theorems(TheoremSpec))


@lru_cache(maxsize=1)
def all_new_rows():
    result = []
    for stem in FACTORIES:
        module = importlib.import_module('peano_lab.library.'+stem+'_candidate')
        result.extend(getattr(module,'make_'+stem+'_candidate_theorems')(TheoremSpec))
    return tuple(result)


@lru_cache(maxsize=1)
def predecessors():
    from peano_lab.library.editions_v31 import ALPHA_CHECKED_SPECS
    assert len(ALPHA_CHECKED_SPECS) == 3796
    return ALPHA_CHECKED_SPECS


@lru_cache(maxsize=1)
def core():
    return {row.name:row for row in (*predecessors(),*all_new_rows())}


def test_source_pins_and_exact_ten_row_inventory():
    for filename,pin in SOURCE_PINS.items():
        module = support if 'support' in filename else candidate
        assert sha256(Path(module.__file__).read_bytes()).hexdigest() == pin
    assert tuple(row.name for row in rows()) == NAMES
    assert tuple(len(row.dependencies) for row in rows()) == (5,7,3,12,4,4,5,11,3,1)
    assert len(all_new_rows()) == len({row.name for row in all_new_rows()}) == 90
    assert all(row.script and not any(command.startswith(('use ','admit','sorry','DNE','ring'))
                                     for command in row.script) for row in rows())
    assert all(len(set(row.dependencies)) == len(row.dependencies) for row in rows())
    assert all(re.search(r"(?<![\w'])"+re.escape(name)+r"(?![\w'])",'\n'.join(row.script))
               for row in rows() for name in row.dependencies)


def test_all_ninety_topological_specs_novel_against_all_3796_admitted_rows():
    available = {row.name for row in predecessors()}
    encoded = {}
    for row in all_new_rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        representation = exact_ast(row.statement)
        key = sha256(representation.encode()).digest()
        assert all(representation != previous for previous in encoded.get(key,())),row.name
        encoded.setdefault(key,[]).append(representation)
        available.add(row.name)
    for row in predecessors():
        representation = exact_ast(row.statement)
        assert all(representation != previous for previous in encoded.get(
            sha256(representation.encode()).digest(),())),row.name
    assert len(available) == 3886


def test_actual_current_parent_adapter_preserves_the_exact_whole_cone():
    import constructive_g009_support as adapter
    from peano_lab.library import campaign_completed_lower_closure as promoted
    state = adapter.load_candidate_state()
    assert state.rows == all_new_rows()
    selection = adapter.select_support(state.rows,tuple(row.name for row in state.rows))
    assert len(selection.owned) == 90 and not selection.current_support
    assert tuple(row.name for row in selection.complete_specs) == tuple(row.name for row in selection.plan.rows)
    assert len(selection.parent_support) == len(selection.complete_specs)-90
    assert set(selection.plan.root_names) <= {row.name for row in state.rows}
    providers = adapter.parent_seed_paths()
    assert len(providers) == len(set(providers)) == 39
    assert all(adapter.ROOT in path.parents for path in providers)
    print({'syntax_only_adapter':True,'new_rows':90,'prior_rows':3796,
           'complete_cone_rows':len(selection.complete_specs),
           'execution_frontier_rows':len(selection.frontier),
           'new_specs_sha256':state.specs_sha256,
           'actual_inherited_providers':len(providers),
           'maximal_roots':selection.plan.root_names},flush=True)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_independently_expanded_complete_statement(row):
    assert exact_ast(row.statement) == exact_ast(format_contract(*contracts()[row.name]))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
@pytest.mark.parametrize('mode',('compound','zero','repeat','large'))
def test_full_contract_compound_instances_keep_all_boundaries(row,mode):
    names = contracts()[row.name][0].split()
    replacements = {name:'ambient_left+ambient_right' if index%2 else 'ambient_left*ambient_right'
                    for index,name in enumerate(names)}
    if mode == 'zero': replacements = dict.fromkeys(names,'0')
    if mode == 'repeat': replacements = dict.fromkeys(names,'ambient_left')
    if mode == 'large': replacements = dict.fromkeys(names,'79228162514264337593543950335')
    close = 'forall ambient_left ambient_right unused. '
    actual = instantiate(row.statement.split('.',1)[1],replacements,'actual')
    expected = instantiate(format_contract(*contracts()[row.name]).split('.',1)[1],replacements,'expected')
    assert exact_ast(close+actual) == exact_ast(close+expected)


GRAPH_BUILDERS = (
    (support.dirichlet_coprime_product_data_relation,PARAMETERS,expected_data),
    (support.dirichlet_divisor_grid_witness_relation,('F','G','m','n','i','z','d','e','a','b'),expected_grid),
)


@pytest.mark.parametrize('builder,arguments,expected',GRAPH_BUILDERS)
@pytest.mark.parametrize('mode',('ordinary','compound','repeat','zero','large'))
def test_public_definition_graphs_are_exact_conservative_expansions(builder,arguments,expected,mode):
    context = (*arguments,'ambient_left','ambient_right','unused')
    terms = arguments
    if mode == 'compound':
        terms = tuple('ambient_left+ambient_right' if index%2 else 'ambient_left*ambient_right'
                      for index in range(len(arguments)))
    if mode == 'repeat': terms = ('ambient_left',)*len(arguments)
    if mode == 'zero': terms = ('0',)*len(arguments)
    if mode == 'large': terms = ('79228162514264337593543950335',)*len(arguments)
    close = 'forall '+' '.join(context)+'. '
    actual = builder(*terms,tag='public_hygienic',variables=context)
    assert exact_ast(close+actual) == exact_ast(close+expected(*terms,'independent_public'))


@pytest.mark.parametrize('builder,arguments,expected',GRAPH_BUILDERS)
def test_all_generated_binders_reject_even_unused_context_capture(builder,arguments,expected):
    text = builder(*arguments,tag='capture_probe',variables=arguments)
    bound = {name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',text)
             for name in clause.split()}
    assert bound and not set(arguments)&bound
    for name in sorted(bound):
        with pytest.raises((TypeError,ValueError)):
            builder(*arguments,tag='capture_probe',variables=(*arguments,name))


@pytest.mark.parametrize('builder,arguments,expected',GRAPH_BUILDERS)
@pytest.mark.parametrize('mode',('duplicate','missing','list_context','bad_tag','unbound','formula_term'))
def test_invalid_definition_contexts_fail_closed(builder,arguments,expected,mode):
    context,tag,terms = arguments,'invalid_probe',arguments
    if mode == 'duplicate': context = (*arguments,arguments[0])
    if mode == 'missing': context = arguments[1:]
    if mode == 'list_context': context = list(arguments)
    if mode == 'bad_tag': tag = 'bad-tag'
    if mode == 'unbound': terms = ('unbound_external',*arguments[1:])
    if mode == 'formula_term': terms = ('0=0',*arguments[1:])
    with pytest.raises((TypeError,ValueError)):
        builder(*terms,tag=tag,variables=context)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_ha_body_exact_nodes_and_depth(row):
    try:
        receipt = replay_candidate_bodies((row,),core=core())[0]
        nodes,depth = METRICS[rows().index(row)]
        assert (receipt.proof_nodes,receipt.proof_depth) == (nodes,depth)
        assert 0 < receipt.proof_objects <= nodes
    except CandidateBodyError as error:
        pytest.fail(str(error)[:700],pytrace=False)
    finally:
        gc.collect()


def rejected(row,table):
    gc.collect()
    try:
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,),core=table)
    finally:
        gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
@pytest.mark.parametrize('mutation',('false','empty'))
def test_false_or_absent_body_rejected(row,mutation):
    altered = replace(row,statement='0=1') if mutation == 'false' else replace(row,script=())
    rejected(altered,core())


EDGES = tuple((row,name) for row in rows() for name in row.dependencies)


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
@pytest.mark.parametrize('mutation',('drop','poison'))
def test_every_dependency_edge_required_by_original_body(row,dependency,mutation):
    table = dict(core())
    if mutation == 'drop':
        row = replace(row,dependencies=tuple(name for name in row.dependencies if name != dependency))
    else:
        table[dependency] = replace(table[dependency],statement='0=1')
    rejected(row,table)


def hostile_contracts():
    values = contracts()
    result = []
    name = NAMES[6]
    names,premises,target = values[name]
    for label,index in (('missing_left_multiplicativity',0),('missing_right_multiplicativity',1),
                        ('missing_product_bound',4),('missing_coprimality',5)):
        result.append((label,name,format_contract(names,(*premises[:index],*premises[index+1:]),target)))
    result.append(('natural_code_product_is_not_signed_product',name,
                   format_contract(names,premises,'c=a*b')))
    name = NAMES[8]
    names,premises,target = values[name]
    wrong_unique = 'exists H. '+conjoin(
        expected_convolution_table('N','F','G','H','bad_exists'),
        expected_multiplicative('N','H','bad_multiplicative'),
        f'forall K. ({expected_convolution_table("N","F","G","K","bad_other")}) -> H=K')
    result.append(('table_code_uniqueness_is_not_positive_extensionality',name,
                   format_contract(names,premises,wrong_unique)))
    name = NAMES[0]
    names,premises,target = values[name]
    result.append(('zero_slots_need_not_be_divisor_pairs',name,
                   format_contract(names,premises[:-1],target)))
    name = NAMES[9]
    names,premises,target = values[name]
    wrong_inverse = 'exists G. '+conjoin(
        expected_inverse('N','F','G','bad_inverse'),
        expected_at('G','0','w','bad_zero'), 'G=F')
    result.append(('a_multiplicative_function_is_not_generally_its_own_inverse',name,
                   format_contract(names,premises,wrong_inverse)))
    return tuple(result)


@pytest.mark.parametrize('label,name,statement',hostile_contracts(),
                         ids=[case[0] for case in hostile_contracts()])
def test_substantively_stronger_or_changed_claim_is_not_proved(label,name,statement):
    row = next(row for row in rows() if row.name == name)
    rejected(replace(row,statement=statement),core())


def actual_value(table,index):
    code,(pb,pc,nb,nc) = table
    positive,negative = _unpair(code)
    assert _unpair(positive) == (pb,pc) and _unpair(negative) == (nb,nc)
    return decode_signed(model_at(table,index))


def model_multiplicative(N,table):
    return (N > 0 and model_at(table,1) == encode_signed(1) and
            all(actual_value(table,a*b) == actual_value(table,a)*actual_value(table,b)
                for a in range(1,N+1) for b in range(1,N+1)
                if a*b <= N and math.gcd(a,b) == 1))


def arithmetic_value(kind,n):
    if kind == 'one': return 1
    if kind == 'identity': return n
    if kind == 'delta': return int(n == 1)
    if kind == 'character3': return 0 if n%3 == 0 else (1 if n%3 == 1 else -1)
    raise AssertionError(kind)


def convolution_mask(F,G,n):
    return tuple(0 if d == 0 or n%d else actual_value(F,d)*actual_value(G,n//d)
                 for d in range(n+1))


@pytest.mark.parametrize('m,n',((1,1),(1,4),(2,3),(3,4),(4,5)))
@pytest.mark.parametrize('first,second',(
    ('one','one'),('identity','one'),('character3','identity'),('delta','character3')))
def test_actual_beta_divisor_product_support_and_full_signed_closure(m,n,first,second):
    N = m*n
    F = model_table((-23,*(arithmetic_value(first,i) for i in range(1,N+1))),offset=3,endpoint=97)
    G = model_table((17,*(arithmetic_value(second,i) for i in range(1,N+1))),offset=7,endpoint=-89)
    assert model_multiplicative(N,F) and model_multiplicative(N,G)
    left,right,target = (convolution_mask(F,G,k) for k in (m,n,N))
    A,B,Q = (model_table(values,offset=offset,endpoint=73)
             for values,offset in ((left,5),(right,11),(target,13)))
    grid = tuple(a*b for a in left for b in right)
    T = model_table(grid,offset=17,endpoint=-101)
    L,M = (m+1)*(n+1),N+1
    map_values = tuple(d*e for d in range(m+1) for e in range(n+1))
    r,s = _encode_beta(map_values)
    images = tuple(r%(1+(i+1)*s) for i in range(L))
    assert images == map_values and L != M
    active = tuple(i for i in range(L) if actual_value(T,i) != 0)
    for i in active:
        d,e = divmod(i,n+1)
        assert d > 0 and e > 0 and m%d == n%e == 0
        j = images[i]
        assert j < M and actual_value(T,i) == actual_value(Q,j)
        assert actual_value(T,i) == actual_value(A,d)*actual_value(B,e)
    assert len({images[i] for i in active}) == len(active)
    assert all(any(images[i] == j and actual_value(T,i) == actual_value(Q,j) for i in active)
               for j in range(M) if actual_value(Q,j) != 0)
    assert len(set(images)) < len(images)  # inactive slots really do collide
    for table,length in ((A,m+1),(B,n+1),(T,L),(Q,M)):
        assert decode_signed(actual_sum_trace(table,length)) == sum(actual_value(table,i) for i in range(length))
    assert sum(grid) == sum(left)*sum(right) == sum(target)
    values = tuple(sum(convolution_mask(F,G,k)) for k in range(1,N+1))
    H = model_table((31,*values),offset=19,endpoint=103)
    K = model_table((-37,*values),offset=23,endpoint=-107)
    assert H[0] != K[0] and model_at(H,0) != model_at(K,0)
    assert model_at(H,N+1) != model_at(K,N+1)
    assert all(model_at(H,i) == model_at(K,i) for i in range(1,N+1))
    assert model_multiplicative(N,H) and model_multiplicative(N,K)


def test_support_only_coprimality_and_signed_values_are_substantive():
    # Without coprimality the two positive pairs (1,2) and (2,1) collide,
    # and convolution of the constant-one function is not completely multiplicative.
    F = model_table((13,1,1,1,1),offset=3,endpoint=0)
    H = tuple(sum(convolution_mask(F,F,k)) for k in range(1,5))
    assert H == (1,2,2,3) and H[1]**2 != H[3]
    assert 1*2 == 2*1 and (1,2) != (2,1)
    assert encode_signed(-1)*encode_signed(2) != encode_signed(-2)
    assert model_multiplicative(4,F) and not model_multiplicative(0,F)
    minus_delta = model_table((13,-1,0,0,0),offset=7,endpoint=0)
    assert model_at(minus_delta,1) == 1 and not model_multiplicative(1,minus_delta)


def test_inclusive_product_bound_cannot_be_replaced_by_two_factor_bounds():
    # F is multiplicative through five, but its value at six is deliberately wrong.
    F = model_table((13,1,2,3,4,5,19),offset=7,endpoint=0)
    G = model_table((-17,1,0,0,0,0,0),offset=5,endpoint=0)
    assert model_multiplicative(5,F) and model_multiplicative(5,G)
    assert 2 <= 5 and 3 <= 5 and math.gcd(2,3) == 1
    left,right,total = (sum(convolution_mask(F,G,k)) for k in (2,3,6))
    assert left*right == 6 and total == 19


def test_constructive_data_contract_contains_no_assumed_reindex_or_sum():
    names,premises,target = contracts()[NAMES[5]]
    expected = format_contract(names,premises,target)
    assert exact_ast(next(row for row in rows() if row.name == NAMES[5]).statement) == exact_ast(expected)
    assert len(premises) == 9 and target.startswith('exists T r s.')
    # The only logical input graphs are two normalized functions and three
    # actual summand prefixes, plus positivity/bound/coprimality. The produced
    # table and map cannot already be present as hidden input quantifiers.
    assert names.split() == ['N','F','G','m','n','A','B','Q']
