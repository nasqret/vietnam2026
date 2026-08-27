"""Fresh-process original HA tests for constructive Gaussian divisibility."""

from __future__ import annotations

from dataclasses import asdict,replace
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import subprocess
import sys

import pytest

from peano_lab.library import gaussian_divisibility_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.library import gaussian_euclidean_candidate as ge
from test_gaussian_ring_candidate import ROOT,core,rows as ring_rows,assert_family_contract,reference_divides,reference_associate,reference_irreducible,reference_unit,GRID,numerical_mul,numerical_norm


@lru_cache(maxsize=1)
def rows():
    return candidate.make_gaussian_divisibility_candidate_theorems(TheoremSpec)


BODY_PROFILES=dict(zip((row.name for row in rows()),(
    (21,13,21),(21,13,21),(11,8,11),(11,8,11),(11,8,11),(48,26,48),(44,22,44),(25,16,25),
    (43,25,43),(49,26,49),(88,36,88),(29,17,29),(24,15,24),(63,37,63),(78,37,78),(44,22,44),
    (87,38,87),(112,32,112),(14,10,14),(44,21,44),(58,24,58),(24,16,24),(30,18,30),(72,38,72),
    (109,38,109),(48,27,48),(63,22,63),(29,15,29),(45,26,45),
),strict=True))


def check_body(name: str, mutation: str='none'):
    table=core()|{row.name:row for row in (*ring_rows(),*rows())}
    row=table[name]
    if mutation=='false_conclusion':
        row=replace(row,statement=f'({row.statement}) /\\ false')
    elif mutation=='truncated_body':
        row=replace(row,script=row.script[:-1])
    elif mutation=='removed_dependency':
        row=replace(row,dependencies=row.dependencies[:-1])
    elif mutation=='corrupt_dependency':
        dep=row.dependencies[0]
        table=table|{dep:replace(table[dep],statement='0=0')}
    elif mutation=='missing_nonzero_norm_bound':
        assert row.name=='gaussian_divisor_norm_bound'
        row=replace(row,statement=row.statement.replace('~(z=0) -> ','',1))
    elif mutation=='mutual_divisibility_is_code_equality':
        assert row.name=='gaussian_mutual_divisibility_associate'
        row=replace(row,statement=f"forall a b. ({reference_divides('a','b','fake_equal_first')}) -> ({reference_divides('b','a','fake_equal_second')}) -> a=b")
    elif mutation=='unrestricted_natural_divisibility_decision':
        assert row.name=='gaussian_divides_decidable'
        row=replace(row,statement=f"forall d z. ({reference_divides('d','z','fake_decision_yes')}) \\/ ~({reference_divides('d','z','fake_decision_no')})")
    if mutation!='none':
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,),core=table)
        return {'rejected':True,'mutation':mutation}
    return asdict(replay_candidate_bodies((row,),core=table)[0])


def isolated_body(name: str, mutation: str='none'):
    environment=os.environ.copy()
    environment['PYTHONPATH']=os.pathsep.join((str(ROOT/'peano-lab/py'),str(ROOT/'scripts')))
    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--body',name,mutation],cwd=ROOT,env=environment,text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
def test_original_kernel_body_in_fresh_process(name):
    receipt=isolated_body(name)
    assert receipt['name']==name
    assert receipt['proof_nodes']>0 and receipt['proof_depth']<=256
    assert (receipt['proof_nodes'],receipt['proof_depth'],receipt['proof_objects'])==BODY_PROFILES[name]


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
@pytest.mark.parametrize('mutation',('false_conclusion','truncated_body'))
def test_negative_proof_mutation_in_fresh_process(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


@pytest.mark.parametrize('name',tuple(row.name for row in rows() if row.dependencies))
@pytest.mark.parametrize('mutation',('removed_dependency','corrupt_dependency'))
def test_dependency_mutation_in_fresh_process(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


def test_exact_divisibility_inventory_and_every_local_formula():
    assert_family_contract(rows(),ring_rows(),(29,92,787,'84637a1c3b2b7180962d41becec0ae7720a401029d27db325ddce37d51afc474'))


ROOT_PINS={
    'gaussian_divides_decidable':'c008dfc3987d6c5565c6f85a23eb9ce2b618f58b327d1336039bfde9fb606569',
    'gaussian_mutual_divisibility_associate':'001a4800dd2a63d04ee8f2046d1cc5bac6e4cc875f9039e378bfa959533e693e',
    'gaussian_divisor_norm_factor':'6ff9c8c4c3446fc06f8bf556f61d788a1ded00f5f849fbb200d9111d13e68422',
    'gaussian_divisor_norm_bound':'f5d18361d3f4a6b7dd50809d625b8775dcf964e1c57f03c91db76c1939012cad',
    'gaussian_irreducible_divides_irreducible_associate':'72938c554c178ad6346334c29d595e858e70b67ced0d1fa118ed35cd1c585a2e',
}


@pytest.mark.parametrize('name,digest',ROOT_PINS.items())
def test_principal_divisibility_hashes(name,digest):
    assert sha256(next(row.statement for row in rows() if row.name==name).encode()).hexdigest()==digest


def test_divisibility_decision_has_actual_carriers_and_both_exact_branches():
    expected=f"forall d z. ({ge._gaussian('d','expected_decision_divisor')}) -> ({ge._gaussian('z','expected_decision_value')}) -> ({reference_divides('d','z','expected_yes')}) \\/ ~({reference_divides('d','z','expected_no')})"
    row=next(row for row in rows() if row.name=='gaussian_divides_decidable')
    assert _closed_formula(row.statement)==_closed_formula(expected)
    assert 'gaussian_euclidean_division_exists' in row.dependencies
    assert 'gaussian_division_divisible_remainder_zero' in row.dependencies


def test_divisor_norm_factor_actually_constructs_quotient_and_norm():
    expected=f"forall d z D N. ({reference_divides('d','z')}) -> ({ge._code_norm('d','D','expected_divisor_norm')}) -> ({ge._code_norm('z','N','expected_value_norm')}) -> exists q Q. " \
             f"({ge._code_mul('d','q','z','expected_actual_quotient')}) /\\ (({ge._code_norm('q','Q','expected_quotient_norm')}) /\\ N=D*Q)"
    row=next(row for row in rows() if row.name=='gaussian_divisor_norm_factor')
    assert _closed_formula(row.statement)==_closed_formula(expected)


def test_mutual_divisibility_has_actual_unit_witness_not_identical_codes():
    expected=f"forall a b. ({reference_divides('a','b','expected_first')}) -> ({reference_divides('b','a','expected_second')}) -> ({reference_associate('a','b')})"
    row=next(row for row in rows() if row.name=='gaussian_mutual_divisibility_associate')
    assert _closed_formula(row.statement)==_closed_formula(expected)
    assert 'gaussian_zero_divides_only_zero' in row.dependencies
    assert 'gaussian_multiply_cancel_left' in row.dependencies


def test_irreducible_divisibility_matches_real_unit_association():
    expected=f"forall p q. ({reference_irreducible('p','expected_first_irred')}) -> ({reference_irreducible('q','expected_second_irred')}) -> ({reference_divides('p','q')}) -> ({reference_associate('p','q')})"
    row=next(row for row in rows() if row.name=='gaussian_irreducible_divides_irreducible_associate')
    assert _closed_formula(row.statement)==_closed_formula(expected)


@pytest.mark.parametrize('name,mutation',(
    ('gaussian_divisor_norm_bound','missing_nonzero_norm_bound'),
    ('gaussian_mutual_divisibility_associate','mutual_divisibility_is_code_equality'),
    ('gaussian_divides_decidable','unrestricted_natural_divisibility_decision'),
))
def test_divisibility_statement_boundary_mutations_are_rejected(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


def numerical_quotient(divisor,value):
    denominator=numerical_norm(divisor)
    if denominator==0:
        return (0,0) if value==(0,0) else None
    real=value[0]*divisor[0]+value[1]*divisor[1]
    imaginary=value[1]*divisor[0]-value[0]*divisor[1]
    if real%denominator or imaginary%denominator:
        return None
    return (real//denominator,imaginary//denominator)


@pytest.mark.parametrize('divisor',GRID)
def test_independent_divisor_norm_and_unit_association_microaudit(divisor):
    for value in GRID:
        quotient=numerical_quotient(divisor,value)
        if quotient is not None:
            assert numerical_mul(divisor,quotient)==value
            assert numerical_norm(value)==numerical_norm(divisor)*numerical_norm(quotient)
            if value!=(0,0):
                assert numerical_norm(divisor)<=numerical_norm(value)
        reverse=numerical_quotient(value,divisor)
        if quotient is not None and reverse is not None:
            if divisor==(0,0):
                assert value==(0,0)
            else:
                assert numerical_norm(quotient)==1


def test_nonzero_and_associate_conventions_have_real_counterexamples():
    assert numerical_quotient((5,0),(0,0))==(0,0)
    assert numerical_norm((5,0))>numerical_norm((0,0))
    assert numerical_quotient((1,0),(-1,0))==(-1,0)
    assert numerical_quotient((-1,0),(1,0))==(-1,0)
    assert (1,0)!=(-1,0)


if __name__=='__main__':
    assert sys.argv[1]=='--body'
    resource.setrlimit(resource.RLIMIT_CPU,(45,50))
    print(json.dumps(check_body(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'none')))
