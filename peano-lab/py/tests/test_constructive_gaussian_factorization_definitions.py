"""Exact, noncircular Gaussian definition DAG and canonical defined readings."""

from collections import Counter
from dataclasses import replace
from importlib import import_module
import json
from pathlib import Path
import re
import sys

import pytest

ROOT=Path(__file__).resolve().parents[3]
if str(ROOT/'scripts') not in sys.path:
    sys.path.insert(0,str(ROOT/'scripts'))

import constructive_priority_layer_definition_graph as prior_graph
import constructive_gaussian_factorization_definition_graph as graph
from constructive_priority_layer_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR
from constructive_gaussian_factorization_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL,
    GAUSSIAN_FACTORIZATION_DEFINITIONS as NEW,
    GAUSSIAN_FACTORIZATION_REGISTRIES,definition_closure,
)
from constructive_gaussian_factorization_defined_adapter import compact_formula_source,compact_tactic_command
from constructive_formula_compactor import _FormulaCompactor,_LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context,parse_formula_with_names
from peano_lab.kernel.terms import ParseError
from peano_lab.library.theorems import TheoremSpec
from peano_lab.library import gaussian_ring_candidate as ring
from peano_lab.library import gaussian_gcd_candidate as gcd
from peano_lab.library import gaussian_factor_search_candidate as search
from peano_lab.library import gaussian_factorization_candidate as factor
from peano_lab.library import gaussian_factor_permutation_candidate as permutation


MODULES=(
    'gaussian_ring_candidate','gaussian_divisibility_candidate','gaussian_gcd_candidate',
    'gaussian_factor_search_candidate','gaussian_factorization_candidate',
    'gaussian_product_reindex_candidate','gaussian_factor_permutation_candidate',
)
ROWS=tuple(row for module in MODULES for row in getattr(import_module('peano_lab.library.'+module),'make_'+module+'_theorems')(TheoremSpec))


def test_every_historical_object_and_reviewed_record_is_unchanged():
    old,_,_=prior_graph.reviewed_registry()
    current,order,layers=graph.reviewed_registry()
    assert len(PRIOR)==len(old)==264
    assert len(current)==len(ALL)==284
    assert len(NEW)==20
    assert all(ALL[name] is item for name,item in PRIOR.items())
    assert all(current[name]==record for name,record in old.items())
    assert tuple(item.stable_id for item in NEW)==tuple(f'ND{i:04d}' for i in range(208,228))
    assert len({item.stable_id for item in ALL.values()})==284
    assert sum(len(item.conceptual_dependencies) for item in NEW)==50
    assert Counter(item.name for _,items in GAUSSIAN_FACTORIZATION_REGISTRIES for item in items)==Counter(item.name for item in NEW)
    seen=set()
    for name in order:
        assert set(current[name]['dependencies'])<=seen
        assert layers[name]==max((layers[dependency]+1 for dependency in current[name]['dependencies']),default=0)
        assert 'proof_dependency' not in current[name]
        seen.add(name)


@pytest.mark.parametrize('definition',NEW,ids=lambda item:item.name)
def test_template_call_is_exactly_its_original_ha_ast(definition):
    parser=_LocalDefinedParser(f"{definition.name}({','.join(definition.parameters)})",ALL)
    parser.free=list(definition.parameters)
    assert parser.parse()==definition.template_formula
    assert tuple(parser.free)==definition.parameters
    assert parse_formula_in_context(definition.template_source,list(definition.parameters))==definition.template_formula


@pytest.mark.parametrize('definition',NEW,ids=lambda item:item.name)
def test_nested_binding_repeated_terms_and_compound_arguments_are_hygienic(definition):
    arguments=tuple(('x','y','S (x+y)','x*x')[index%4] for index in range(definition.arity))
    substitutions=dict(zip(definition.parameters,arguments))
    pattern=r'\b(?:'+'|'.join(re.escape(parameter) for parameter in definition.parameters)+r')\b'
    expanded=re.sub(pattern,lambda match:f'({substitutions[match.group()]})',definition.template_source)
    expected=parse_formula_in_context(f'forall x. exists y. ({expanded})',[])
    assert _LocalDefinedParser(f"forall x. exists y. {definition.name}({','.join(arguments)})",ALL).parse()==expected
    with pytest.raises(ParseError,match='expects'):
        _LocalDefinedParser(f'{definition.name}()',ALL).parse()


@pytest.mark.parametrize('definition',NEW,ids=lambda item:item.name)
def test_definition_expansion_uses_only_exact_ancestors(definition):
    ancestors=definition_closure(definition.conceptual_dependencies)
    compact=_FormulaCompactor(ancestors).compact(definition.template_source)
    assert compact['exact_ast_equivalence'] is True
    assert definition.stable_id not in compact['statement_definition_uses']
    assert set(compact['statement_definition_uses'])<={item.stable_id for item in ancestors}


BUILDERS={
    'GDvd':ring.gaussian_divides_relation,'GUnit':ring.gaussian_unit_relation,
    'GAssociate':ring.gaussian_associate_relation,'GIrreducible':ring.gaussian_irreducible_relation,
    'GPrime':ring.gaussian_prime_relation,'GBezout':gcd.gaussian_bezout_relation,'GGcd':gcd.gaussian_gcd_relation,
    'GNormBoundedCoordinates':search.gaussian_norm_bounded_coordinates_relation,
    'GProperNormDivisor':search.gaussian_proper_norm_divisor_relation,
    'GStrictNonunitFactorization':search.gaussian_strict_nonunit_factorization_relation,
    'GProduct':factor.gaussian_product_relation,'GAllIrreducible':factor.gaussian_all_irreducible_relation,
    'GAllPrime':factor.gaussian_all_prime_relation,'GIrreducibleFactorization':factor.gaussian_irreducible_factorization_relation,
    'GPrimeFactorization':factor.gaussian_prime_factorization_relation,
    'GFactorAssociateMatching':permutation.gaussian_factor_associate_matching_relation,
    'GFactorPermutation':permutation.gaussian_factor_permutation_relation,
}


@pytest.mark.parametrize('name,builder',BUILDERS.items())
def test_reviewed_graph_matches_the_actual_public_proof_builder(name,builder):
    definition=ALL[name]
    source=builder(*definition.parameters,tag='independent_surface',variables=definition.parameters)
    assert parse_formula_in_context(source,list(definition.parameters))==definition.template_formula


def test_product_step_and_step_prefix_are_actual_adjacent_beta_multiplications():
    step=(f"exists a P Q. ({factor._at('b','c','i','a','independent_step_factor')}) /\\ "
          f"(({factor._at('h','e','i','P','independent_step_before')}) /\\ "
          f"(({factor._at('h','e','S i','Q','independent_step_after')}) /\\ ({ring._mul('P','a','Q','independent_step_multiply')})))")
    assert parse_formula_in_context(step,['b','c','h','e','i'])==ALL['GProductStep'].template_formula
    steps=factor._steps('b','c','h','e','l','independent_steps')
    assert parse_formula_in_context(steps,['b','c','h','e','l'])==ALL['GProductSteps'].template_formula
    reading=_FormulaCompactor(definition_closure(('GProductStep','Lt'))).compact(steps)
    assert 'GProductStep(' in reading['defined_statement']
    product=_FormulaCompactor(definition_closure(('GProductSteps','BetaAt'))).compact(ALL['GProduct'].template_source)
    assert 'GProductSteps(' in product['defined_statement']
    assert '6' in product['defined_statement']


def test_unit_is_a_shared_divisor_of_actual_gaussian_identity_six():
    reading=_FormulaCompactor(definition_closure(('GDvd',))).compact(ALL['GUnit'].template_source)
    assert reading['defined_statement']=='GDvd(z,6)'
    assert ALL['GUnit'].conceptual_dependencies==('GDvd',)


def test_matched_factors_preserve_literal_bounded_injective_surjective_permutation():
    definition=ALL['GMatchedFactors']
    source=permutation._matched(*definition.parameters,'independent_matched')
    assert parse_formula_in_context(source,list(definition.parameters))==definition.template_formula
    ancestors={item.name for item in definition_closure(('GMatchedFactors',))}
    assert {'PermutationPrefix','BoundedPrefix','InjectivePrefix','SurjectivePrefix','GFactorAssociateMatching','GAssociate','GUnit'}<=ancestors
    assert ALL['GFactorPermutation'].arity==8
    assert ALL['GMatchedFactors'].arity==7


@pytest.mark.parametrize('mutation',('cycle','unknown','duplicate_id','changed_ast'))
def test_invalid_additive_registry_fails_closed(mutation):
    selected=ALL['GProduct']
    if mutation=='cycle':
        selected=replace(selected,conceptual_dependencies=(selected.name,))
    elif mutation=='unknown':
        selected=replace(selected,conceptual_dependencies=('AssumedFactorizationOracle',))
    elif mutation=='duplicate_id':
        selected=replace(selected,stable_id='PD0001')
    else:
        selected=replace(selected,template_source='0=1')
    registries=tuple((name,tuple(selected if item.name==selected.name else item for item in definitions)) for name,definitions in graph.DEFAULT_REGISTRIES)
    with pytest.raises(graph.DefinitionGraphError):
        graph.reviewed_registry(registries)


@pytest.mark.parametrize('row',ROWS,ids=lambda item:item.name)
def test_every_gaussian_statement_has_an_exact_defined_roundtrip(row):
    compact=compact_formula_source(row.statement)
    assert compact.receipt.exact_ast_equivalence
    assert compact.expanded_source==row.statement
    assert ''.join(part.text for part in compact.parts)==compact.defined_source
    assert compact.receipt.free_names==()
    assert _LocalDefinedParser(compact.defined_source,ALL).parse()==parse_formula_in_context(row.statement,[])


@pytest.mark.parametrize('row',ROWS,ids=lambda item:item.name)
def test_every_local_proposition_has_an_exact_defined_roundtrip(row):
    for index,command in enumerate(row.script,1):
        reading=compact_tactic_command(command,index)
        assert reading.expanded_command==command and reading.line_number==index
        assert ''.join(part.text for part in reading.parts)==reading.defined_command
        if reading.proposition is not None:
            proposition=reading.proposition
            assert proposition.receipt.exact_ast_equivalence
            exact,names=parse_formula_with_names(proposition.expanded_source)
            parser=_LocalDefinedParser(proposition.defined_source,ALL)
            parser.free=list(names)
            assert parser.parse()==exact and tuple(parser.free)==names


def test_definition_graph_is_non_circular_and_keeps_proof_conclusions_out_of_data():
    closures={name:{item.name for item in definition_closure((name,))} for name in ('GDvd','GUnit','GIrreducible','GPrime','GGcd','GBezout','GProduct','GPrimeFactorization','GFactorPermutation')}
    assert 'GPrime' not in closures['GIrreducible']
    assert 'GIrreducible' not in closures['GPrime']
    assert {'GMul','ZPairAdd'}<=closures['GBezout']
    assert not {'GGcd','GPrime','GIrreducible','GPrimeFactorization'}&closures['GBezout']
    assert 'GDvd' in closures['GGcd'] and 'GBezout' not in closures['GGcd']
    assert {'GProductSteps','GProductStep','GMul','BetaAt'}<=closures['GProduct']
    assert not {'GPrime','GIrreducible','GAllPrime','GAllIrreducible','GPrimeFactorization','GFactorPermutation','GMatchedFactors'}&closures['GProduct']
    assert {'GUnit','GAllPrime','GPrime','GProduct','GMul'}<=closures['GPrimeFactorization']
    assert not {'GMatchedFactors','GFactorAssociateMatching','GFactorPermutation'}&closures['GPrimeFactorization']
    assert {'PermutationPrefix','GMatchedFactors','GFactorAssociateMatching','GAssociate'}<=closures['GFactorPermutation']
    assert 'GPrimeFactorization' not in closures['GFactorPermutation']
    assert all('UniquePrimeFactorization' not in name for name in ALL)


def test_generic_ring_prime_and_differently_encoded_factorization_are_not_aliased():
    assert graph.REVIEWED_BLUEPRINT_ALIASES is prior_graph.REVIEWED_BLUEPRINT_ALIASES
    assert not {'RingPrime','GaussianFactorization'}&ALL.keys()
    assert not {'RingPrime','GaussianFactorization'}&graph.REVIEWED_BLUEPRINT_ALIASES.keys()
    # This small planning fixture is independent of whether an unrelated
    # current atlas publication has already advanced from v28 to v29.  Its
    # required Convergent refinement contains the actual reviewed expansion,
    # not merely a marker bypassing the inherited semantic guard.
    convergent=PRIOR['Convergent']
    campaign={'schema':'constructive-grand-campaign-v1','nodes':[],'definitions':{
        'Convergent':{'parameters':list(convergent.parameters),'meaning':convergent.summary,
                      'expansion':convergent.template_source,'reviewed_definition_id':convergent.stable_id},
        'RingPrime':{'parameters':['R','p'],'meaning':'A prime element of an arbitrary encoded ring.','expansion':'The actual arbitrary ring operations determine primality.'},
        'GaussianFactorization':{'parameters':['z','u','s'],'meaning':'A hypothetical single-code factor word.','expansion':'The supplied word s and coefficient u encode a factorization of z.'},
    }}
    artifact=graph.build_definition_graph(campaign)
    names={item['blueprint_name'] for item in artifact['compatible_reviewed_matches']}
    assert 'RingPrime' not in names and 'GaussianFactorization' not in names
    assert artifact['reviewed_definition_count']==284


def test_inherited_planning_guard_is_not_bypassed_by_gaussian_extension():
    campaign=json.loads((ROOT/'book/_static/constructive-grand-campaign/campaign.json').read_text())
    campaign['definitions']['Convergent']={'parameters':['s','i','u','v'],'meaning':'An old planning convergent.','expansion':'u,v>0 are obtained by recurrences.'}
    with pytest.raises(graph.DefinitionGraphError,match='excludes 0/1'):
        graph.build_definition_graph(campaign)


@pytest.mark.parametrize('name,required',(
    ('gaussian_unit_iff_norm_one',('GNorm(','GUnit(')),
    ('gaussian_divides_decidable',('ZPairValid(','GDvd(')),
    ('gaussian_gcd_bezout_exists',('ZPairValid(','GGcd(','GBezout(')),
    ('gaussian_irreducible_iff_prime',('GIrreducible(','GPrime(')),
    ('gaussian_product_swap_last_invariant',('GProduct(','BetaAt(')),
    ('gaussian_prime_factorization_exists',('GPrimeFactorization(',)),
    ('gaussian_unique_prime_factorization',('GPrimeFactorization(','GMatchedFactors(')),
))
def test_principal_roots_have_short_exact_readings_with_visible_witnesses(name,required):
    row=next(item for item in ROWS if item.name==name)
    surface=compact_formula_source(row.statement).defined_source
    assert all(token in surface for token in required),surface
    assert len(surface)<1600
    if name=='gaussian_unique_prime_factorization':
        assert surface.count('∃')>=6
        assert surface.count('∀')>=5
        assert '=' in surface


def test_unknown_definition_closure_does_not_silently_expand_unreviewed_prose():
    with pytest.raises(ValueError,match='unknown or cyclic'):
        definition_closure(('GaussianFactorization',))
