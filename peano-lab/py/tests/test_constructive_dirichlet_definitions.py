"""Exact conservative Dirichlet graphs, real edges, and inherited identities."""

from collections import Counter
from dataclasses import fields,is_dataclass,replace
from pathlib import Path
import re
import sys

import pytest

ROOT=Path(__file__).resolve().parents[3]
if str(ROOT/'scripts') not in sys.path:
    sys.path.insert(0,str(ROOT/'scripts'))

import constructive_lower_continuation_definition_graph as previous
import constructive_dirichlet_definition_graph as graph
import constructive_dirichlet_definitions as definitions
from constructive_lower_continuation_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR
from constructive_dirichlet_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL, DIRICHLET_DEFINITIONS as NEW,
    DIRICHLET_REGISTRIES, definition_closure,
)
from constructive_dirichlet_defined_adapter import compact_formula_source
from constructive_formula_compactor import _FormulaCompactor,_LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.kernel.terms import ParseError
from peano_lab.library import signed_finite_support_candidate as finite
from peano_lab.library import dirichlet_convolution_candidate as convolution
from peano_lab.library import dirichlet_fubini_candidate as fubini
from peano_lab.library import dirichlet_units_candidate as units
from peano_lab.library import mobius_inversion_candidate as inversion
from peano_lab.library.formula_dag import FormulaArena


EXPECTED=(
    ('SignedZeroWindow',('F','k','l'),finite.signed_arithmetic_zero_window_relation,('Le','Lt','ArithAt')),
    ('DirichletEntry',('F','G','n','d','z'),convolution.dirichlet_convolution_entry_relation,('Dvd','ArithAt','SignedMul')),
    ('DirichletPrefix',('F','G','n','l','M'),convolution.dirichlet_convolution_prefix_relation,('ArithTable','Le','ArithAt','DirichletEntry')),
    ('DirichletSum',('F','G','n','z'),convolution.dirichlet_convolution_sum_relation,('DirichletPrefix','SignedPrefixSum')),
    ('DirichletTable',('N','F','G','H'),convolution.dirichlet_convolution_table_relation,('ArithTable','Le','ArithAt','DirichletSum')),
    ('DirichletGridEntry',('F','G','H','n','a','e','z'),fubini.signed_dirichlet_grid_entry_relation,('Dvd','ArithAt','SignedMul')),
    ('DirichletFlatEntry',('F','G','H','n','i','z'),fubini.signed_dirichlet_flat_entry_relation,('Lt','DirichletGridEntry')),
    ('DirichletFlatPrefix',('F','G','H','n','l','T'),fubini.signed_dirichlet_flat_prefix_relation,('ArithTable','Le','ArithAt','DirichletFlatEntry')),
    ('DirichletGrid',('F','G','H','n','T'),fubini.signed_dirichlet_grid_table_relation,('ArithTable','Le','ArithAt','DirichletGridEntry')),
    ('DirichletFactorRow',('F','G','H','n','a','V'),fubini.signed_dirichlet_factor_row_relation,('ArithTable','Le','ArithAt','DirichletGridEntry')),
    ('ConstantOneTable',('N','U'),units.dirichlet_constant_one_table_relation,('ArithTable','Le','ArithAt')),
    ('KroneckerDeltaTable',('N','E'),units.dirichlet_kronecker_delta_table_relation,('ArithTable','Le','ArithAt')),
    ('DivisorTransform',('N','F','G'),inversion.signed_arithmetic_divisor_transform_relation,('Le','ArithAt','DivisorSum')),
)


def _same_ast(left,right):
    pending,seen=[(left,right)],set()
    while pending:
        a,b=pending.pop()
        assert type(a) is type(b)
        key=id(a),id(b)
        if key in seen:
            continue
        seen.add(key)
        if is_dataclass(a):
            pending.extend((getattr(a,field.name),getattr(b,field.name)) for field in fields(a))
        else:
            assert a==b


def test_all_356_inherited_definitions_and_every_old_dag_record_remain_exact():
    old,_,_=previous.reviewed_registry()
    current,order,layers=graph.reviewed_registry()
    assert len(PRIOR)==len(old)==356
    assert all(ALL[name] is item for name,item in PRIOR.items())
    assert all(current[name]==record for name,record in old.items())
    assert len(ALL)==len(current)==369
    assert len({item.stable_id for item in ALL.values()})==369
    assert tuple(item.stable_id for item in NEW)==tuple(f'ND{i:04d}' for i in range(300,313))
    assert tuple(item.name for item in NEW)==tuple(item[0] for item in EXPECTED)
    assert sum(len(row['dependencies']) for row in old.values())==742
    assert sum(len(row['dependencies']) for row in current.values())==784
    assert max(layers.values())==12
    seen=set()
    for name in order:
        assert set(current[name]['dependencies'])<=seen
        assert layers[name]==max((layers[dep]+1 for dep in current[name]['dependencies']),default=0)
        seen.add(name)


def test_family_registries_are_an_exact_disjoint_partition():
    assert tuple((route,len(items)) for route,items in DIRICHLET_REGISTRIES)==(
        ('finite-support',1),('dirichlet-convolution',4),('dirichlet-fubini',5),
        ('dirichlet-units',2),('mobius-inversion',1))
    assert Counter(item.name for _,items in DIRICHLET_REGISTRIES for item in items)==Counter(item.name for item in NEW)
    assert graph.DEFAULT_REGISTRIES==previous.DEFAULT_REGISTRIES+DIRICHLET_REGISTRIES
    with pytest.raises(TypeError):
        ALL['unreviewed']=NEW[0]


def test_no_new_definition_duplicates_an_old_or_another_new_exact_identity():
    seen={}
    for item in PRIOR.values():
        encoded=FormulaArena().freeze(item.template_formula).to_json()
        seen.setdefault(item.arity,{}).setdefault(encoded,[]).append(item.name)
    for item in NEW:
        encoded=FormulaArena().freeze(item.template_formula).to_json()
        assert encoded not in seen.get(item.arity,{}),item.name
        seen.setdefault(item.arity,{})[encoded]=[item.name]
    for name in ('ArithTable','ArithAt','ArithPositiveEqual','SignedMul','SignedPrefixSum','DivisorSum','DivisorMask'):
        assert ALL[name] is PRIOR[name]
    assert graph.REVIEWED_BLUEPRINT_ALIASES is previous.REVIEWED_BLUEPRINT_ALIASES
    assert not set(item.name for item in NEW)&set(graph.REVIEWED_BLUEPRINT_ALIASES)


@pytest.mark.parametrize('name,parameters,builder,dependencies',EXPECTED,ids=lambda value:value if isinstance(value,str) else None)
def test_every_definition_has_the_exact_public_graph_parameter_order_and_edges(name,parameters,builder,dependencies):
    item=ALL[name]
    assert item.parameters==parameters
    assert item.conceptual_dependencies==dependencies
    expected=parse_formula_in_context(builder(*parameters,tag='independent',variables=parameters),list(parameters))
    _same_ast(item.template_formula,expected)
    parser=_LocalDefinedParser(f"{name}({','.join(parameters)})",ALL)
    parser.free=list(parameters)
    _same_ast(parser.parse(),expected)
    assert tuple(parser.free)==parameters


@pytest.mark.parametrize('name,parameters,builder,dependencies',EXPECTED,ids=lambda value:value if isinstance(value,str) else None)
@pytest.mark.parametrize('large',(False,True),ids=('compound','large-numeral'))
def test_nested_binders_repeated_terms_and_large_literals_expand_hygienically(name,parameters,builder,dependencies,large):
    choices=('x','y','S (x+y)','x*y') if not large else (str(2**96+17),'x+y','y','x')
    arguments=tuple(choices[index%len(choices)] for index in range(len(parameters)))
    explicit=builder(*arguments,tag='nested',variables=('x','y'))
    expected=parse_formula_in_context(f'forall x. exists y. ({explicit})',[])
    surface=f"forall x. exists y. {name}({','.join(arguments)})"
    _same_ast(_LocalDefinedParser(surface,ALL).parse(),expected)


@pytest.mark.parametrize('definition',NEW,ids=lambda item:item.name)
def test_every_declared_expansion_edge_really_occurs(definition):
    compact=_FormulaCompactor(definition_closure(definition.conceptual_dependencies)).compact(definition.template_source)
    assert compact['exact_ast_equivalence'] is True
    assert definition.stable_id not in compact['statement_definition_uses']
    for name in definition.conceptual_dependencies:
        child=ALL[name]
        isolated=_FormulaCompactor((child,)).compact(definition.template_source)
        assert isolated['exact_ast_equivalence'] is True
        assert child.stable_id in isolated['statement_definition_uses'],(definition.name,name)


@pytest.mark.parametrize('definition',NEW,ids=lambda item:item.name)
def test_new_readable_adapter_preserves_exact_template_and_free_context(definition):
    compact=compact_formula_source(definition.template_source)
    assert compact.receipt.exact_ast_equivalence is True
    assert compact.expanded_source==definition.template_source
    assert compact.receipt.definition_uses
    assert definition.stable_id in {item.definition_id for item in compact.receipt.definition_uses}
    parser=_LocalDefinedParser(compact.defined_source,ALL)
    parser.free=list(compact.receipt.free_names)
    _same_ast(parser.parse(),parse_formula_in_context(definition.template_source,list(compact.receipt.free_names)))


@pytest.mark.parametrize('definition',NEW,ids=lambda item:item.name)
@pytest.mark.parametrize('arity_delta',(-1,1))
def test_wrong_surface_arities_fail_closed(definition,arity_delta):
    arguments=('x',)*(definition.arity+arity_delta)
    with pytest.raises(ParseError,match='expects'):
        _LocalDefinedParser(f"{definition.name}({','.join(arguments)})",ALL).parse()


@pytest.mark.parametrize('names',(None,True,'ArithTable',['ArithTable'],('',),(True,)))
def test_malformed_definition_selection_fails_closed(names):
    with pytest.raises(ValueError,match='exact tuple'):
        definition_closure(names)


@pytest.mark.parametrize('names',(('MissingNotation',),('DirichletTable','not_reviewed')))
def test_unknown_definition_cannot_enter_the_actual_closure(names):
    with pytest.raises(ValueError,match='unknown or cyclic'):
        definition_closure(names)


def test_empty_repeated_and_ordered_definition_closures_have_exact_edges_only():
    assert definition_closure(())==()
    ordered=definition_closure(('DirichletGrid','DirichletSum','DirichletGrid'))
    names=tuple(item.name for item in ordered)
    assert len(names)==len(set(names))
    assert 'DirichletGridEntry' in names and 'DirichletEntry' in names
    assert 'DirichletFlatPrefix' not in names and 'DirichletFlatEntry' not in names
    assert 'KroneckerDeltaTable' not in names and 'DivisorTransform' not in names
    seen=set()
    for item in ordered:
        assert set(item.conceptual_dependencies)<=seen
        seen.add(item.name)


def _with_replacement(original,altered):
    return tuple((route,tuple(altered if item.name==original.name else item for item in items))
                 for route,items in graph.DEFAULT_REGISTRIES)


@pytest.mark.parametrize('attack',('duplicate_id','duplicate_name','wrong_template','wrong_formula','missing_dependency','self_cycle','two_cycle','bad_route'))
def test_hostile_registry_identity_formula_and_topology_changes_fail_closed(attack):
    item=NEW[0]
    if attack=='duplicate_id':
        registries=_with_replacement(item,replace(item,stable_id=PRIOR['ArithTable'].stable_id))
    elif attack=='duplicate_name':
        registries=_with_replacement(item,replace(item,name='ArithTable'))
    elif attack=='wrong_template':
        registries=_with_replacement(item,replace(item,template_source='0=1'))
    elif attack=='wrong_formula':
        registries=_with_replacement(item,replace(item,template_formula=parse_formula_in_context('0=1',[])))
    elif attack=='missing_dependency':
        registries=_with_replacement(item,replace(item,conceptual_dependencies=('MissingNotation',)))
    elif attack=='self_cycle':
        registries=_with_replacement(item,replace(item,conceptual_dependencies=(item.name,)))
    elif attack=='two_cycle':
        first=replace(NEW[0],conceptual_dependencies=(NEW[1].name,))
        second=replace(NEW[1],conceptual_dependencies=(NEW[0].name,))
        replacements={first.name:first,second.name:second}
        registries=tuple((route,tuple(replacements.get(entry.name,entry) for entry in items))
                         for route,items in graph.DEFAULT_REGISTRIES)
    else:
        registries=graph.DEFAULT_REGISTRIES+(('../outside',(NEW[0],)),)
    with pytest.raises(graph.DefinitionGraphError):
        graph.reviewed_registry(registries)


def test_runtime_closure_rejects_a_cycle_even_in_an_untrusted_replacement_map(monkeypatch):
    item=ALL['DirichletGrid']
    altered=dict(ALL)
    altered[item.name]=replace(item,conceptual_dependencies=(item.name,))
    monkeypatch.setattr(definitions,'ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME',altered)
    with pytest.raises(ValueError,match='unknown or cyclic'):
        definition_closure((item.name,))


def _small_campaign(parameters=('N','F','G')):
    convergent=PRIOR['Convergent']
    return {'schema':'constructive-grand-campaign-v1',
            'definitions':{'Convergent':{'parameters':list(convergent.parameters),
                'meaning':convergent.summary,'expansion':convergent.template_source,
                'reviewed_definition_id':convergent.stable_id},
                'DivisorTransform':{'parameters':list(parameters),
                'meaning':'A planning label does not itself certify an inversion theorem.',
                'expansion':'N=N'}},
            'nodes':[{'id':'G007','statement':'DivisorTransform(N,F,G)'}]}


def test_notation_edges_and_compatible_names_grant_no_proof_or_admission_authority():
    data=graph.build_definition_graph(_small_campaign())
    assert data['reviewed_definition_count']==369 and data['reviewed_definition_edge_count']==784
    assert data['compatible_reviewed_match_count']==2
    assert all(item['blueprint_expansion_is_kernel_checked'] is False for item in data['compatible_reviewed_matches'])
    assert all(item['authority']=='blueprint-vocabulary-only' for item in data['definitions'])
    assert {edge['kind'] for edge in data['milestone_usage_edges']}=={'statement_uses_definition'}
    assert 'never theorem-proof dependencies' in data['authority_policy']['notation_edges']
    assert not {'alpha_eligible','stable_eligible','G007_proved','full_G009_dirichlet_convolution_theory_proved'}&data.keys()


def test_wrong_planning_arity_receives_no_compatible_evidence():
    data=graph.build_definition_graph(_small_campaign(('F','G')))
    assert data['compatible_reviewed_match_count']==1
    assert all(item['blueprint_name']!='DivisorTransform' for item in data['compatible_reviewed_matches'])
    assert data['incompatible_reviewed_match_count']==1
    assert data['incompatible_reviewed_matches'][0]['confers_checked_evidence'] is False


def test_historical_zero_numerator_convergent_erratum_guard_is_preserved():
    campaign=_small_campaign()
    del campaign['definitions']['Convergent']
    with pytest.raises(graph.DefinitionGraphError,match='excludes 0/1'):
        graph.build_definition_graph(campaign)


def test_definition_prose_preserves_half_open_positive_and_unused_endpoint_guards():
    assert 'half-open interval k<=i<l' in ALL['SignedZeroWindow'].summary
    assert 'inclusive index 0<=d<=l' in ALL['DirichletPrefix'].summary
    assert 'Require n>0' in ALL['DirichletSum'].summary
    assert 'does not itself bound a by n' in ALL['DirichletFlatEntry'].summary
    assert 'unused endpoint (S n)*(S n)' in ALL['DirichletGrid'].summary
    assert 'valid endpoint S n is unused' in ALL['DirichletFactorRow'].summary
    assert 'F(a)*(H(e)*G(c))' in ALL['DirichletGridEntry'].summary
    assert 'Positivity of n' in ALL['DirichletGridEntry'].summary
    assert 'code 2' in ALL['ConstantOneTable'].summary
    assert 'zero entry is unrestricted' in ALL['KroneckerDeltaTable'].summary
    assert 'Table validity is a separate prerequisite' in ALL['DivisorTransform'].summary
