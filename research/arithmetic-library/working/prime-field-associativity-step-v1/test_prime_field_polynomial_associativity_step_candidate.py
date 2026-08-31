"""Independent actual-witness contracts/models and original conditional HA.

The immutable append test supplies only its independently expanded native
graphs and integer beta-model utilities. Its tests and proof fixtures are not
run or used as acceptance evidence. Actual dependency statements come from
canonical factories and four exact working source files, without package
aliases, Alpha imports, saved receipts, or successful proof-checker doubles.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
import gc
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
LIBRARY = ROOT / 'peano-lab/py/peano_lab/library'
SOURCE = HERE / 'prime_field_polynomial_associativity_step_candidate.py'
SOURCE_SHA256 = 'dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1'
FROZEN_PINS = {
    'prime-field-shift-v1/prime_field_polynomial_shift_candidate.py': '325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b',
    'prime-field-shift-v1/test_prime_field_polynomial_shift_candidate.py': '0622fb92978fcf028842aa4d9822ef61213642eb852e080f7c787dcea4bb395f',
    'prime-field-scalar-v1/prime_field_polynomial_scalar_convolution_candidate.py': 'e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e',
    'prime-field-scalar-v1/test_prime_field_polynomial_scalar_convolution_candidate.py': '881452ada0b5dc3be7d6cd00ee31dc08075b07f51d83595ee60f8cfb40d4c6e5',
    'prime-field-append-v1/prime_field_polynomial_append_candidate.py': '271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042',
    'prime-field-append-v1/test_prime_field_polynomial_append_candidate.py': '0c554b05b2c7e2c40e3b0e8044160379a3284bb173e48d59d77def0cad4272aa',
    'prime-field-shift-equivalence-v1/prime_field_polynomial_shift_equivalence_candidate.py': '8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068',
    'prime-field-shift-equivalence-v1/test_prime_field_polynomial_shift_equivalence_candidate.py': '9ed90ddc4680f8c2c3d04e2e3a76f8cffda4bfb95b1b83ab391d134c7fe5ab18',
}
PRIVATE_NAMES = (
    'working_associativity_step_candidate', 'working_associativity_step_oracle',
    'working_associativity_step_shift', 'working_associativity_step_scalar',
    'working_associativity_step_append', 'working_associativity_step_shift_equivalence',
    'working_append_candidate', 'working_append_shift_provider', 'working_append_scalar_provider',
)


def protected_bindings():
    return {name:value for name,value in sys.modules.items()
            if name.startswith('peano_lab.library.editions_v') or name in PRIVATE_NAMES}


def load_file(name, path):
    before = protected_bindings()
    specification = importlib.util.spec_from_file_location(name,path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key,value in before.items())
    return module


ORACLE_PATH = 'prime-field-append-v1/test_prime_field_polynomial_append_candidate.py'
assert sha256((WORKING/ORACLE_PATH).read_bytes()).hexdigest() == FROZEN_PINS[ORACLE_PATH]
oracle = load_file(PRIVATE_NAMES[1],WORKING/ORACLE_PATH)
candidate = load_file(PRIVATE_NAMES[0],SOURCE)
PROVIDER_PINS = {**oracle.PROVIDER_PINS,
    'prime_field_polynomial_convolution_congruence_candidate.py': 'effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70'}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_associativity_step_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def working_factories():
    for path,digest in FROZEN_PINS.items():
        assert sha256((WORKING/path).read_bytes()).hexdigest() == digest
    result = []
    for name,path,factory in (
        (PRIVATE_NAMES[2],'prime-field-shift-v1/prime_field_polynomial_shift_candidate.py','make_prime_field_polynomial_shift_candidate_theorems'),
        (PRIVATE_NAMES[3],'prime-field-scalar-v1/prime_field_polynomial_scalar_convolution_candidate.py','make_prime_field_polynomial_scalar_convolution_candidate_theorems'),
        (PRIVATE_NAMES[4],'prime-field-append-v1/prime_field_polynomial_append_candidate.py','make_prime_field_polynomial_append_candidate_theorems'),
        (PRIVATE_NAMES[5],'prime-field-shift-equivalence-v1/prime_field_polynomial_shift_equivalence_candidate.py','make_prime_field_polynomial_shift_equivalence_candidate_theorems'),
    ):
        result.append(getattr(load_file(name,WORKING/path),factory))
    return tuple(result)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    from peano_lab.library.prime_field_polynomial_representation_candidate import make_prime_field_polynomial_representation_candidate_theorems
    from peano_lab.library.prime_field_polynomial_distributivity_candidate import make_prime_field_polynomial_distributivity_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_padding_candidate import make_prime_field_polynomial_convolution_padding_candidate_theorems
    from peano_lab.library.prime_field_polynomial_equivalence_candidate import make_prime_field_polynomial_equivalence_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_congruence_candidate import make_prime_field_polynomial_convolution_congruence_candidate_theorems
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems

    for filename,digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY/filename).read_bytes()).hexdigest() == digest
    core = {row.name:row for row in THEOREMS}
    factories = (
        make_prime_field_arithmetic_candidate_theorems, make_prime_field_polynomial_candidate_theorems,
        make_prime_field_polynomial_convolution_candidate_theorems, make_prime_field_polynomial_representation_candidate_theorems,
        make_prime_field_polynomial_distributivity_candidate_theorems, make_prime_field_polynomial_convolution_padding_candidate_theorems,
        make_prime_field_polynomial_equivalence_candidate_theorems, make_prime_field_polynomial_convolution_congruence_candidate_theorems,
        make_matrix_rank_finite_coding_candidate_theorems,*working_factories(),
    )
    for factory in factories:
        for row in factory(TheoremSpec):
            assert row.name not in core or core[row.name] == row
            core[row.name] = row
    return core


def body_core():
    core = dict(provider_core())
    for row in rows():
        assert row.name not in core
        core[row.name] = row
    return core


# Parameters and every premise are specified independently. The native graph
# oracle is the literal frozen, hand-expanded test code, not a source builder.
And,Prime,Equal,At = oracle.And,oracle.Prime,oracle.Equal,oracle.At
Shift,Scale,LeftPad,Add = oracle.Shift,oracle.Scale,oracle.LeftPad,oracle.Add
Convolution,Equivalent = oracle.Convolution,oracle.Equivalent
A,B,P,Q,R = ('ab','ac','L'),('bb','bc','M'),('pb','pc','N'),('qb','qc','K'),('rb','rc','T')
LEFT = ('ub','uc','vb','vc','UPb','UPc','VPb','VPc','zb','zc')
RIGHT = ('eb','ec','fb','fc','EPb','EPc','FPb','FPc','yb','yc')
OLD0,OLD1 = ('b0','c0','N0'),('b1','c1','N1')
ALIGN0 = ('u0b','u0c','v0b','v0c','UP0b','UP0c','VP0b','VP0c','z0b','z0c')
ALIGN1 = ('u1b','u1c','v1b','v1c','UP1b','UP1c','VP1b','VP1c','z1b','z1c')
C = ('cb','cc','J')
Q0,R0,S0 = ('q0b','q0c','K0'),('r0b','r0c','U0'),('s0b','s0c','V0')
Q1,R1,S1 = ('q1b','q1c','K1'),('r1b','r1c','U1'),('s1b','s1c','V1')


def Aligned(p,scalar,source,old,outputs):
    a,b,L = source
    c,d,N = old
    u,v,s,t,U,V,S,T,z,w = outputs
    return (Shift(c,d,N,u,v),Scale(p,scalar,a,b,s,t,L),
            LeftPad(u,v,'S '+N,L,U,V),LeftPad(s,t,L,'S '+N,S,T),
            Add(p,U,V,S,T,z,w,L+'+S '+N))


def independent_contracts():
    helper_parameters = ('p','c',*A,*B,*P,*Q,*R,*LEFT,'sb','sc','W',*RIGHT)
    helper_premises = (Prime('p'),Convolution('p',*A,*B,*P),Convolution('p',*A,*Q,*R),
        *Aligned('p','c',B,Q,LEFT),Convolution('p',*A,'zb','zc','M+S K','sb','sc','W'),
        *Aligned('p','c',P,R,RIGHT))
    comparison_parameters = ('p','c',*A,*OLD0,*OLD1,*ALIGN0,*ALIGN1)
    comparison_premises = (Prime('p'),Equivalent(*OLD0,*OLD1),
                          *Aligned('p','c',A,OLD0,ALIGN0),*Aligned('p','c',A,OLD1,ALIGN1))
    step_parameters = ('p',*A,*B,*P,*C,*Q0,*R0,*S0,'c','db','dc',*Q1,*R1,*S1)
    step_premises = (Prime('p'),Convolution('p',*A,*B,*P),Convolution('p',*B,*C,*Q0),
        Convolution('p',*P,*C,*R0),Convolution('p',*A,*Q0,*S0),Equivalent(*R0,*S0),
        Equal('cb','cc','db','dc','J'),At('db','dc','J','c'),
        Convolution('p',*B,'db','dc','S J',*Q1),Convolution('p',*P,'db','dc','S J',*R1),
        Convolution('p',*A,*Q1,*S1))
    return (
        (helper_parameters,helper_premises,Equivalent('sb','sc','W','yb','yc','N+S T')),
        (comparison_parameters,comparison_premises,Equivalent('z0b','z0c','L+S N0','z1b','z1c','L+S N1')),
        (step_parameters,step_premises,Equivalent(*R1,*S1)),
    )


NAMES = ('prime_field_polynomial_convolution_shift_scale_aligned_equivalent',
         'prime_field_polynomial_shift_scale_aligned_congruent',
         'prime_field_polynomial_convolution_associativity_append_step')
COMMANDS = (421,214,487)
METRICS = ((539,110),(229,72),(698,140))  # Observed from original conditional HA; every positive test replays it.


def test_exact_source_inventory_and_declared_dependency_topology():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert tuple(len(row.script) for row in rows()) == COMMANDS
    assert tuple(len(row.dependencies) for row in rows()) == (16,8,14)
    core = provider_core()
    for index,row in enumerate(rows()):
        assert row.name not in core and len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(core) | set(NAMES[:index])


@pytest.mark.parametrize('index',range(3),ids=('row00','row01','row02'))
def test_independent_fully_expanded_contract_and_clause_order(index):
    parameters,premises,conclusion = independent_contracts()[index]
    expected = oracle.contract(parameters,premises,conclusion)
    oracle.same_ast(_closed_formula(rows()[index].statement),_closed_formula(expected))
    assert len(set(parameters)) == len(parameters)
    assert len(premises) == (14,12,11)[index]


def test_step_contains_actual_old_hypothesis_not_its_desired_new_conclusion():
    _,premises,conclusion = independent_contracts()[2]
    assert premises[5] == Equivalent(*R0,*S0)
    assert conclusion == Equivalent(*R1,*S1) and conclusion not in premises
    assert tuple(premises[index] for index in (1,2,3,4,8,9,10)) == (
        Convolution('p',*A,*B,*P),Convolution('p',*B,*C,*Q0),Convolution('p',*P,*C,*R0),
        Convolution('p',*A,*Q0,*S0),Convolution('p',*B,'db','dc','S J',*Q1),
        Convolution('p',*P,'db','dc','S J',*R1),Convolution('p',*A,*Q1,*S1),
    )
    assert not any(part in ('K1=S K0','U1=S U0','V1=S V0') for part in premises)
    assert oracle.Lt('c','p') not in premises
    assert any(command == 'have hc : '+candidate._lt('c','p','append_step_scalar_bound') for command in rows()[2].script)


def test_step_keeps_each_intermediate_alignment_in_its_own_local_branch():
    script = rows()[2].script
    locations = {label:next(index for index,command in enumerate(script)
                            if command.startswith('have '+label+' : '))
                 for label in ('hYalign','hS_total','hZalign','hZlength','hAZ','hR_total','hY0align')}
    assert tuple(locations.values()) == tuple(sorted(locations.values()))
    parameters = (*independent_contracts()[2][0],'x',*(f'x{index}' for index in range(1,10)))
    prefix = 'forall '+' '.join(parameters)+'. '
    for label,output in (('hS_total',S1),('hR_total',R1)):
        local_formula = script[locations[label]].split(' : ',1)[1]
        oracle.same_ast(_closed_formula(prefix+local_formula),
                        _closed_formula(prefix+Equivalent(*output,'x8','x9','N+S V0')))
    left_branch = script[locations['hS_total']:locations['hR_total']]
    right_branch = script[locations['hR_total']:]
    assert sum(command.startswith('cases hYalign') for command in script[:locations['hS_total']]) == 14
    assert sum(command.startswith('cases hZalign') for command in left_branch) == 14
    assert not any(command.startswith('cases hY0align') for command in left_branch)
    assert sum(command.startswith('cases hY0align') for command in right_branch) == 14
    assert not any(command.startswith(('cases hZalign','cases hAZ','cases hZlength')) for command in right_branch)
    assert script[locations['hR_total']-2:locations['hR_total']] == ('exact hS_transport','exact hhelper_equal')
    assert not any('(x23)' in command or '(x30)' in command or '(x31)' in command or '(x32)' in command
                   for command in script)


def test_alignment_is_only_five_actual_existing_graphs_and_no_alias():
    parameters = ('p','c',*A,*P,*LEFT)
    prefix = 'forall '+' '.join(parameters)+'. '
    actual = candidate._aligned('p','c',A,P,LEFT,'independent')
    expected = Aligned('p','c',A,P,LEFT)
    assert len(actual) == len(expected) == 5
    for first,second in zip(actual,expected,strict=True):
        oracle.same_ast(_closed_formula(prefix+first),_closed_formula(prefix+second))
    tree = ast.parse(SOURCE.read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node,(ast.Import,ast.ImportFrom))]
    assert all(isinstance(node,ast.ImportFrom) and node.level == 0 for node in imports)
    assert {node.module for node in imports} == {
        '__future__','typing','peano_lab.library.prime_field_arithmetic_candidate',
        'peano_lab.library.prime_field_polynomial_candidate','peano_lab.library.prime_field_polynomial_convolution_candidate',
        'peano_lab.library.prime_field_polynomial_representation_candidate','peano_lab.library.prime_field_tables_candidate',
    }
    assert not any(isinstance(node,ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert candidate.__all__ == ['make_prime_field_polynomial_associativity_step_candidate_theorems']
    assert not any(name.endswith('_relation') for name in vars(candidate))
    assert all('gcd' not in name and 'bezout' not in name for name in NAMES)
    assert 'prime_field_polynomial_convolution_associative' not in NAMES


@pytest.mark.parametrize('name',('peano_lab.library.editions_v_associativity_step_guard',*PRIVATE_NAMES))
def test_explicit_file_loading_preserves_preexisting_module_identity(name,monkeypatch):
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules,name,marker)
    before = protected_bindings()
    loaded = load_file(PRIVATE_NAMES[0],SOURCE)
    models = load_file(PRIVATE_NAMES[1],WORKING/ORACLE_PATH)
    assert Path(loaded.__file__) == SOURCE and Path(models.__file__) == WORKING/ORACLE_PATH
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key,value in before.items())
    assert sys.modules[name] is marker


def test_actual_provider_paths_and_all_eight_frozen_companion_files():
    provider_core()
    for filename,digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY/filename).read_bytes()).hexdigest() == digest
        name = 'peano_lab.library.'+filename.removesuffix('.py')
        if name in sys.modules:
            assert Path(sys.modules[name].__file__).resolve() == (LIBRARY/filename).resolve()
    for path,digest in FROZEN_PINS.items():
        assert sha256((WORKING/path).read_bytes()).hexdigest() == digest


def test_local_novelty_against_selected_actual_types_only():
    from peano_lab.library.formula_dag import FormulaArena

    core = body_core()
    selected = set(NAMES) | {name for row in rows() for name in row.dependencies}
    encoded = {name:FormulaArena().freeze(_closed_formula(core[name].statement)).to_json() for name in selected}
    for name in NAMES:
        assert all(encoded[name] != value for other,value in encoded.items() if other != name)


@pytest.mark.parametrize('index',range(3),ids=('row00','row01','row02'))
def test_actual_original_ha_body_and_exact_nodes_depth(index):
    assert METRICS[index] is not None  # A stored metric never replaces the actual replay below.
    row = rows()[index]
    try:
        receipt = replay_candidate_bodies((row,),core=body_core())[0]
        assert receipt.name == row.name
        assert (receipt.command_count,receipt.dependency_count) == (len(row.script),len(row.dependencies))
        assert (receipt.proof_nodes,receipt.proof_depth) == METRICS[index]
        assert 0 < receipt.proof_objects <= receipt.proof_nodes
    finally:
        gc.collect()


@pytest.mark.parametrize('index',range(3),ids=('row00','row01','row02'))
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


def changed_contracts():
    changed = []
    for index,(parameters,premises,conclusion) in enumerate(independent_contracts()):
        for position in range(len(premises)):
            changed.append((index,f'missing-premise-{position}',oracle.contract(parameters,premises[:position]+premises[position+1:],conclusion)))
    stronger = {
        0:(('raw-codes',And('sb=yb','sc=yc')),('unshifted-product',Equivalent('sb','sc','W',*R)),
           ('wrong-output-length',Equivalent('sb','sc','W','yb','yc','S T'))),
        1:(('raw-codes',And('z0b=z1b','z0c=z1c')),('same-aligned-length','L+S N0=L+S N1'),
           ('wrong-output-length',Equivalent('z0b','z0c','L','z1b','z1c','L+S N1'))),
        2:(('raw-codes',And('r1b=s1b','r1c=s1c')),('universal-successor-length','K1=S K0'),
           ('old-right-output',Equivalent(*R1,*S0))),
    }
    for index,variants in stronger.items():
        parameters,premises,_ = independent_contracts()[index]
        changed.extend((index,label,oracle.contract(parameters,premises,conclusion)) for label,conclusion in variants)
    return tuple(changed)


CHANGED = changed_contracts()


@pytest.mark.parametrize('index,label,statement',CHANGED,ids=tuple(f'row{i:02d}-{label}' for i,label,_ in CHANGED))
def test_fixed_body_rejects_altered_guards_or_other_claim(index,label,statement):
    # Fixed-script rejection does not assert independence of every premise.
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index],statement=statement),),core=body_core())


def encoded(values,variant=1):
    values = tuple(values)
    return oracle.encode_beta(values+(97+variant,101+variant),variant),len(values)


def actual_product(p,left,right,variant):
    a,L = left
    b,M = right
    assert all(value < p for value in oracle.prefix(a,L)+oracle.prefix(b,M))
    values = oracle.product_values(p,oracle.prefix(a,L),oracle.prefix(b,M))
    output,N = encoded(values,variant)
    assert N == (0 if L == 0 or M == 0 else L+M-1)
    for index in range(N+3):
        residue,diagonal,trace,total = oracle.actual_coefficient_witness(p,a,L,b,M,index,variant+1)
        assert 0 <= residue < p and total % p == residue
        assert oracle.beta(trace,0) == 0
        assert residue == (oracle.beta(output,index) if index < N else 0)
        assert oracle.beta(diagonal,index+1) == 101
    return output,N


def actual_alignment(p,c,source,old,variant):
    a,L = source
    b,N = old
    assert 0 <= c < p
    shifted,_ = encoded(oracle.prefix(b,N)+(0,),variant)
    scalar,_ = encoded(tuple(c*value % p for value in oracle.prefix(a,L)),variant+1)
    left,_ = encoded((0,)*L+oracle.prefix(shifted,N+1),variant+2)
    right,_ = encoded((0,)*(N+1)+oracle.prefix(scalar,L),variant+3)
    H = L+N+1
    summed,_ = encoded(tuple((oracle.beta(left,i)+oracle.beta(right,i)) % p for i in range(H)),variant+4)
    parts = (shifted,scalar,left,right,summed)
    assert alignment_clauses(p,c,source,old,parts) == (True,)*5
    return parts,H


def alignment_clauses(p,c,source,old,parts):
    a,L = source
    b,N = old
    u,v,left,right,z = parts
    return (oracle.model_shift(b,N,u),oracle.model_scale(p,c,a,v,L),
            oracle.model_left_pad(u,N+1,L,left),oracle.model_left_pad(v,L,N+1,right),
            oracle.model_add(p,left,right,z,L+N+1))


TRIPLES = (((),(),()),((),(1,),(1,2)),((1,),(),()),((1,),(),(1,)),((1,),(1,),()),
           ((1,),(1,),(1,)),((0,),(1,2),(1,1)),((1,0),(0,1),(1,)),
           ((1,2),(2,1),(2,0)),((0,1),(1,0),(0,2,1)),((1,1),(1,1),(1,1)))
PRIME_SCALARS = tuple((p,c) for p in (2,3,5) for c in range(p))


@pytest.mark.parametrize('values',TRIPLES)
@pytest.mark.parametrize('p,c',PRIME_SCALARS)
def test_actual_aligned_multiplication_witness_models(values,p,c):
    Adata,Bdata,Qdata = (encoded(tuple(value % p for value in row),index+1) for index,row in enumerate(values))
    Pdata = actual_product(p,Adata,Bdata,5)
    Rdata = actual_product(p,Adata,Qdata,7)
    left,H = actual_alignment(p,c,Bdata,Qdata,11)
    right,G = actual_alignment(p,c,Pdata,Rdata,19)
    Sdata = actual_product(p,Adata,(left[-1],H),29)
    assert oracle.equivalent(*Sdata,right[-1],G)
    assert Sdata[0] != right[-1]
    assert H == Bdata[1]+Qdata[1]+1 and G == Pdata[1]+Rdata[1]+1


COMPARISON_VALUES = (((),()),((1,),()),((),(1,0)),((1,2),(2,0,1)))


@pytest.mark.parametrize('values',COMPARISON_VALUES)
@pytest.mark.parametrize('pads',((0,0),(0,1),(1,0),(1,1)))
@pytest.mark.parametrize('p,c',PRIME_SCALARS)
def test_actual_alignment_congruence_models_at_independent_lengths(values,pads,p,c):
    source_values,old_values = (tuple(value % p for value in row) for row in values)
    source = encoded(source_values,1)
    old0 = encoded((0,)*pads[0]+old_values,3)
    old1 = encoded((0,)*pads[1]+old_values,5)
    assert oracle.equivalent(*old0,*old1)
    left,H = actual_alignment(p,c,source,old0,11)
    right,G = actual_alignment(p,c,source,old1,19)
    assert oracle.equivalent(left[-1],H,right[-1],G)
    assert left[-1] != right[-1]


def step_model(p,c,values):
    Adata,Bdata,Cdata = (encoded(tuple(value % p for value in row),index+1) for index,row in enumerate(values))
    Pdata = actual_product(p,Adata,Bdata,5)
    Q0data = actual_product(p,Bdata,Cdata,7)
    R0data = actual_product(p,Pdata,Cdata,9)
    S0data = actual_product(p,Adata,Q0data,11)
    assert oracle.equivalent(*R0data,*S0data)
    Ddata = encoded(oracle.prefix(*Cdata)+(c,),13)
    assert oracle.prefix(Cdata[0],Cdata[1]) == oracle.prefix(Ddata[0],Cdata[1])
    assert oracle.beta(Ddata[0],Cdata[1]) == c
    assert all(value < p for value in oracle.prefix(*Ddata))
    assert c < p  # Observed from actual bounded D plus its actual endpoint.
    Q1data = actual_product(p,Bdata,Ddata,15)
    R1data = actual_product(p,Pdata,Ddata,17)
    S1data = actual_product(p,Adata,Q1data,19)
    z,H = actual_alignment(p,c,Bdata,Q0data,23)
    y,G = actual_alignment(p,c,Pdata,S0data,31)
    y0,G0 = actual_alignment(p,c,Pdata,R0data,39)
    az = actual_product(p,Adata,(z[-1],H),47)
    assert oracle.equivalent(*Q1data,z[-1],H)
    assert oracle.equivalent(*az,y[-1],G)
    assert oracle.equivalent(*S1data,*az)
    assert oracle.equivalent(*R1data,y0[-1],G0)
    assert oracle.equivalent(y0[-1],G0,y[-1],G)
    assert oracle.equivalent(*R1data,*S1data)
    return Adata,Bdata,Cdata,Pdata,Q0data,R0data,S0data,Ddata,Q1data,R1data,S1data


@pytest.mark.parametrize('values',TRIPLES)
@pytest.mark.parametrize('p,c',PRIME_SCALARS)
def test_actual_append_step_models_with_all_products_and_witnesses(values,p,c):
    data = step_model(p,c,values)
    assert data[9][0] != data[10][0]


@pytest.mark.parametrize('fault',range(5))
def test_every_actual_alignment_clause_is_substantive(fault):
    p,c = 5,1
    source = encoded((1,),1)
    good,H = actual_alignment(p,c,source,source,3)
    u,v,left,right,z = good
    if fault == 0:
        u = encoded((2,0),11)[0]
        left = encoded((0,2,0),13)[0]
    elif fault == 1:
        v = encoded((2,),11)[0]
        right = encoded((0,0,2),13)[0]
    elif fault == 2:
        left = encoded((0,2,0),13)[0]
    elif fault == 3:
        right = encoded((0,0,2),13)[0]
    if fault == 4:
        z = encoded((0,1,2),17)[0]
    else:
        z = encoded(tuple((oracle.beta(left,i)+oracle.beta(right,i)) % p for i in range(H)),17)[0]
    clauses = alignment_clauses(p,c,source,source,(u,v,left,right,z))
    assert not clauses[fault] and all(value for index,value in enumerate(clauses) if index != fault)
    assert not oracle.equivalent(good[-1],H,z,H)


def test_comparison_uses_actual_old_formal_equivalence():
    source = encoded((1,),1)
    old0,old1 = encoded((1,),3),encoded((2,),5)
    left,H = actual_alignment(5,0,source,old0,7)
    right,G = actual_alignment(5,0,source,old1,13)
    assert not oracle.equivalent(*old0,*old1)
    assert not oracle.equivalent(left[-1],H,right[-1],G)


def test_empty_prefix_refutes_universal_successor_product_lengths():
    data = step_model(5,1,((1,1),(1,2,1),()))
    _,_,_,_,q0,r0,_,_,q1,r1,_ = data
    assert q0[1] == r0[1] == 0
    assert q1[1] == 3 and r1[1] == 4
    assert q1[1] != q0[1]+1 and r1[1] != r0[1]+1


def test_empty_left_factor_has_empty_real_products_and_nonempty_aligned_zeros():
    data = step_model(2,1,((),(1,1),()))
    Adata,_,_,Pdata,_,R0data,S0data,_,_,R1data,S1data = data
    assert Adata[1] == Pdata[1] == R0data[1] == S0data[1] == R1data[1] == S1data[1] == 0
    aligned,H = actual_alignment(2,1,Pdata,R0data,31)
    assert H == 1 and oracle.beta(aligned[-1],0) == 0
    assert oracle.equivalent(*R1data,aligned[-1],H)


@pytest.mark.parametrize('fault',('prefix','endpoint','noncanonical'))
def test_actual_append_requirements_cannot_be_replaced_by_unchecked_values(fault):
    p = 3
    old = encoded((1,),1)
    values,c = ((2,1),1) if fault == 'prefix' else (((1,2),1) if fault == 'endpoint' else ((1,3),3))
    new = encoded(values,3)
    prefix_ok = oracle.prefix(old[0],old[1]) == oracle.prefix(new[0],old[1])
    endpoint_ok = oracle.beta(new[0],old[1]) == c
    bounded = all(value < p for value in oracle.prefix(*new))
    assert (prefix_ok,endpoint_ok,bounded) == {
        'prefix':(False,True,True),'endpoint':(True,False,True),'noncanonical':(True,True,False),
    }[fault]


def test_characteristic_two_uses_natural_unit_and_formal_not_evaluation_equality():
    data = step_model(2,1,((1,1),(1,1),()))
    assert oracle.prefix(*data[3]) == (1,0,1)
    square,linear = (1,0,0),(1,0)
    def evaluate(values,x):
        value = 0
        for coefficient in values:
            value = (value*x+coefficient) % 2
        return value
    assert all(evaluate(square,x) == evaluate(linear,x) for x in range(2))
    assert not oracle.equivalent(*encoded(square,1),*encoded(linear,3))


def test_zero_scalar_leaves_all_exterior_values_free():
    data = step_model(3,0,((1,2),(2,1),(1,)))
    first,second = data[9],data[10]
    assert oracle.equivalent(*first,*second)
    assert oracle.beta(first[0],first[1]) == 114 and oracle.beta(second[0],second[1]) == 116
