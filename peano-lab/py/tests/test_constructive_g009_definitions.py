"""Independent conservative-notation checks, without Alpha or proof replay.

Only eleven new definition templates and the 372 inherited definition
records are inspected. No 3796-row theorem catalogue, candidate proof,
proof bundle, Lean process, or successful saved receipt is loaded.
"""

import ast
from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
from pathlib import Path
import re
import sys

import pytest

# Observe this module's own imports and operations, not other CI modules.
_WATCHED_MODULE_ROOTS = ('peano_lab.library.editions_v31',
                         'constructive_g009_checkpoints','check_constructive_g009')


def _tracked_module_identities(modules=None):
    modules = sys.modules if modules is None else modules
    return {name:module for name,module in modules.items()
            if any(name == root or name.startswith(root+'.') for root in _WATCHED_MODULE_ROOTS)}


def _assert_tracked_modules_unchanged(before,modules=None):
    after = _tracked_module_identities(modules)
    assert after.keys() == before.keys(), 'authority module inventory changed'
    assert all(after[name] is module for name,module in before.items()), 'authority module identity changed'


@pytest.fixture(autouse=True)
def _authority_module_baseline():
    before = _tracked_module_identities()
    yield before
    _assert_tracked_modules_unchanged(before)


_PROJECT_IMPORT_MODULES_BEFORE = _tracked_module_identities()

import constructive_g009_definitions as definitions
import constructive_g009_definition_graph as graph
import constructive_dirichlet_inverse_definition_graph as previous_graph
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.kernel.terms import ParseError
from peano_lab.library.formula_dag import FormulaArena


PRIOR = definitions.HISTORICAL_DEFINITIONS_BY_NAME
ALL = definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
NEW = definitions.G009_DEFINITIONS

EXPECTED = (
    ('MultiplicativePrefix',('N','F'),definitions.multiplicative.signed_multiplicative_prefix_relation,
     ('ArithTable','ArithAt','Le','Coprime','SignedMul')),
    ('DivisorFactorPair',('m','n','d','a','b'),definitions.pairs.divisor_factor_pair_relation,('Dvd',)),
    ('DivisorPairIndexMap',('V','L','r','s'),definitions.index_map.divisor_pair_index_map_relation,('Lt','BetaAt')),
    ('SignedCartesianProduct',('F','G','T','m','n'),definitions.cartesian.signed_cartesian_product_relation,
     ('ArithTable','Lt','ArithAt','SignedMul')),
    ('SignedSupportReindex',('A','B','r','s','L','M'),definitions.support_reindex.signed_support_reindex_relation,
     ('ArithTable','Lt','ArithAt','BetaAt')),
    ('SignedIncidenceEntry',('A','r','s','i','j','z'),definitions.support_reindex.signed_support_incidence_entry_relation,
     ('ArithAt','BetaAt')),
    ('SignedIncidenceFlatEntry',('A','r','s','M','k','z'),definitions.support_reindex.signed_support_incidence_flat_entry_relation,
     ('Lt','SignedIncidenceEntry')),
    ('SignedIncidenceFlatPrefix',('A','r','s','M','l','T'),definitions.support_reindex.signed_support_incidence_flat_prefix_relation,
     ('ArithTable','Le','ArithAt','SignedIncidenceFlatEntry')),
    ('SignedSupportIncidence',('A','r','s','L','M','T'),definitions.support_reindex.signed_support_incidence_relation,
     ('ArithTable','Lt','ArithAt','SignedIncidenceEntry')),
    ('DirichletCoprimeProductData',('N','F','G','m','n','A','B','T','Q','r','s'),
     definitions.product_data.dirichlet_coprime_product_data_relation,
     ('MultiplicativePrefix','Le','Coprime','DirichletPrefix','SignedCartesianProduct','DivisorPairIndexMap')),
    ('DirichletDivisorGridWitness',('F','G','m','n','i','z','d','e','a','b'),
     definitions.product_data.dirichlet_divisor_grid_witness_relation,
     ('Lt','DivisorFactorPair','DirichletEntry','SignedMul')),
)

MATH_PINS = {
    'arithmetic_multiplicative_candidate':'f4374450ec543f69093b98367c90f67f09ac15daacd1df2f90961d7b6ece4a7e',
    'coprime_divisor_decomposition_candidate':'de19bb61543f5d7ab3a1d1b675c96ae4b31c7c96b58d6107904e7188973a2e1c',
    'divisor_pair_index_candidate':'fc6a5a555fdee62cf5f54365163f32c4acfee10b8f416b811bb69debdbcf62a0',
    'signed_block_sum_candidate':'0597b3806fec32b8eb117f5d0f6be2304c754aa8078df6f50de9dd4d12a2c18f',
    'signed_cartesian_product_candidate':'d7dbe1d9a82ee5b91e33d6a4624d3e7f05b20d4618045ecab8e753eee6c7e351',
    'signed_support_reindex_candidate':'db91e38ca5e671adf88e3bf70396b1a242f9c760d6f2c52c4785e6a63316339e',
    'dirichlet_multiplicative_entry_candidate':'d7f55b8f25e56f8b9c5bc3f6c4b83698d5f1ad770e1e4ed77c53f12a602bd897',
    'dirichlet_multiplicative_support_candidate':'56e9f8ccaa7c795e42b33984bc2346182ba3a1f820883ba884e571b89091d4a5',
    'dirichlet_multiplicative_candidate':'bb1342735115781fd8f0107d3876c95098e0b6dc459f31981ffb2c16432eab77',
}


def _same_ast(first,second):
    pending,seen = [(first,second)],set()
    while pending:
        a,b = pending.pop()
        assert type(a) is type(b)
        key = id(a),id(b)
        if key in seen:
            continue
        seen.add(key)
        if is_dataclass(a):
            pending.extend((getattr(a,field.name),getattr(b,field.name)) for field in fields(a))
        else:
            assert a == b


def _and(*formulas):
    return formulas[0] if len(formulas) == 1 else f'(({formulas[0]}) /\\ ({_and(*formulas[1:])}))'


def _call(name,*arguments):
    return name+'('+','.join(arguments)+')'


def _independent(name,arguments,context=()):
    """Write each new graph only in frozen, lower-level named vocabulary."""
    used = set(context)
    used.update(re.findall(r'[A-Za-z_][A-Za-z0-9_]*',' '.join(arguments)))
    counter = 0

    def fresh(count):
        nonlocal counter
        values = []
        while len(values) < count:
            value = 'independent_g009_'+str(counter)
            counter += 1
            if value not in used:
                used.add(value)
                values.append(value)
        return tuple(values)

    def expand(current,args):
        if current == 'MultiplicativePrefix':
            N,F = args
            a,b,x,y,z = fresh(5)
            law = (f'forall {a} {b} {x} {y} {z}. ~({a}=0) -> ~({b}=0) -> '
                   f'Le({a}*{b},{N}) -> Coprime({a},{b}) -> ArithAt({F},{a},{x}) -> '
                   f'ArithAt({F},{b},{y}) -> ArithAt({F},{a}*{b},{z}) -> SignedMul({x},{y},{z})')
            return _and(f'~(({N})=0)',f'ArithTable({N},{F})',f'ArithAt({F},1,2)',law)
        if current == 'DivisorFactorPair':
            m,n,d,a,b = args
            return _and(f'~(({a})=0)',f'~(({b})=0)',f'Dvd({a},{m})',f'Dvd({b},{n})',f'({d})=({a})*({b})')
        if current == 'DivisorPairIndexMap':
            V,L,r,s = args
            i,d,e = fresh(3)
            return _and(f'~(({V})=0)',f'forall {i} {d} {e}. Lt({i},{L}) -> Lt({e},{V}) -> '
                        f'{i}=({V})*{d}+{e} -> BetaAt({r},{s},{i},{d}*{e})')
        if current == 'SignedCartesianProduct':
            F,G,T,m,n = args
            i,j,a,b,c = fresh(5)
            law = (f'forall {i} {j} {a} {b} {c}. Lt({i},{m}) -> Lt({j},{n}) -> '
                   f'ArithAt({F},{i},{a}) -> ArithAt({G},{j},{b}) -> '
                   f'ArithAt({T},({n})*{i}+{j},{c}) -> SignedMul({a},{b},{c})')
            return _and(f'ArithTable(0,{F})',f'ArithTable(0,{G})',f'ArithTable(({m})*({n}),{T})',law)
        if current == 'SignedSupportReindex':
            A,B,r,s,L,M = args
            i,a,j = fresh(3)
            preserve = (f'forall {i} {a}. Lt({i},{L}) -> ArithAt({A},{i},{a}) -> ~({a}=0) -> exists {j}. '
                        +_and(f'BetaAt({r},{s},{i},{j})',f'Lt({j},{M})',f'ArithAt({B},{j},{a})'))
            i,k,j,a,b = fresh(5)
            injective = (f'forall {i} {k} {j} {a} {b}. Lt({i},{L}) -> Lt({k},{L}) -> '
                         f'ArithAt({A},{i},{a}) -> ~({a}=0) -> ArithAt({A},{k},{b}) -> ~({b}=0) -> '
                         f'BetaAt({r},{s},{i},{j}) -> BetaAt({r},{s},{k},{j}) -> {i}={k}')
            j,b,i = fresh(3)
            cover = (f'forall {j} {b}. Lt({j},{M}) -> ArithAt({B},{j},{b}) -> ~({b}=0) -> exists {i}. '
                     +_and(f'Lt({i},{L})',f'BetaAt({r},{s},{i},{j})',f'ArithAt({A},{i},{b})'))
            return _and(f'ArithTable(0,{A})',f'ArithTable(0,{B})',preserve,injective,cover)
        if current == 'SignedIncidenceEntry':
            A,r,s,i,j,z = args
            a,k = fresh(2)
            choice = f'({_and(f"({j})={k}",f"({z})={a}")}) \\/ ({_and(f"~(({j})={k})",f"({z})=0")})'
            return f'exists {a} {k}. '+_and(f'ArithAt({A},{i},{a})',f'BetaAt({r},{s},{i},{k})',choice)
        if current == 'SignedIncidenceFlatEntry':
            A,r,s,M,k,z = args
            i,j = fresh(2)
            return f'exists {i} {j}. '+_and(f'({k})=(S ({M}))*{i}+{j}',f'Lt({j},S ({M}))',
                    expand('SignedIncidenceEntry',(A,r,s,i,j,z)))
        if current == 'SignedIncidenceFlatPrefix':
            A,r,s,M,l,T = args
            k,z = fresh(2)
            return _and(f'ArithTable({l},{T})',f'forall {k} {z}. Le({k},{l}) -> ArithAt({T},{k},{z}) -> '
                        f'({expand("SignedIncidenceFlatEntry",(A,r,s,M,k,z))})')
        if current == 'SignedSupportIncidence':
            A,r,s,L,M,T = args
            i,j,z = fresh(3)
            entries = (f'forall {i} {j} {z}. Lt({i},{L}) -> Lt({j},{M}) -> '
                       f'ArithAt({T},(S ({M}))*{i}+{j},{z}) -> '
                       f'({expand("SignedIncidenceEntry",(A,r,s,i,j,z))})')
            return _and(f'ArithTable(0,{A})',f'ArithTable(({L})*(S ({M})),{T})',entries)
        if current == 'DirichletCoprimeProductData':
            N,F,G,m,n,A,B,T,Q,r,s = args
            return _and(expand('MultiplicativePrefix',(N,F)),expand('MultiplicativePrefix',(N,G)),
                f'~(({m})=0)',f'~(({n})=0)',f'Le(({m})*({n}),{N})',f'Coprime({m},{n})',
                f'DirichletPrefix({F},{G},{m},{m},{A})',f'DirichletPrefix({F},{G},{n},{n},{B})',
                expand('SignedCartesianProduct',(A,B,T,f'S ({m})',f'S ({n})')),
                f'DirichletPrefix({F},{G},({m})*({n}),({m})*({n}),{Q})',
                expand('DivisorPairIndexMap',(f'S ({n})',f'(S ({m}))*(S ({n}))',r,s)))
        if current == 'DirichletDivisorGridWitness':
            F,G,m,n,i,z,d,e,a,b = args
            return _and(f'({i})=(S ({n}))*({d})+({e})',f'Lt({d},S ({m}))',f'Lt({e},S ({n}))',
                expand('DivisorFactorPair',(m,n,f'({d})*({e})',d,e)),
                f'DirichletEntry({F},{G},{m},{d},{a})',f'DirichletEntry({F},{G},{n},{e},{b})',
                f'SignedMul({a},{b},{z})')
        raise AssertionError('unreviewed independent graph '+current)

    return expand(name,arguments)


def _parse(source,registry,context=()):
    parser = _LocalDefinedParser(source,registry)
    parser.free = list(context)
    formula = parser.parse()
    assert tuple(parser.free) == tuple(context)
    return formula


def _binders(source):
    return {name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}


def test_all_372_parent_objects_and_dag_records_remain_unchanged():
    old,_,_ = previous_graph.reviewed_registry()
    current,order,layers = graph.reviewed_registry()
    assert len(PRIOR) == len(old) == 372
    assert all(ALL[name] is item for name,item in PRIOR.items())
    assert all(current[name] == record for name,record in old.items())
    assert len(ALL) == len(current) == len({item.stable_id for item in ALL.values()}) == 383
    assert tuple(item.stable_id for item in NEW) == tuple(f'ND{i:04d}' for i in range(316,327))
    assert max(int(item.stable_id[2:]) for item in PRIOR.values() if item.stable_id.startswith('ND')) == 315
    assert sum(len(item['dependencies']) for item in old.values()) == 787
    assert sum(len(item['dependencies']) for item in current.values()) == 825
    seen = set()
    for name in order:
        assert set(current[name]['dependencies']) <= seen
        assert layers[name] == max((layers[dependency]+1 for dependency in current[name]['dependencies']),default=0)
        seen.add(name)


def test_single_family_registry_and_all_eleven_public_graphs_without_factory_calls():
    assert definitions.G009_REGISTRIES == (('multiplicative-convolution',NEW),)
    assert graph.DEFAULT_REGISTRIES == previous_graph.DEFAULT_REGISTRIES+definitions.G009_REGISTRIES
    assert tuple(item.name for item in NEW) == tuple(item[0] for item in EXPECTED)
    functions = set()
    for name,pin in MATH_PINS.items():
        source = definitions.MATH_DIRECTORY/(name+'.py')
        raw = source.read_bytes()
        assert sha256(raw).hexdigest() == pin
        tree = ast.parse(raw)
        functions.update((name,node.name) for node in tree.body
                         if isinstance(node,ast.FunctionDef) and node.name.endswith('_relation') and not node.name.startswith('_'))
    assert functions == {(builder.__module__.rsplit('.',1)[1],builder.__name__) for _,_,builder,_ in EXPECTED}
    with pytest.raises(TypeError):
        ALL['Fake'] = NEW[0]


def test_actual_definition_ast_novelty_and_low_level_identity_reuse():
    prior = {}
    for item in PRIOR.values():
        prior.setdefault(item.arity,set()).add(FormulaArena().freeze(item.template_formula).to_json())
    for item in NEW:
        encoded = FormulaArena().freeze(item.template_formula).to_json()
        assert encoded not in prior.get(item.arity,set()), item.name
        prior.setdefault(item.arity,set()).add(encoded)
    for name in ('SignedMul','SignedAdd','ArithTable','ArithAt','SignedPrefixSum','BetaAt','DirichletPrefix',
                 'DirichletEntry','DirichletTable','SignedRectangularSum','ArithSlice'):
        assert ALL[name] is PRIOR[name]


@pytest.mark.parametrize('name,parameters,builder,dependencies',EXPECTED,ids=[item[0] for item in EXPECTED])
def test_exact_public_alignment_and_independent_frozen_vocabulary(name,parameters,builder,dependencies):
    item = ALL[name]
    assert item.parameters == parameters and item.conceptual_dependencies == dependencies
    expected = parse_formula_in_context(builder(*parameters,tag='independent_public',variables=parameters),list(parameters))
    _same_ast(expected,_parse(_independent(name,parameters,parameters),PRIOR,parameters))
    _same_ast(expected,item.template_formula)
    _same_ast(expected,_parse(_call(name,*parameters),ALL,parameters))


@pytest.mark.parametrize('name,parameters,builder,dependencies',EXPECTED,ids=[item[0] for item in EXPECTED])
@pytest.mark.parametrize('kind',('compound','large','zero','repeated','reversed'))
def test_nested_and_whole_context_roundtrips(name,parameters,builder,dependencies,kind):
    options = {'compound':('S (x+y)','x*y','x+y'), 'large':(str(2**96+17),'x+y','y'),
               'zero':('0',), 'repeated':('x+y',), 'reversed':('y','x')}[kind]
    arguments = tuple(options[i%len(options)] for i in range(len(parameters)))
    context = ('unused_outer','x','unused_middle','y','unused_last')
    actual = parse_formula_in_context(builder(*arguments,tag='compound_public',variables=context),list(context))
    _same_ast(actual,_parse(_call(name,*arguments),ALL,context))
    _same_ast(actual,_parse(_independent(name,arguments,context),PRIOR,context))
    bound_context = f'forall unused_outer. forall x. exists y. ({builder(*arguments,tag="bound_public",variables=context)})'
    _same_ast(parse_formula_in_context(bound_context,[]),
              _parse('forall unused_outer. forall x. exists y. '+_call(name,*arguments),ALL))


@pytest.mark.parametrize('name,parameters,builder,dependencies',EXPECTED,ids=[item[0] for item in EXPECTED])
def test_every_generated_public_binder_rejected_even_if_unused_in_arguments(name,parameters,builder,dependencies):
    source = builder(*parameters,tag='capture_audit',variables=parameters)
    binders = _binders(source)
    assert binders and not binders.intersection(parameters)
    for binder in sorted(binders):
        with pytest.raises(ValueError,match='captures a context variable'):
            builder(*parameters,tag='capture_audit',variables=(*parameters,binder))
    # The entire surrounding context, not just argument free names, is guarded.
    with pytest.raises(ValueError,match='captures a context variable'):
        builder(*parameters,tag='capture_audit',variables=(*parameters,*sorted(binders)))


@pytest.mark.parametrize('item',NEW,ids=lambda item:item.name)
def test_named_template_instantiation_avoids_early_middle_and_late_binder_capture(item):
    binders = sorted(_binders(item.template_source))
    assert binders
    for binder in dict.fromkeys((binders[0],binders[len(binders)//2],binders[-1])):
        arguments = (binder,)*item.arity
        context = ('unused',binder,'other_unused')
        _same_ast(_parse(_call(item.name,*arguments),ALL,context),
                  _parse(_independent(item.name,arguments,context),PRIOR,context))


@pytest.mark.parametrize('item',NEW,ids=lambda item:item.name)
def test_each_declared_expansion_edge_occurs_in_the_actual_formula(item):
    closure = definitions.definition_closure(item.conceptual_dependencies)
    compact = _FormulaCompactor(closure).compact(item.template_source)
    assert compact['exact_ast_equivalence'] is True
    assert item.stable_id not in compact['statement_definition_uses']
    for dependency in item.conceptual_dependencies:
        child = ALL[dependency]
        isolated = _FormulaCompactor((child,)).compact(item.template_source)
        assert child.stable_id in isolated['statement_definition_uses'],(item.name,dependency)
    if item.name == 'DirichletCoprimeProductData':
        assert not {'SignedSupportReindex','SignedPrefixSum','DirichletSum'} & set(item.conceptual_dependencies)
    if item.name == 'MultiplicativePrefix':
        assert 'SignedUnit' not in item.conceptual_dependencies
        assert not _FormulaCompactor((ALL['SignedUnit'],)).compact(item.template_source)['statement_definition_uses']


@pytest.mark.parametrize('item',NEW,ids=lambda item:item.name)
def test_each_template_compacts_and_expands_exactly(item):
    compact = _FormulaCompactor(NEW).compact(item.template_source)
    assert compact['exact_ast_equivalence'] is True
    assert item.stable_id in compact['statement_definition_uses']
    _same_ast(_parse(compact['defined_statement'],ALL,tuple(compact['free_names'])),
              parse_formula_in_context(item.template_source,list(compact['free_names'])))


@pytest.mark.parametrize('item',NEW,ids=lambda item:item.name)
@pytest.mark.parametrize('difference',(-1,1))
def test_wrong_arities_reject_without_guessing(item,difference):
    with pytest.raises(ParseError,match='expects'):
        _LocalDefinedParser(_call(item.name,*(('x',)*(item.arity+difference))),ALL).parse()


@pytest.mark.parametrize('names',(None,True,'ArithTable',['ArithTable'],('',),(True,)))
def test_invalid_closure_input_is_not_silently_coerced(names):
    with pytest.raises(ValueError,match='exact tuple'):
        definitions.definition_closure(names)


@pytest.mark.parametrize('names',(('Absent',),('MultiplicativePrefix','not_reviewed')))
def test_unknown_closure_input_fails_closed(names):
    with pytest.raises(ValueError,match='unknown or cyclic'):
        definitions.definition_closure(names)


def test_closure_is_actual_acyclic_prerequisites_not_proof_oracles():
    assert definitions.definition_closure(()) == ()
    selected = definitions.definition_closure(('DirichletCoprimeProductData','DirichletCoprimeProductData'))
    names = tuple(item.name for item in selected)
    assert len(names) == len(set(names))
    assert {'DirichletPrefix','MultiplicativePrefix','SignedCartesianProduct','DivisorPairIndexMap'} <= set(names)
    assert not {'SignedSupportReindex','SignedPrefixSum','DirichletSum','DirichletInverse','SignedUnit'} & set(names)
    seen = set()
    for item in selected:
        assert set(item.conceptual_dependencies) <= seen
        seen.add(item.name)


def _with_replacements(replacements):
    return tuple((route,tuple(replacements.get(item.name,item) for item in items))
                 for route,items in graph.DEFAULT_REGISTRIES)


@pytest.mark.parametrize('attack',('duplicate_id','duplicate_name','wrong_template','wrong_formula',
                                  'missing_dependency','self_cycle','two_cycle','bad_route'))
def test_malformed_identity_expansion_or_dag_is_rejected(attack):
    item = NEW[0]
    if attack == 'duplicate_id':
        registries = _with_replacements({item.name:replace(item,stable_id=PRIOR['ArithTable'].stable_id)})
    elif attack == 'duplicate_name':
        registries = _with_replacements({item.name:replace(item,name='ArithTable')})
    elif attack == 'wrong_template':
        registries = _with_replacements({item.name:replace(item,template_source='0=1')})
    elif attack == 'wrong_formula':
        registries = _with_replacements({item.name:replace(item,template_formula=parse_formula_in_context('0=1',[]))})
    elif attack == 'missing_dependency':
        registries = _with_replacements({item.name:replace(item,conceptual_dependencies=('Absent',))})
    elif attack == 'self_cycle':
        registries = _with_replacements({item.name:replace(item,conceptual_dependencies=(item.name,))})
    elif attack == 'two_cycle':
        registries = _with_replacements({item.name:replace(item,conceptual_dependencies=(NEW[1].name,)),
                                        NEW[1].name:replace(NEW[1],conceptual_dependencies=(item.name,))})
    else:
        registries = graph.DEFAULT_REGISTRIES+(('../outside',(item,)),)
    with pytest.raises(graph.DefinitionGraphError):
        graph.reviewed_registry(registries)


def test_hostile_selection_cycle_rejected_without_changing_old_registry(monkeypatch):
    item = NEW[-2]
    changed = dict(ALL)
    changed[item.name] = replace(item,conceptual_dependencies=(item.name,))
    monkeypatch.setattr(definitions,'ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME',changed)
    with pytest.raises(ValueError,match='unknown or cyclic'):
        definitions.definition_closure((item.name,))


def _small_campaign(prefix_parameters=('N','F')):
    convergent = PRIOR['Convergent']
    return {'schema':'constructive-grand-campaign-v1','definitions':{
        'Convergent':{'parameters':list(convergent.parameters),'meaning':convergent.summary,
                     'expansion':convergent.template_source,'reviewed_definition_id':convergent.stable_id},
        'Multiplicative':{'parameters':['f'],'meaning':'Planning arithmetic-function notation.',
                          'expansion':'The planning function satisfies its coprime product law.'},
        'MultiplicativePrefix':{'parameters':list(prefix_parameters),'meaning':'Finite normalized table notation.',
                                'expansion':'N=N'}},
        'nodes':[{'id':'G009','statement':'Multiplicative(f) and MultiplicativePrefix(N,F)'}]}


def test_one_argument_planning_multiplicative_is_not_an_alias_for_finite_prefix():
    assert graph.REVIEWED_BLUEPRINT_ALIASES is previous_graph.REVIEWED_BLUEPRINT_ALIASES
    assert 'Multiplicative' not in ALL and 'Multiplicative' not in graph.REVIEWED_BLUEPRINT_ALIASES
    data = graph.build_definition_graph(_small_campaign())
    rows = {row['name']:row for row in data['definitions']}
    assert rows['Multiplicative']['reviewed_match'] is None
    assert rows['MultiplicativePrefix']['reviewed_match']['reviewed_id'] == 'ND0316'
    assert rows['MultiplicativePrefix']['reviewed_match']['blueprint_expansion_is_kernel_checked'] is False
    assert data['reviewed_definition_count'] == 383 and data['reviewed_definition_edge_count'] == 825
    assert all(row['authority'] == 'blueprint-vocabulary-only' for row in data['definitions'])
    assert 'never theorem-proof dependencies' in data['authority_policy']['notation_edges']
    assert not {'alpha_eligible','stable_eligible','full_G009_dirichlet_convolution_theory_proved',
                'multiplicative_convolution_principals_checked'} & data.keys()


def test_wrong_finite_planning_arity_never_confers_checked_evidence():
    data = graph.build_definition_graph(_small_campaign(('F',)))
    assert data['incompatible_reviewed_match_count'] == 1
    assert data['incompatible_reviewed_matches'][0]['confers_checked_evidence'] is False


def test_attempted_one_to_two_argument_alias_is_recorded_as_incompatible():
    aliases = {**graph.REVIEWED_BLUEPRINT_ALIASES,'Multiplicative':('MultiplicativePrefix',(0,))}
    data = graph.build_definition_graph(_small_campaign(),aliases=aliases)
    mismatch = data['incompatible_reviewed_matches']
    assert len(mismatch) == 1 and mismatch[0]['blueprint_name'] == 'Multiplicative'
    assert mismatch[0]['reason'] == 'incompatible-arity' and mismatch[0]['confers_checked_evidence'] is False


def test_old_zero_numerator_erratum_guard_is_not_removed():
    campaign = _small_campaign()
    del campaign['definitions']['Convergent']
    with pytest.raises(graph.DefinitionGraphError,match='excludes 0/1'):
        graph.build_definition_graph(campaign)


def test_scope_prose_keeps_positive_normalization_padding_and_support_distinct():
    assert 'canonical code 2' in ALL['MultiplicativePrefix'].summary
    assert 'F(0)' in ALL['MultiplicativePrefix'].summary and 'N>0' in ALL['MultiplicativePrefix'].summary
    assert 'inactive images may collide' in ALL['DivisorPairIndexMap'].summary
    assert 'unused endpoint m*n' in ALL['SignedCartesianProduct'].summary
    assert 'not a whole-window permutation' in ALL['SignedSupportReindex'].summary
    assert 'stride S M' in ALL['SignedSupportIncidence'].summary and 'j=M' in ALL['SignedSupportIncidence'].summary
    assert 'no upper row bound' in ALL['SignedIncidenceFlatEntry'].summary
    assert 'need not be nonzero' in ALL['DirichletDivisorGridWitness'].summary


def test_definition_suite_has_not_imported_current_alpha_or_checkpoint_authority(_authority_module_baseline):
    _assert_tracked_modules_unchanged(_authority_module_baseline)


@pytest.mark.parametrize('module_name',_WATCHED_MODULE_ROOTS)
@pytest.mark.parametrize('initial,mutation',(
    ('absent','unchanged'),('preloaded','unchanged'),('absent','insert'),
    ('absent','insert_none'),('preloaded','remove'),('preloaded','replace'),
    ('preloaded','extra_entry'),
))
def test_authority_module_identity_observation_is_exact(module_name,initial,mutation):
    # Private cache-shaped data only: never insert a fabricated edition into
    # sys.modules, call a proof gate, or supply an accepting authority fixture.
    modules = {'unrelated.cached.module':object()}
    if initial == 'preloaded': modules[module_name] = object()
    before = _tracked_module_identities(modules)
    if mutation == 'insert': modules[module_name] = object()
    elif mutation == 'insert_none': modules[module_name] = None
    elif mutation == 'remove': del modules[module_name]
    elif mutation == 'replace': modules[module_name] = object()
    elif mutation == 'extra_entry': modules[module_name+'.unexpected'] = object()
    if mutation == 'unchanged':
        _assert_tracked_modules_unchanged(before,modules)
    else:
        with pytest.raises(AssertionError,match='authority module'):
            _assert_tracked_modules_unchanged(before,modules)


# Collection itself must not add/remove/replace any watched authority module.
_assert_tracked_modules_unchanged(_PROJECT_IMPORT_MODULES_BEFORE)
