"""Independent source/model checks and actual original conditional HA replays.

The exact append-step statement supplies only a typed dependency, never a
successful checker result. No metric or numerical model can authorize a body
or admission: every positive test below performs the actual original replay.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING = HERE.parent
LIBRARY = ROOT/'peano-lab/py/peano_lab/library'
SOURCE = HERE/'prime_field_polynomial_associativity_induction_candidate.py'
SOURCE_SHA256 = '8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c'
STEP_PATH = WORKING/'prime-field-associativity-step-v1/prime_field_polynomial_associativity_step_candidate.py'
STEP_SOURCE_SHA256 = 'dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1'
STEP_NAME = 'prime_field_polynomial_convolution_associativity_append_step'
STEP_STATEMENT_SHA256 = 'f2d971514a76d10991d99754cdb81e84b6096f8fbdc24e7dfd0b6a580dbddaa0'
ORACLE_PATH = WORKING/'prime-field-append-v1/test_prime_field_polynomial_append_candidate.py'
ORACLE_SHA256 = '0c554b05b2c7e2c40e3b0e8044160379a3284bb173e48d59d77def0cad4272aa'
PRIVATE_NAMES = ('working_associativity_induction_candidate','working_associativity_induction_oracle',
                 'working_associativity_induction_unproved_step','working_append_candidate',
                 'working_append_shift_provider','working_append_scalar_provider')


def protected_bindings():
    return {name:value for name,value in sys.modules.items()
            if name.startswith('peano_lab.library.editions_v') or name in PRIVATE_NAMES}


def load_file(name,path):
    before = protected_bindings()
    specification = importlib.util.spec_from_file_location(name,path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key,value in before.items())
    return module


assert sha256(ORACLE_PATH.read_bytes()).hexdigest() == ORACLE_SHA256
oracle = load_file(PRIVATE_NAMES[1],ORACLE_PATH)
candidate = load_file(PRIVATE_NAMES[0],SOURCE)
PROVIDER_PINS = {**oracle.PROVIDER_PINS,
    'finite_fold_theorems.py':'e69c41198d25aa0cba3bbf8415344050b28ecb8d058c1cd8d98415e0db09178c',
    'finite_fold_surface.py':'95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30'}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_associativity_induction_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def exact_unproved_step():
    assert sha256(STEP_PATH.read_bytes()).hexdigest() == STEP_SOURCE_SHA256
    module = load_file(PRIVATE_NAMES[2],STEP_PATH)
    specifications = module.make_prime_field_polynomial_associativity_step_candidate_theorems(TheoremSpec)
    selected = [row for row in specifications if row.name == STEP_NAME]
    assert len(selected) == 1 and sha256(selected[0].statement.encode()).hexdigest() == STEP_STATEMENT_SHA256
    return selected[0]


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    from peano_lab.library.prime_field_polynomial_representation_candidate import make_prime_field_polynomial_representation_candidate_theorems
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems

    for name,digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY/name).read_bytes()).hexdigest() == digest
    core = {row.name:row for row in THEOREMS}
    for factory in (make_prime_field_arithmetic_candidate_theorems,make_prime_field_polynomial_candidate_theorems,
                    make_prime_field_polynomial_convolution_candidate_theorems,
                    make_prime_field_polynomial_representation_candidate_theorems,make_matrix_rank_finite_coding_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in core or core[row.name] == row
            core[row.name] = row
    step = exact_unproved_step()
    assert step.name not in core
    core[step.name] = step  # Exact type only; this line is not proof acceptance.
    return core


def body_core():
    core = dict(provider_core())
    for row in rows():
        assert row.name not in core
        core[row.name] = row
    return core


A,B,P = ('ab','ac','L'),('bb','bc','M'),('pb','pc','N')
C,Q,R,S = ('cb','cc','J'),('qb','qc','K'),('rb','rc','U'),('sb','sc','V')
Convolution,Equivalent = oracle.Convolution,oracle.Equivalent
BASE_PARAMETERS = ('p',*A,*B,*P,'cb','cc',*Q,*R,*S)
PARAMETERS = ('p',*A,*B,*P,*C,*Q,*R,*S)


def independent_contracts():
    empty = ('cb','cc','0')
    return (
        (BASE_PARAMETERS,('~(p=0)',Convolution('p',*B,*empty,*Q),Convolution('p',*P,*empty,*R),
                          Convolution('p',*A,*Q,*S)),Equivalent(*R,*S)),
        (PARAMETERS,(oracle.Prime('p'),Convolution('p',*A,*B,*P),Convolution('p',*B,*C,*Q),
                     Convolution('p',*P,*C,*R),Convolution('p',*A,*Q,*S)),Equivalent(*R,*S)),
    )


NAMES = ('prime_field_polynomial_nested_empty_right_equivalent',
         'prime_field_polynomial_convolution_associative_equivalent')
COMMANDS = (104,283)
METRICS = ((122,49),(336,123))  # Actual observations; positive cases must independently replay both bodies.


def test_exact_draft_source_and_source_order_dependencies():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert tuple(len(row.script) for row in rows()) == COMMANDS
    assert tuple(len(row.dependencies) for row in rows()) == (5,8)
    core = provider_core()
    for index,row in enumerate(rows()):
        assert row.name not in core and len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(core) | set(NAMES[:index])
    assert STEP_NAME in rows()[1].dependencies and STEP_NAME not in rows()[0].dependencies


@pytest.mark.parametrize('index',range(2),ids=('row00','row01'))
def test_independent_fully_expanded_contract(index):
    parameters,premises,conclusion = independent_contracts()[index]
    oracle.same_ast(_closed_formula(rows()[index].statement),_closed_formula(oracle.contract(parameters,premises,conclusion)))
    assert len(set(parameters)) == len(parameters)


def test_empty_base_has_no_unnecessary_AB_or_prime_premise():
    _,premises,_ = independent_contracts()[0]
    assert len(premises) == 4 and premises[0] == '~(p=0)'
    assert Convolution('p',*A,*B,*P) not in premises
    assert oracle.Prime('p') not in premises


def test_full_principal_has_four_actual_products_and_no_equality_premise():
    _,premises,conclusion = independent_contracts()[1]
    assert len(premises) == 5 and premises[0] == oracle.Prime('p')
    assert premises[1:] == (Convolution('p',*A,*B,*P),Convolution('p',*B,*C,*Q),
                            Convolution('p',*P,*C,*R),Convolution('p',*A,*Q,*S))
    assert conclusion not in premises
    assert not any(part in ('U=V','U=S N','K=S M') for part in premises)


def test_actual_induction_predicate_quantifies_codes_and_all_output_triples_after_length():
    declarations = [command.removeprefix('have hall : ') for command in rows()[1].script if command.startswith('have hall : ')]
    assert len(declarations) == 1
    inner_parameters = ('j','db','dc','qxb','qxc','k','rxb','rxc','u','sxb','sxc','v')
    inner_c = ('db','dc','j')
    inner_q,inner_r,inner_s = ('qxb','qxc','k'),('rxb','rxc','u'),('sxb','sxc','v')
    expected = oracle.contract(inner_parameters,(Convolution('p',*B,*inner_c,*inner_q),
        Convolution('p',*P,*inner_c,*inner_r),Convolution('p',*A,*inner_q,*inner_s)),Equivalent(*inner_r,*inner_s))
    prefix = 'forall '+' '.join(('p',*A,*B,*P))+'. '
    oracle.same_ast(_closed_formula(prefix+declarations[0]),_closed_formula(prefix+expected))
    assert rows()[1].script.count('induction j') == 1
    actual_ih = tuple(command for command in rows()[1].script if command.startswith('specialize IH '))
    assert actual_ih == tuple('specialize IH ('+term+')' for term in ('db','dc','x2','x3','x1','x5','x6','x4','x8','x9','x7'))


def test_exact_step_type_is_explicitly_not_a_saved_success_record():
    step = exact_unproved_step()
    assert type(step) is TheoremSpec and step.name == STEP_NAME
    assert sha256(step.statement.encode()).hexdigest() == STEP_STATEMENT_SHA256
    assert not hasattr(step,'proof_verified') and not hasattr(step,'live_capability')
    assert not any('receipt' in command or 'audit.json' in command for row in rows() for command in row.script)


def test_candidate_has_only_canonical_graph_imports_and_no_alias_or_admission_API():
    tree = ast.parse(SOURCE.read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node,(ast.Import,ast.ImportFrom))]
    assert all(isinstance(node,ast.ImportFrom) and node.level == 0 for node in imports)
    assert {node.module for node in imports} == {
        '__future__','typing','peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate','peano_lab.library.prime_field_polynomial_convolution_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate',
    }
    assert not any(isinstance(node,ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert candidate.__all__ == ['make_prime_field_polynomial_associativity_induction_candidate_theorems']
    assert not any(name.endswith('_relation') for name in vars(candidate))


@pytest.mark.parametrize('name',('peano_lab.library.editions_v_associativity_induction_guard',*PRIVATE_NAMES))
def test_explicit_file_loading_preserves_preexisting_module_identity(name,monkeypatch):
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules,name,marker)
    before = protected_bindings()
    module = load_file(PRIVATE_NAMES[0],SOURCE)
    models = load_file(PRIVATE_NAMES[1],ORACLE_PATH)
    step = load_file(PRIVATE_NAMES[2],STEP_PATH)
    assert Path(module.__file__) == SOURCE and Path(models.__file__) == ORACLE_PATH and Path(step.__file__) == STEP_PATH
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key,value in before.items())
    assert sys.modules[name] is marker


def test_actual_provider_bytes_and_paths_are_unchanged():
    provider_core()
    for filename,digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY/filename).read_bytes()).hexdigest() == digest
        name = 'peano_lab.library.'+filename.removesuffix('.py')
        if name in sys.modules:
            assert Path(sys.modules[name].__file__).resolve() == (LIBRARY/filename).resolve()
    assert sha256(STEP_PATH.read_bytes()).hexdigest() == STEP_SOURCE_SHA256
    assert sha256(ORACLE_PATH.read_bytes()).hexdigest() == ORACLE_SHA256


def test_local_novelty_against_selected_types_only():
    from peano_lab.library.formula_dag import FormulaArena

    core = body_core()
    selected = set(NAMES) | {name for row in rows() for name in row.dependencies}
    encoded = {name:FormulaArena().freeze(_closed_formula(core[name].statement)).to_json() for name in selected}
    for name in NAMES:
        assert all(encoded[name] != value for other,value in encoded.items() if other != name)


@pytest.mark.parametrize('index',range(2),ids=('row00','row01'))
def test_actual_original_ha_body_and_exact_nodes_depth(index):
    assert METRICS[index] is not None  # No successful fixture may bypass this gate.
    row = rows()[index]
    receipt = replay_candidate_bodies((row,),core=body_core())[0]
    assert receipt.name == row.name and (receipt.proof_nodes,receipt.proof_depth) == METRICS[index]
    assert (receipt.dependency_count,receipt.command_count) == (len(row.dependencies),len(row.script))
    assert 0 < receipt.proof_objects <= receipt.proof_nodes


@pytest.mark.parametrize('index',range(2),ids=('row00','row01'))
@pytest.mark.parametrize('mutation',('false_conclusion','missing_body','truncated_body'))
def test_false_or_incomplete_body_is_rejected(index,mutation):
    row = rows()[index]
    parameters,premises,_ = independent_contracts()[index]
    changed = replace(row,statement=oracle.contract(parameters,premises,'0=1')) if mutation == 'false_conclusion' else replace(
        row,script=() if mutation == 'missing_body' else row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=body_core())


EDGES = tuple((index,dependency) for index,row in enumerate(rows()) for dependency in row.dependencies)
EDGE_IDS = tuple(f'row{index:02d}-edge{position:02d}' for position,(index,_) in enumerate(EDGES))


@pytest.mark.parametrize('index,dependency',EDGES,ids=EDGE_IDS)
def test_each_removed_dependency_is_rejected(index,dependency):
    row = rows()[index]
    changed = replace(row,dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=body_core())


@pytest.mark.parametrize('index,dependency',EDGES,ids=EDGE_IDS)
def test_each_poisoned_dependency_is_rejected(index,dependency):
    core = body_core()
    core[dependency] = replace(core[dependency],statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],),core=core)


CHANGED = tuple((index,position,oracle.contract(parameters,premises[:position]+premises[position+1:],conclusion))
    for index,(parameters,premises,conclusion) in enumerate(independent_contracts()) for position in range(len(premises)))


@pytest.mark.parametrize('index,position,statement',CHANGED,ids=tuple(f'row{i:02d}-missing-premise-{position}' for i,position,_ in CHANGED))
def test_fixed_body_rejects_altered_guards_or_other_claim(index,position,statement):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index],statement=statement),),core=body_core())


def encoded(values,variant):
    values = tuple(values)
    return oracle.encode_beta(values+(101+variant,107+variant),variant),len(values)


def actual_product(p,left,right,variant):
    a,L = left
    b,M = right
    assert p > 0 and all(value < p for value in oracle.prefix(a,L)+oracle.prefix(b,M))
    values = oracle.product_values(p,oracle.prefix(a,L),oracle.prefix(b,M))
    result,N = encoded(values,variant)
    assert N == (0 if L == 0 or M == 0 else L+M-1)
    for i in range(N+3):
        residue,diagonal,trace,total = oracle.actual_coefficient_witness(p,a,L,b,M,i,variant+1)
        assert residue == total % p and 0 <= residue < p
        assert residue == (oracle.beta(result,i) if i < N else 0)
        assert oracle.beta(trace,0) == 0 and oracle.beta(diagonal,i+1) == 101
    return result,N


TRIPLES = (((),(),()),((),(1,),(1,2)),((1,),(),(2,)),((1,),(1,),()),
           ((1,),(1,),(1,)),((1,0),(0,1),(1,)),((0,1),(1,0),(0,2,1)),
           ((1,2),(2,1),(2,0)),((1,1),(1,1),(1,1)))


@pytest.mark.parametrize('values',TRIPLES)
@pytest.mark.parametrize('p',(1,2,4,5))
def test_actual_empty_base_models_at_nonzero_composite_and_unit_moduli(values,p):
    Adata,Bdata,Pdata = (encoded(tuple(value % p for value in row),index+1) for index,row in enumerate(values))
    empty = ((997,13),0)
    Qdata = actual_product(p,Bdata,empty,5)
    Rdata = actual_product(p,Pdata,empty,7)
    Sdata = actual_product(p,Adata,Qdata,9)
    assert Qdata[1] == Rdata[1] == Sdata[1] == 0
    assert oracle.equivalent(*Rdata,*Sdata) and Rdata[0] != Sdata[0]


@pytest.mark.parametrize('values',TRIPLES)
@pytest.mark.parametrize('p',(2,3,5))
def test_actual_four_product_models_of_the_full_proposed_contract(values,p):
    Adata,Bdata,Cdata = (encoded(tuple(value % p for value in row),index+1) for index,row in enumerate(values))
    Pdata = actual_product(p,Adata,Bdata,5)
    Qdata = actual_product(p,Bdata,Cdata,7)
    Rdata = actual_product(p,Pdata,Cdata,9)
    Sdata = actual_product(p,Adata,Qdata,11)
    assert oracle.equivalent(*Rdata,*Sdata) and Rdata[0] != Sdata[0]


@pytest.mark.parametrize('values',TRIPLES)
@pytest.mark.parametrize('p',(2,3,5))
def test_model_induction_changes_codes_and_reconstructs_every_prefix_product(values,p):
    Adata,Bdata,Cdata = (encoded(tuple(value % p for value in row),index+1) for index,row in enumerate(values))
    Pdata = actual_product(p,Adata,Bdata,5)
    previous = None
    for length in range(Cdata[1]+1):
        prefix = (Cdata[0],length)
        Qdata = actual_product(p,Bdata,prefix,7+6*length)
        Rdata = actual_product(p,Pdata,prefix,9+6*length)
        Sdata = actual_product(p,Adata,Qdata,11+6*length)
        assert oracle.equivalent(*Rdata,*Sdata)
        if previous is not None:
            old_prefix,old_q,old_r,old_s = previous
            scalar = oracle.beta(Cdata[0],length-1)
            assert scalar < p
            assert oracle.prefix(old_prefix[0],old_prefix[1]) == oracle.prefix(prefix[0],length-1)
            assert old_q[0] != Qdata[0] and old_r[0] != Rdata[0] and old_s[0] != Sdata[0]
            assert oracle.equivalent(*old_r,*old_s)
        previous = prefix,Qdata,Rdata,Sdata


def test_base_does_not_assume_the_unneeded_AB_product():
    Adata,Bdata,Pdata = encoded((1,),1),encoded((1,),3),encoded((2,),5)
    assert not oracle.equivalent(*actual_product(5,Adata,Bdata,7),*Pdata)
    empty = ((42,0),0)
    Qdata = actual_product(5,Bdata,empty,9)
    Rdata = actual_product(5,Pdata,empty,11)
    Sdata = actual_product(5,Adata,Qdata,13)
    assert oracle.equivalent(*Rdata,*Sdata)


def test_first_positive_prefix_does_not_have_successor_product_length():
    Adata,Bdata,Cdata = encoded((1,1),1),encoded((1,2,1),3),encoded((1,),5)
    Pdata = actual_product(5,Adata,Bdata,7)
    old_q = actual_product(5,Bdata,(Cdata[0],0),9)
    old_r = actual_product(5,Pdata,(Cdata[0],0),11)
    new_q = actual_product(5,Bdata,Cdata,13)
    new_r = actual_product(5,Pdata,Cdata,15)
    assert old_q[1] == old_r[1] == 0
    assert new_q[1] == 3 and new_r[1] == 4
    assert new_q[1] != old_q[1]+1 and new_r[1] != old_r[1]+1


def test_characteristic_two_evaluation_agreement_cannot_supply_formal_induction_hypothesis():
    square,linear = (1,0,0),(1,0)
    def evaluate(values,x):
        value = 0
        for a in values:
            value = (value*x+a) % 2
        return value
    assert all(evaluate(square,x) == evaluate(linear,x) for x in range(2))
    assert not oracle.equivalent(*encoded(square,1),*encoded(linear,3))


def test_no_field_bound_or_relation_extends_past_the_actual_prefix():
    a = encoded((1,),17)
    b = encoded((1,),19)
    product = actual_product(2,a,b,23)
    assert oracle.beta(a[0],a[1]) == 118 and oracle.beta(b[0],b[1]) == 120
    assert oracle.beta(product[0],product[1]) == 124
    assert oracle.beta(product[0],0) == 1
