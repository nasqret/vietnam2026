"""Exact conservative polynomial-operation notation; no proof acceptance.

Only the seven concrete public formulas and 383 predecessor definition
objects are inspected.  No candidate factory, catalogue, proof bundle,
independent verifier or successful proof receipt supplies these tests.
"""

from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
import importlib.util
from pathlib import Path
import re
import sys

import pytest


_AUTHORITY_ROOTS = ('peano_lab.library.editions_v31','constructive_g009_checkpoints',
                    'check_constructive_g009','constructive_polynomial_division_checkpoints',
                    'check_constructive_polynomial_division')


def _authority_modules(modules=None):
    modules = sys.modules if modules is None else modules
    return {name:value for name,value in modules.items()
            if any(name==root or name.startswith(root+'.') for root in _AUTHORITY_ROOTS)}


def _assert_authority_unchanged(before,modules=None):
    after = _authority_modules(modules)
    assert after.keys()==before.keys(), 'proof-authority module inventory changed'
    assert all(after[name] is value for name,value in before.items()), 'proof-authority module identity changed'


_AUTHORITY_BEFORE_IMPORT = _authority_modules()
import constructive_g009_definitions as previous_definitions
import constructive_g009_definition_graph as previous_graph

_OLD_MODULES = {name:value for name,value in sys.modules.items()
                if name.startswith('constructive_') and name.endswith(('_definitions','_definition_graph'))}
_OLD_BYTES = {Path(module.__file__):sha256(Path(module.__file__).read_bytes()).hexdigest()
              for module in _OLD_MODULES.values()}

import constructive_polynomial_division_definitions as definitions
import constructive_polynomial_division_definition_graph as graph
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.kernel.terms import ParseError
from peano_lab.library.formula_dag import FormulaArena


PRIOR = previous_definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
ALL = definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
NEW = definitions.POLYNOMIAL_DIVISION_DEFINITIONS
EXPECTED = (
    ('FpCoefficientNegation',('p','ab','ac','rb','rc','L'),
     definitions.subtraction.prime_field_polynomial_negate_relation,('Lt','BetaAt','FpNeg')),
    ('FpCoefficientSubtraction',('p','ab','ac','bb','bc','rb','rc','L'),
     definitions.subtraction.prime_field_polynomial_subtract_relation,('Lt','BetaAt','FpAdd')),
    ('PolynomialSuffix',('b','c','t','d','e','M'),
     definitions.trim.prime_field_polynomial_suffix_relation,('Lt','BetaAt')),
    ('FpPolynomialTrim',('p','b','c','L','t','d','e','M'),
     definitions.trim.prime_field_polynomial_trim_relation,('BetaPrefixInto','Lt','BetaAt','PolynomialSuffix')),
    ('FpMonic',('p','b','c','L'),
     definitions.monic.prime_field_polynomial_monic_relation,('BetaPrefixInto','BetaAt')),
    ('FpMonicNormalization',('p','k','ab','ac','bb','bc','L'),
     definitions.monic.prime_field_polynomial_monic_normalization_relation,('BetaAt','FpInv','FpPolyScale')),
    ('FpSyntheticDivision',('p','b','c','a','n','qb','qc','r'),
     definitions.synthetic.prime_field_polynomial_synthetic_division_relation,('FpHornerTrace','MatrixAffineSlice')),
)
MATH_MODULES = (definitions.subtraction,definitions.trim,definitions.monic,definitions.synthetic)


@pytest.fixture(autouse=True)
def _unchanged_authority_and_predecessors():
    before = _authority_modules()
    yield
    _assert_authority_unchanged(before)
    assert all(sys.modules[name] is module for name,module in _OLD_MODULES.items())
    assert all(sha256(path.read_bytes()).hexdigest()==digest for path,digest in _OLD_BYTES.items())


def _same_ast(left,right):
    pending,seen = [(left,right)],set()
    while pending:
        a,b = pending.pop()
        assert type(a) is type(b)
        key = id(a),id(b)
        if key in seen: continue
        seen.add(key)
        if is_dataclass(a):
            pending.extend((getattr(a,item.name),getattr(b,item.name)) for item in fields(a))
        else:
            assert a==b


def _and(*parts):
    result = '('+parts[-1]+')'
    for part in reversed(parts[:-1]): result = '('+part+') /\\ ('+result+')'
    return result


def _call(name,*arguments):
    return name+'('+','.join(arguments)+')'


def _independent(name,arguments,context=()):
    """Assemble each new formula only in actual inherited named vocabulary."""
    used = set(context)
    used.update(re.findall(r'[A-Za-z_][A-Za-z0-9_]*',' '.join(arguments)))
    counter = 0

    def fresh(count):
        nonlocal counter
        values = []
        while len(values)<count:
            value = 'independent_polynomial_definition_'+str(counter)
            counter += 1
            if value not in used:
                values.append(value)
                used.add(value)
        return tuple(values)

    def suffix(b,c,t,d,e,M):
        i,a = fresh(2)
        return (f'forall {i} {a}. Lt({i},{M}) -> '
                f'BetaAt({b},{c},({t})+{i},{a}) -> BetaAt({d},{e},{i},{a})')

    if name=='FpCoefficientNegation':
        p,ab,ac,rb,rc,L = arguments
        i,a,r = fresh(3)
        return f'forall {i}. Lt({i},{L}) -> exists {a} {r}. '+_and(
            f'BetaAt({ab},{ac},{i},{a})',f'BetaAt({rb},{rc},{i},{r})',f'FpNeg({p},{a},{r})')
    if name=='FpCoefficientSubtraction':
        p,ab,ac,bb,bc,rb,rc,L = arguments
        i,a,b,r = fresh(4)
        return f'forall {i}. Lt({i},{L}) -> exists {a} {b} {r}. '+_and(
            f'BetaAt({ab},{ac},{i},{a})',f'BetaAt({bb},{bc},{i},{b})',
            f'BetaAt({rb},{rc},{i},{r})',f'FpAdd({p},{b},{r},{a})')
    if name=='PolynomialSuffix':
        return suffix(*arguments)
    if name=='FpPolynomialTrim':
        p,b,c,L,t,d,e,M = arguments
        i,a = fresh(2)
        removed = f'forall {i}. Lt({i},{t}) -> BetaAt({b},{c},{i},0)'
        head = f'exists {a}. '+_and(f'BetaAt({d},{e},0,{a})',f'~({a}=0)')
        return _and(f'({L})=({t})+({M})',f'BetaPrefixInto({b},{c},{L},{p})',removed,
                    suffix(b,c,t,d,e,M),f'({M})=0 \\/ ({head})')
    if name=='FpMonic':
        p,b,c,L = arguments
        return _and(f'~(({L})=0)',f'BetaPrefixInto({b},{c},{L},{p})',f'BetaAt({b},{c},0,1)')
    if name=='FpMonicNormalization':
        p,k,ab,ac,bb,bc,L = arguments
        a, = fresh(1)
        inverse = f'exists {a}. '+_and(f'BetaAt({ab},{ac},0,{a})',f'FpInv({p},{a},{k})')
        return _and(f'~(({L})=0)',inverse,f'FpPolyScale({p},{k},{ab},{ac},{bb},{bc},{L})')
    if name=='FpSyntheticDivision':
        p,b,c,a,n,qb,qc,r = arguments
        u,v = fresh(2)
        return f'exists {u} {v}. '+_and(f'FpHornerTrace({p},{b},{c},{a},S ({n}),{r},{u},{v})',
                                      f'MatrixAffineSlice({u},{v},1,1,{qb},{qc},{n})')
    raise AssertionError('unreviewed polynomial graph '+name)


def _parse(source,registry,context=()):
    parser = _LocalDefinedParser(source,registry)
    parser.free = list(context)
    result = parser.parse()
    assert tuple(parser.free)==tuple(context)
    return result


def _binders(source):
    return {name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}


def test_all_383_predecessor_objects_records_identifiers_and_routes_remain_exact():
    old,_,_ = previous_graph.reviewed_registry()
    current,order,layers = graph.reviewed_registry()
    assert len(PRIOR)==len(old)==383
    assert definitions.HISTORICAL_DEFINITIONS_BY_NAME is PRIOR
    assert all(ALL[name] is item for name,item in PRIOR.items())
    assert all(current[name]==record for name,record in old.items())
    assert len(ALL)==len(current)==len({item.stable_id for item in ALL.values()})==390
    assert tuple(item.stable_id for item in NEW)==tuple(f'ND{i:04d}' for i in range(327,334))
    assert sum(len(item['dependencies']) for item in old.values())==825
    assert sum(len(item['dependencies']) for item in current.values())==844
    assert max(layers.values())==12
    seen = set()
    for name in order:
        assert set(current[name]['dependencies'])<=seen
        assert layers[name]==max((layers[dependency]+1 for dependency in current[name]['dependencies']),default=0)
        seen.add(name)


def test_exact_seven_graphs_single_route_and_immutable_combined_mapping():
    assert definitions.POLYNOMIAL_DIVISION_REGISTRIES==(('polynomial-division-prerequisites',NEW),)
    assert graph.DEFAULT_REGISTRIES==previous_graph.DEFAULT_REGISTRIES+definitions.POLYNOMIAL_DIVISION_REGISTRIES
    assert tuple(item.name for item in NEW)==tuple(item[0] for item in EXPECTED)
    assert tuple(item.arity for item in NEW)==(6,8,6,8,4,7,8)
    with pytest.raises(TypeError): ALL['Unreviewed']=NEW[0]
    public = set()
    for module in MATH_MODULES:
        path = Path(module.__file__).resolve()
        assert path==definitions.MATH_DIRECTORY/(module.__name__.rsplit('.',1)[1]+'.py')
        source = ast.parse(path.read_bytes())
        public.update((module.__name__,node.name) for node in source.body
                      if isinstance(node,ast.FunctionDef) and node.name.endswith('_relation') and not node.name.startswith('_'))
    assert public=={(builder.__module__,builder.__name__) for _,_,builder,_ in EXPECTED}


def test_definition_import_cannot_invoke_any_new_theorem_factory(monkeypatch):
    def reject(*args,**kwargs):
        raise AssertionError('a notation import called a theorem factory')
    for module in MATH_MODULES:
        name = 'make_'+module.__name__.rsplit('.',1)[1].removesuffix('_candidate')+'_candidate_theorems'
        assert callable(getattr(module,name))
        monkeypatch.setattr(module,name,reject)
    path = Path(definitions.__file__)
    spec = importlib.util.spec_from_file_location('_polynomial_notation_only_import',path)
    assert spec is not None and spec.loader is not None
    private = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(),str(path),'exec'),private.__dict__)
    assert len(private.POLYNOMIAL_DIVISION_DEFINITIONS)==7
    assert all(private.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name] is item for name,item in PRIOR.items())


def test_actual_ast_novelty_and_existing_vocabulary_reuse_without_aliases():
    prior = {}
    for item in PRIOR.values():
        prior.setdefault(item.arity,set()).add(FormulaArena().freeze(item.template_formula).to_json())
    for item in NEW:
        value = FormulaArena().freeze(item.template_formula).to_json()
        assert value not in prior.get(item.arity,set()),item.name
        prior.setdefault(item.arity,set()).add(value)
    for name in ('BetaPrefixInto','BetaPrefixEqual','FpPolyAdd','FpPolyScale','FpNeg','FpInv',
                 'FpAdd','FpMul','FpHornerTrace','MatrixAffineSlice','FpRepresentedDegree','Lt','BetaAt'):
        assert ALL[name] is PRIOR[name]
    assert not {'FpCanonicalCoefficients','FpCoefficientAdd','FpCoefficientScale'} & ALL.keys()


@pytest.mark.parametrize('name,parameters,builder,dependencies',EXPECTED,ids=[row[0] for row in EXPECTED])
def test_every_template_is_the_public_graph_and_an_independent_lower_vocabulary_expansion(name,parameters,builder,dependencies):
    item = ALL[name]
    assert item.parameters==parameters and item.conceptual_dependencies==dependencies
    public = parse_formula_in_context(builder(*parameters,tag='independent_public',variables=parameters),list(parameters))
    _same_ast(public,item.template_formula)
    _same_ast(public,_parse(_independent(name,parameters,parameters),PRIOR,parameters))
    _same_ast(public,_parse(_call(name,*parameters),ALL,parameters))


@pytest.mark.parametrize('name,parameters,builder,dependencies',EXPECTED,ids=[row[0] for row in EXPECTED])
@pytest.mark.parametrize('kind',('compound','large','zero','repeated','reversed'))
def test_whole_context_compound_big_numeral_and_nested_quantifier_roundtrips(name,parameters,builder,dependencies,kind):
    choices = {'compound':('S (x+y)','x*y','x+y'),'large':(str(2**96+17),'x+y','y'),
               'zero':('0',),'repeated':('x+y',),'reversed':('y','x')}[kind]
    arguments = tuple(choices[index%len(choices)] for index in range(len(parameters)))
    context = ('unused_outer','x','unused_middle','y','unused_last')
    public = builder(*arguments,tag='roundtrip',variables=context)
    _same_ast(parse_formula_in_context(public,list(context)),_parse(_call(name,*arguments),ALL,context))
    _same_ast(parse_formula_in_context(public,list(context)),_parse(_independent(name,arguments,context),PRIOR,context))
    _same_ast(parse_formula_in_context('forall unused_outer. forall x. exists y. ('+public+')',[]),
              _parse('forall unused_outer. forall x. exists y. '+_call(name,*arguments),ALL))


@pytest.mark.parametrize('name,parameters,builder,dependencies',EXPECTED,ids=[row[0] for row in EXPECTED])
def test_all_generated_public_binders_reject_even_unused_surrounding_capture(name,parameters,builder,dependencies):
    source = builder(*parameters,tag='capture_audit',variables=parameters)
    binders = _binders(source)
    assert binders and not binders.intersection(parameters)
    for binder in sorted(binders):
        with pytest.raises(ValueError,match='captures'):
            builder(*parameters,tag='capture_audit',variables=(*parameters,binder))
        with pytest.raises(ValueError,match='captures'):
            builder(parameters[0]+'+'+binder,*parameters[1:],tag='capture_audit',variables=(*parameters,binder))


@pytest.mark.parametrize('item',NEW,ids=lambda item:item.name)
def test_named_instantiation_avoids_early_middle_and_late_internal_binder_names(item):
    binders = sorted(_binders(item.template_source))
    assert binders
    for binder in dict.fromkeys((binders[0],binders[len(binders)//2],binders[-1])):
        arguments = (binder,)*item.arity
        context = ('unused',binder,'other_unused')
        _same_ast(_parse(_call(item.name,*arguments),ALL,context),
                  _parse(_independent(item.name,arguments,context),PRIOR,context))


@pytest.mark.parametrize('item',NEW,ids=lambda item:item.name)
def test_every_one_of_19_expansion_edges_occurs_in_the_actual_formula(item):
    compact = _FormulaCompactor(definitions.definition_closure(item.conceptual_dependencies)).compact(item.template_source)
    assert compact['exact_ast_equivalence'] is True
    assert item.stable_id not in compact['statement_definition_uses']
    for dependency in item.conceptual_dependencies:
        child = ALL[dependency]
        isolated = _FormulaCompactor((child,)).compact(item.template_source)
        assert child.stable_id in isolated['statement_definition_uses'],(item.name,dependency)


@pytest.mark.parametrize('item',NEW,ids=lambda item:item.name)
def test_every_new_template_compacts_and_reexpands_without_changing_its_ast(item):
    compact = _FormulaCompactor(NEW).compact(item.template_source)
    assert compact['exact_ast_equivalence'] is True
    assert item.stable_id in compact['statement_definition_uses']
    _same_ast(_parse(compact['defined_statement'],ALL,tuple(compact['free_names'])),
              parse_formula_in_context(item.template_source,list(compact['free_names'])))


@pytest.mark.parametrize('name,forbidden',(
    ('PolynomialSuffix',('MatrixAffineSlice','FpHornerTrace','BetaPrefixInto')),
    ('FpMonicNormalization',('FpMonic','FpRepresentedDegree','Prime')),
    ('FpSyntheticDivision',('FpMonic','FpRepresentedDegree','Prime','FpCoefficientSubtraction')),
    ('FpCoefficientSubtraction',('Prime','FpRepresentedDegree','FpPolyAdd')),
    ('FpPolynomialTrim',('Prime','FpRepresentedDegree','MatrixAffineSlice')),
))
def test_proved_consequences_and_construction_helpers_are_not_invented_expansion_edges(name,forbidden):
    item = ALL[name]
    assert not set(forbidden) & set(item.conceptual_dependencies)
    for dependency in forbidden:
        compact = _FormulaCompactor((ALL[dependency],)).compact(item.template_source)
        assert ALL[dependency].stable_id not in compact['statement_definition_uses'],(name,dependency)


@pytest.mark.parametrize('item',NEW,ids=lambda item:item.name)
@pytest.mark.parametrize('delta',(-1,1))
def test_wrong_named_arities_are_rejected_without_implicit_parameters(item,delta):
    with pytest.raises(ParseError,match='expects'):
        _LocalDefinedParser(_call(item.name,*(('x',)*(item.arity+delta))),ALL).parse()


@pytest.mark.parametrize('names',(None,True,'FpMonic',['FpMonic'],('',),(True,)))
def test_invalid_closure_inputs_fail_closed(names):
    with pytest.raises(ValueError,match='exact tuple'):
        definitions.definition_closure(names)


@pytest.mark.parametrize('names',(('Absent',),('FpMonic','unreviewed')))
def test_unknown_closure_names_fail_closed(names):
    with pytest.raises(ValueError,match='unknown or cyclic'):
        definitions.definition_closure(names)


def test_transitive_closure_has_only_actual_acyclic_definition_prerequisites():
    assert definitions.definition_closure(())==()
    chosen = definitions.definition_closure(('FpSyntheticDivision','FpMonicNormalization','FpSyntheticDivision'))
    names = [item.name for item in chosen]
    assert len(names)==len(set(names))
    assert {'FpHornerTrace','MatrixAffineSlice','FpInv','FpPolyScale'}<=set(names)
    assert not {'FpMonic','FpRepresentedDegree','FpCoefficientSubtraction','Prime'} & set(names)
    seen = set()
    for item in chosen:
        assert set(item.conceptual_dependencies)<=seen
        seen.add(item.name)


def _changed_registry(changes):
    return tuple((route,tuple(changes.get(item.name,item) for item in items))
                 for route,items in graph.DEFAULT_REGISTRIES)


@pytest.mark.parametrize('attack',('duplicate_id','duplicate_name','wrong_template','wrong_formula',
                                  'missing_dependency','self_cycle','two_cycle','bad_route'))
def test_malformed_identity_template_or_expansion_graph_is_rejected(attack):
    item = NEW[0]
    if attack=='duplicate_id': changes = {item.name:replace(item,stable_id=PRIOR['Lt'].stable_id)}
    elif attack=='duplicate_name': changes = {item.name:replace(item,name='Lt')}
    elif attack=='wrong_template': changes = {item.name:replace(item,template_source='0=1')}
    elif attack=='wrong_formula': changes = {item.name:replace(item,template_formula=parse_formula_in_context('0=1',[]))}
    elif attack=='missing_dependency': changes = {item.name:replace(item,conceptual_dependencies=('Absent',))}
    elif attack=='self_cycle': changes = {item.name:replace(item,conceptual_dependencies=(item.name,))}
    elif attack=='two_cycle':
        changes = {item.name:replace(item,conceptual_dependencies=(NEW[1].name,)),
                   NEW[1].name:replace(NEW[1],conceptual_dependencies=(item.name,))}
    else: changes = {}
    registries = _changed_registry(changes)
    if attack=='bad_route': registries += (('../outside',(item,)),)
    with pytest.raises(graph.DefinitionGraphError): graph.reviewed_registry(registries)


def test_private_cycle_mutation_does_not_change_the_inherited_registry(monkeypatch):
    item = NEW[-1]
    changed = dict(ALL)
    changed[item.name] = replace(item,conceptual_dependencies=(item.name,))
    monkeypatch.setattr(definitions,'ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME',changed)
    with pytest.raises(ValueError,match='unknown or cyclic'):
        definitions.definition_closure((item.name,))
    assert all(PRIOR[name] is value for name,value in previous_definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME.items())


def _small_campaign(parameters=('p','b','c','a','n','qb','qc','r')):
    convergent = PRIOR['Convergent']
    return {'schema':'constructive-grand-campaign-v1','definitions':{
        'Convergent':{'parameters':list(convergent.parameters),'meaning':convergent.summary,
                     'expansion':convergent.template_source,'reviewed_definition_id':convergent.stable_id},
        'FiniteField':{'parameters':['p','k'],'meaning':'Prime-power field planning notation.',
                       'expansion':'A field with p^k elements is still a separate construction.'},
        'FpSyntheticDivision':{'parameters':list(parameters),'meaning':'Actual finite execution.',
                               'expansion':'0=0'}},
        'nodes':[{'id':'G091','status':'available','statement':'FiniteField(p,k) and FpSyntheticDivision(p,b,c,a,n,qb,qc,r)'}]}


def test_blueprint_metadata_never_claims_synthetic_division_is_a_prime_power_field():
    assert graph.REVIEWED_BLUEPRINT_ALIASES is previous_graph.REVIEWED_BLUEPRINT_ALIASES
    assert 'FiniteField' not in graph.REVIEWED_BLUEPRINT_ALIASES
    document = graph.build_definition_graph(_small_campaign())
    records = {record['name']:record for record in document['definitions']}
    assert records['FiniteField']['reviewed_match'] is None
    assert records['FpSyntheticDivision']['reviewed_match']['reviewed_id']=='ND0333'
    assert records['FpSyntheticDivision']['reviewed_match']['blueprint_expansion_is_kernel_checked'] is False
    assert document['reviewed_definition_count']==390 and document['reviewed_definition_edge_count']==844
    assert all(record['authority']=='blueprint-vocabulary-only' for record in document['definitions'])
    assert 'never theorem-proof dependencies' in document['authority_policy']['notation_edges']
    assert not {'alpha_eligible','stable_eligible','full_G091_proved','full_prime_power_fields_proved'} & document.keys()
    assert all(edge['kind']=='definition_uses_definition' for edge in document['definition_edges'])


def test_wrong_blueprint_arity_does_not_supply_checked_evidence():
    document = graph.build_definition_graph(_small_campaign(('p','k')))
    assert document['incompatible_reviewed_match_count']==1
    assert document['incompatible_reviewed_matches'][0]['confers_checked_evidence'] is False


def test_existing_zero_numerator_erratum_guard_remains_mandatory():
    campaign = _small_campaign()
    del campaign['definitions']['Convergent']
    with pytest.raises(graph.DefinitionGraphError,match='excludes 0/1'):
        graph.build_definition_graph(campaign)


def test_scope_prose_keeps_lengths_field_units_empty_domains_and_open_g091_separate():
    assert 'highest-degree-first' in ALL['FpCoefficientNegation'].summary
    assert 'p=0' in ALL['FpCoefficientNegation'].summary
    assert 'FpAdd(p,b,r,a)' in ALL['FpCoefficientSubtraction'].summary
    assert 'equality of raw beta codes' in ALL['FpCoefficientSubtraction'].summary
    assert 'not itself a definition-expansion edge' in ALL['PolynomialSuffix'].summary
    assert 'L=t+M' in ALL['FpPolynomialTrim'].summary and 'empty or' in ALL['FpPolynomialTrim'].summary
    assert 'natural 1' in ALL['FpMonic'].summary and 'not signed code 2' in ALL['FpMonic'].summary
    assert 'separate conclusions, not premises' in ALL['FpMonicNormalization'].summary
    assert 'composite modulus' in ALL['FpMonicNormalization'].summary
    assert 'offset 1 and stride 1' in ALL['FpSyntheticDivision'].summary
    assert 'empty quotient' in ALL['FpSyntheticDivision'].summary
    assert 'not arbitrary-divisor Euclidean division or G091' in ALL['FpSyntheticDivision'].summary


@pytest.mark.parametrize('root',_AUTHORITY_ROOTS)
@pytest.mark.parametrize('attack',('insert','insert_none','remove','replace','child'))
def test_authority_identity_observer_rejects_changes_without_modifying_real_module_cache(root,attack):
    modules = {'unrelated':object()}
    if attack in ('remove','replace'): modules[root]=object()
    before = _authority_modules(modules)
    if attack=='insert': modules[root]=object()
    elif attack=='insert_none': modules[root]=None
    elif attack=='remove': del modules[root]
    elif attack=='replace': modules[root]=object()
    else: modules[root+'.extra']=object()
    with pytest.raises(AssertionError,match='proof-authority module'):
        _assert_authority_unchanged(before,modules)


_assert_authority_unchanged(_AUTHORITY_BEFORE_IMPORT)


if __name__=='__main__':
    import resource
    import signal
    import time
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    started = time.monotonic()
    status = int(pytest.main(['-q','--tb=short','-p','no:cacheprovider',__file__]))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024 and time.monotonic()-started<180
    print({'status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak,
           'cpu_limits':(170,175),'wall_seconds':180},flush=True)
    raise SystemExit(status)
