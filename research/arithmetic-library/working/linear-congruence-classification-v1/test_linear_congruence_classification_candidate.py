"""Independent expanded contracts, arithmetic models, and actual HA rejection.

No Alpha import, successful proof mock, cached proof fixture, or admission.
Native cases must run only inside the original resource-bounded controller.
"""
from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import importlib
import importlib.util
from math import gcd
from pathlib import Path
import sys

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name
from peano_lab.library.finite_fold_surface import power_relation


HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'linear_congruence_classification_candidate.py'
SOURCE_SHA256 = '12b1a98ce830704485f1ea78475fba8b10e39031ffbef00b1b5dfc8ffdef7f47'
PROVIDERS = (
    ('linear_congruence_complete_candidate', 'make_linear_congruence_complete_candidate_theorems'),
    ('ha_generalized_crt_congruence_candidate', 'make_ha_generalized_crt_congruence_candidate_theorems'),
    ('finite_modular_set_candidate', 'make_finite_modular_set_candidate_theorems'),
    ('generalized_crt_compatibility_candidate', 'make_generalized_crt_compatibility_candidate_theorems'),
    ('fermat_endpoints_candidate', 'make_fermat_endpoint_candidate_theorems'),
)


def protected_modules():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(('peano_lab.library.editions', 'working_'))}


_before_import = protected_modules()
_loader = importlib.util.spec_from_file_location('working_linear_classification', SOURCE)
assert _loader is not None and _loader.loader is not None
candidate = importlib.util.module_from_spec(_loader)
_loader.loader.exec_module(candidate)
assert protected_modules().keys() == _before_import.keys()
assert all(protected_modules()[name] is module for name, module in _before_import.items())


@lru_cache(maxsize=1)
def rows():
    return candidate.make_linear_congruence_classification_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    result = dict(_specs_by_name())
    for module_name, factory_name in PROVIDERS:
        module = importlib.import_module('peano_lab.library.' + module_name)
        for row in getattr(module, factory_name)(TheoremSpec):
            if row.name in result:
                assert _closed_formula(result[row.name].statement) == _closed_formula(row.statement)
            else:
                result[row.name] = row
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


def Mod(m, a, b):
    return f'exists zz_mod_left zz_mod_right. ({a})+({m})*zz_mod_left=({b})+({m})*zz_mod_right'


def Lt(a, b):
    return f'exists zz_gap. zz_gap+S ({a})=({b})'


def Gcd(g, a, m):
    return f'(((exists zz_a. ({a})=({g})*zz_a) /\\ (exists zz_m. ({m})=({g})*zz_m)) /\\ forall zz_d. (exists zz_x. ({a})=zz_d*zz_x) -> (exists zz_y. ({m})=zz_d*zz_y) -> exists zz_z. ({g})=zz_d*zz_z)'


def And(*clauses):
    if len(clauses) == 1:
        return '(' + clauses[0] + ')'
    return '((' + clauses[0] + ') /\\ (' + And(*clauses[1:]) + '))'


def Iff(a, b):
    return And('(' + a + ') -> (' + b + ')', '(' + b + ') -> (' + a + ')')


def Contract(parameters, premises, conclusion):
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join('(' + c + ')' for c in (*premises, conclusion))


BASE = ('a', 'm', 'g', 'A', 'M')
ASSUMPTIONS = ('~(m=0)', Gcd('g', 'a', 'm'), 'a=g*A', 'm=g*M')
NAMES = (
    'mod_eq_cancel_gcd_cofactor',
    'linear_congruence_solution_class_iff_reduced_modulus',
    'linear_congruence_reduced_representative_exists',
    'linear_congruence_progression_bound_iff',
    'linear_congruence_bounded_residue_parametrized',
    'linear_congruence_bounded_parameter_unique',
    'linear_congruence_bounded_solutions_parametrized',
    'linear_congruence_exact_bounded_enumeration_exists',
    'linear_congruence_zero_modulus_nonzero_coefficient_unique',
    'linear_congruence_zero_modulus_zero_coefficient_iff',
    'linear_congruence_modulus_one_bounded_iff_zero',
    'fermat_little_all_inputs',
)
METRICS = ((140,32),(78,34),(92,39),(89,28),(108,25),(44,27),
           (103,36),(94,36),(30,17),(28,13),(51,22),(104,30))


def Param():
    return 'exists t. ' + And(Lt('t', 'g'), 'x=r+M*t')


def independent_contracts():
    enumeration = 'exists r. ' + And(Lt('r', 'M'), Mod('m', 'a*r', 'b'),
        'forall x. ' + Iff(And(Lt('x', 'm'), Mod('m', 'a*x', 'b')), Param()),
        'forall t u. (' + Lt('t', 'g') + ') -> (' + Lt('u', 'g') + ') -> (r+M*t=r+M*u) -> t=u')
    return (
        (BASE+('x','y'), ASSUMPTIONS, Iff(Mod('m','a*x','a*y'),Mod('M','x','y'))),
        (BASE+('b','r','x'), (*ASSUMPTIONS,Mod('m','a*r','b')), Iff(Mod('m','a*x','b'),Mod('M','x','r'))),
        (BASE+('b',), (*ASSUMPTIONS,'exists zz_q. b=g*zz_q'), 'exists r. '+And(Lt('r','M'),Mod('m','a*r','b'))),
        (('M','g','r','t'), (Lt('r','M'),), Iff(Lt('r+M*t','g*M'),Lt('t','g'))),
        (('M','g','r','x'), (Lt('r','M'),), Iff(And(Lt('x','g*M'),Mod('M','x','r')),Param())),
        (('M','r','x','t','u'), ('~(M=0)','x=r+M*t','x=r+M*u'), 't=u'),
        (BASE+('b','r','x'), (*ASSUMPTIONS,Lt('r','M'),Mod('m','a*r','b')), Iff(And(Lt('x','m'),Mod('m','a*x','b')),Param())),
        (BASE+('b',), (*ASSUMPTIONS,'exists zz_q. b=g*zz_q'), enumeration),
        (('a','b','x','y'), ('~(a=0)',Mod('0','a*x','b'),Mod('0','a*y','b')), 'x=y'),
        (('b','x'), (), Iff(Mod('0','0*x','b'),'b=0')),
        (('a','b','x'), (), Iff(And(Lt('x','1'),Mod('1','a*x','b')),'x=0')),
        (('p','a','A'), ('(~(p=1) /\\ forall zz_c zz_e. p=zz_c*zz_e -> zz_c=1 \\/ zz_e=1)',
            power_relation('a','p','A',tag='independent_fermat_power')), Mod('p','A','a')),
    )


@pytest.mark.parametrize('index', range(len(NAMES)), ids=NAMES)
def test_exact_independently_expanded_contract(index):
    pars, premises, conclusion = independent_contracts()[index]
    assert _closed_formula(rows()[index].statement) == _closed_formula(Contract(pars, premises, conclusion))


def test_exact_inventory_order_and_no_unproved_dependency_gap():
    assert tuple(row.name for row in rows()) == NAMES
    core = provider_core()
    available = set(core) - set(NAMES)
    for row in rows():
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        available.add(row.name)


def test_original_fermat_candidate_is_preserved_in_all_fields():
    module = importlib.import_module('peano_lab.library.fermat_endpoints_candidate')
    assert sha256(Path(module.__file__).read_bytes()).hexdigest() == 'cfbf54b85c2c64393603e34186f5b34866c6c8062301117443155b617e7a6c9d'
    original = next(row for row in module.make_fermat_endpoint_candidate_theorems(TheoremSpec) if row.name == NAMES[-1])
    assert rows()[-1] == original
    assert original.script and original.dependencies


def test_source_has_no_registry_mutation_or_edition_import():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    tree = ast.parse(SOURCE.read_bytes())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or '').startswith(('peano_lab.library.editions', 'working_'))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {'setrlimit','write_text','write_bytes','exec_module','register'}
    assert 'sys.modules' not in SOURCE.read_text()
    assert all(not any(token in command.lower() for token in ('admit','sorry','dne','by_cases')) for row in rows() for command in row.script)


def test_standalone_count_endpoint_constructs_representative_and_preserves_all_parameters():
    pars, premises, result = independent_contracts()[7]
    assert pars == BASE+('b',) and len(premises) == 5
    assert result.startswith('exists r.') and 'forall x.' in result and 'forall t u.' in result
    assert 'linear_congruence_reduced_representative_exists' in rows()[7].dependencies
    assert 'linear_congruence_bounded_parameter_unique' in rows()[7].dependencies
    assert not any(result == premise for premise in premises)


def mod(m, a, b):
    return a == b if m == 0 else a % m == b % m


def witnesses(m, a, b):
    """Actual balanced witnesses, not just a remainder assertion."""
    assert mod(m,a,b)
    if m == 0:
        return (0,0)
    difference = (b-a)//m
    return (difference,0) if difference >= 0 else (0,-difference)


@pytest.mark.parametrize('m', range(1,11))
@pytest.mark.parametrize('a', range(8))
def test_actual_cofactors_cancellation_class_and_exact_cardinality_model(m,a):
    g = gcd(a,m); A,M = a//g,m//g
    assert a==g*A and m==g*M and gcd(A,M)==1 and g>0 and M>0
    for x in range(2*m+2):
        for y in range(2*m+2):
            assert mod(m,a*x,a*y)==mod(M,x,y)
    for b in range(2*m+1):
        solutions = [x for x in range(m) if mod(m,a*x,b)]
        assert bool(solutions)==(b%g==0)
        if not solutions:
            continue
        r = solutions[0] % M
        assert r<M and mod(m,a*r,b)
        u,v=witnesses(m,a*r,b); assert a*r+m*u==b+m*v
        indexed = [r+M*t for t in range(g)]
        assert indexed==solutions and len(set(indexed))==g
        for x in range(2*m+2):
            assert mod(m,a*x,b)==mod(M,x,r)
            indices=[t for t in range(g) if x==r+M*t]
            assert (x<m and mod(m,a*x,b))==bool(indices)
            assert len(indices)<=1


@pytest.mark.parametrize('M',range(1,7))
@pytest.mark.parametrize('g',range(7))
def test_progression_model_including_empty_parameter_interval(M,g):
    for r in range(M):
        for t in range(g+3):
            assert (r+M*t<g*M)==(t<g)
        for x in range(g*M+4):
            ts=[t for t in range(g) if x==r+M*t]
            assert (x<g*M and mod(M,x,r))==bool(ts)
            assert len(ts)<=1


@pytest.mark.parametrize('a',range(8))
def test_zero_and_one_moduli_are_not_falsely_bounded_or_divided(a):
    for b in range(12):
        zero=[x for x in range(20) if mod(0,a*x,b)]
        if a:
            assert len(zero)<=1
        else:
            assert zero==(list(range(20)) if b==0 else [])
        assert [x for x in range(1) if mod(1,a*x,b)]==[0]
        for x in range(20):
            assert (x<1 and mod(1,a*x,b))==(x==0)


@pytest.mark.parametrize('p',(2,3,5,7))
@pytest.mark.parametrize('a',range(9))
def test_fermat_all_inputs_includes_zero_and_multiples(p,a):
    value=a**p
    u,v=witnesses(p,value,a)
    assert value+p*u==a+p*v


@pytest.mark.parametrize('bad',('cancel_original_modulus','drop_gcd','drop_reference_bound','zero_step_injective','count_at_zero','omit_solution_reference'))
def test_independent_false_strengthening_counterexamples(bad):
    if bad=='cancel_original_modulus':
        assert mod(6,2*0,2*3) and not mod(6,0,3)
    elif bad=='drop_gcd':
        assert 6==1*6 and 2==1*2 and mod(6,2*0,2*3) and not mod(6,0,3)
    elif bad=='drop_reference_bound':
        assert 4+2*0<3*2 and not 4+2*2<3*2
    elif bad=='zero_step_injective':
        assert 2+0*0==2+0*1 and 0!=1
    elif bad=='count_at_zero':
        assert all(mod(0,0*x,0) for x in range(20)) and not any(x<0 for x in range(20))
    else:
        assert mod(3,0,0) and not mod(6,2*0,2)


@pytest.mark.parametrize('index',range(len(NAMES)),ids=NAMES)
def test_native_body(index):
    row=rows()[index]
    receipt=replay_candidate_bodies((row,),core=body_core())[0]
    assert receipt.name==row.name and receipt.command_count==len(row.script)
    assert receipt.dependency_count==len(row.dependencies)
    assert 0<receipt.proof_objects<=receipt.proof_nodes and receipt.proof_depth<=256
    assert (receipt.proof_nodes,receipt.proof_depth)==METRICS[index]


@pytest.mark.parametrize('index',range(len(NAMES)),ids=NAMES)
@pytest.mark.parametrize('mutation',('false_conclusion','missing_body','truncated_body'))
def test_native_false_or_incomplete_body(index,mutation):
    row=rows()[index]; pars,premises,_=independent_contracts()[index]
    changed=replace(row,statement=Contract(pars,premises,'0=1')) if mutation=='false_conclusion' else replace(row,script=() if mutation=='missing_body' else row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=body_core())


EDGES=tuple((i,dep) for i,row in enumerate(rows()) for dep in row.dependencies)


@pytest.mark.parametrize('index,dependency',EDGES,ids=tuple(f'row{i:02d}-{d}' for i,d in EDGES))
def test_native_removed_dependency(index,dependency):
    row=rows()[index]
    changed=replace(row,dependencies=tuple(d for d in row.dependencies if d!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=body_core())


@pytest.mark.parametrize('index,dependency',EDGES,ids=tuple(f'row{i:02d}-{d}' for i,d in EDGES))
def test_native_poisoned_dependency(index,dependency):
    core=body_core(); core[dependency]=replace(core[dependency],statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],),core=core)


PREMISES=tuple((i,j) for i,(_,premises,_) in enumerate(independent_contracts()) for j in range(len(premises)))


@pytest.mark.parametrize('index,position',PREMISES,ids=tuple(f'row{i:02d}-premise{j}' for i,j in PREMISES))
def test_native_removed_input_clause(index,position):
    pars,premises,result=independent_contracts()[index]
    changed=replace(rows()[index],statement=Contract(pars,premises[:position]+premises[position+1:],result))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=body_core())
