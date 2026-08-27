"""Fresh original-HA body checks for actual Gaussian ring/divisibility graphs."""

from __future__ import annotations

from dataclasses import asdict,replace
from functools import lru_cache
from hashlib import sha256
import json
from math import isqrt
import os
from pathlib import Path
import re
import resource
import subprocess
import sys

import pytest

from peano_lab.library import gaussian_ring_candidate as candidate
from peano_lab.library import gaussian_euclidean_candidate as ge
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.kernel.formulas import parse_formula_with_names


ROOT=Path(__file__).resolve().parents[3]
PARENT_SHA256='897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9'


@lru_cache(maxsize=1)
def rows():
    return candidate.make_gaussian_ring_candidate_theorems(TheoremSpec)


BODY_PROFILES=dict(zip((row.name for row in rows()),(
    (38,23,38),(14,11,14),(43,24,43),(60,33,60),(60,33,60),(60,33,60),(60,33,60),(60,33,60),(60,33,60),
    (43,15,41),(89,29,89),(25,14,25),(127,29,127),(177,34,177),(25,14,25),(156,31,156),
    (52,18,46),(162,83,162),(203,35,169),(162,83,162),(11,8,11),(42,24,42),(19,12,19),(28,17,28),
    (63,29,63),(79,31,79),(56,21,56),(44,19,44),(18,11,18),(20,12,20),(80,27,80),(119,67,119),
    (76,24,68),(170,37,152),(77,33,77),(158,48,158),(158,48,158),(66,25,63),(25,15,25),(199,36,174),
    (25,15,25),(178,33,148),(25,15,25),(94,37,94),(139,44,139),(12,9,12),(12,9,12),(62,30,62),
    (62,26,62),(138,32,129),(138,32,129),(138,32,129),(138,32,129),(73,32,73),(189,52,189),(66,33,66),
    (92,38,92),(57,26,57),(123,39,123),(60,27,60),(10,7,10),(40,15,40),(97,37,97),(42,21,42),(38,23,38),
),strict=True))


@lru_cache(maxsize=1)
def core():
    payload=(ROOT/'artifacts/peano-library/alpha/catalog-v28.json').read_bytes()
    assert sha256(payload).hexdigest()==PARENT_SHA256
    document=json.loads(payload)
    assert document['theorem_count']==document['checked_use_count']==2764
    assert document['stable_count']==432
    return {r['name']:TheoremSpec(r['name'],r['statement'],tuple(r['dependencies']),tuple(r['script']),r.get('summary','')) for r in document['theorems']}


def check_body(name: str, mutation: str='none'):
    table=core()|{row.name:row for row in rows()}
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
    elif mutation=='fake_natural_identity':
        assert row.name=='gaussian_one_unit'
        row=replace(row,statement=candidate._unit('1','fake_natural_one'))
    elif mutation=='missing_nonzero_cancellation':
        assert row.name=='gaussian_multiply_cancel_left'
        row=replace(row,statement=row.statement.replace('~(a=0) -> ','',1))
    elif mutation=='missing_carrier_domain':
        assert row.name=='gaussian_add_zero_right'
        row=replace(row,statement='forall a. '+ge._code_add('a','0','a','invalid_natural_domain'))
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


def assert_family_contract(ordered,previous,expected):
    """Pin exact additive inventory and parse every actual local HA formula."""
    assert len(ordered)==expected[0]
    assert sum(len(row.dependencies) for row in ordered)==expected[1]
    assert sum(len(row.script) for row in ordered)==expected[2]
    assert sha256('\n'.join(row.name for row in ordered).encode()).hexdigest()==expected[3]
    available=set(core())|{row.name for row in previous}
    for row in ordered:
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert not parse_formula_with_names(row.statement)[1]
        for command in row.script:
            assert not command.startswith('use ')
            assert not any(marker in command for marker in ('DNE','sorry','admit','oracle','axiom'))
            if command.startswith('have '):
                parse_formula_with_names(command.split(' : ',1)[1])
        available.add(row.name)


def test_literal_ring_inventory_and_every_local_claim():
    assert_family_contract(rows(),(),(65,204,2162,'263fb533b64efe6558a5b8c0678a9c4bc6a0de2c49ac64707d83eb5992a3367d'))


ROOT_PINS={
    'gaussian_unit_iff_norm_one':'1c480f8f6989ba91bf2103bec39c839a75aa0b3026dc5314b8141643c178a6e7',
    'gaussian_multiply_cancel_left':'c9a878b2816db6bb278a7fe639fb33bdfd8cca1d1d4a4289df004b9edfa268da',
    'gaussian_one_unit':'5937226f081263a82019184fc2e7643bc35c47d38d1acfa3103335c52d4543bd',
}


@pytest.mark.parametrize('name,digest',ROOT_PINS.items())
def test_principal_ring_hashes(name,digest):
    assert sha256(next(row.statement for row in rows() if row.name==name).encode()).hexdigest()==digest


def reference_divides(d,z,tag='reference_divides'):
    return f"exists quotient. ({ge._code_mul(d,'quotient',z,tag+'product')})"


def reference_unit(z,tag='reference_unit'):
    return f"exists inverse. ({ge._code_mul(z,'inverse','6',tag+'product')})"


def reference_associate(a,b,tag='reference_associate'):
    return f"exists unit. ({reference_unit('unit',tag+'unit')}) /\\ ({ge._code_mul('unit',a,b,tag+'product')})"


def reference_irreducible(p,tag='reference_irreducible'):
    return f"({ge._gaussian(p,tag+'valid')}) /\\ (~(({p})=0) /\\ (~({reference_unit(p,tag+'unit')}) /\\ " \
           f"forall first second. ({ge._code_mul('first','second',p,tag+'product')}) -> ({reference_unit('first',tag+'first')}) \\/ ({reference_unit('second',tag+'second')})))"


def reference_prime(p,tag='reference_prime'):
    return f"({ge._gaussian(p,tag+'valid')}) /\\ (~(({p})=0) /\\ (~({reference_unit(p,tag+'unit')}) /\\ " \
           f"forall first second product. ({ge._code_mul('first','second','product',tag+'product')}) -> ({reference_divides(p,'product',tag+'divisor')}) -> ({reference_divides(p,'first',tag+'first')}) \\/ ({reference_divides(p,'second',tag+'second')})))"


PUBLIC_BUILDERS=(
    (candidate.gaussian_divides_relation,('d','z'),reference_divides),
    (candidate.gaussian_unit_relation,('z',),reference_unit),
    (candidate.gaussian_associate_relation,('a','b'),reference_associate),
    (candidate.gaussian_irreducible_relation,('p',),reference_irreducible),
    (candidate.gaussian_prime_relation,('p',),reference_prime),
)


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
def test_public_graph_has_exact_independent_semantics(builder,arguments,reference):
    prefix='forall '+' '.join(arguments)+'. '
    actual=builder(*arguments,tag='actual',variables=arguments)
    assert _closed_formula(prefix+actual)==_closed_formula(prefix+reference(*arguments))
    assert set(parse_formula_with_names(actual)[1])==set(arguments)
    assert _closed_formula(prefix+actual)==_closed_formula(prefix+builder(*arguments,tag='renamed',variables=arguments))


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
def test_public_graph_accepts_legitimate_terms_repeats_and_constants(builder,arguments,reference):
    context=('x','y')
    for changed in (('x+0',)*len(arguments),('0',)*len(arguments),('x*y',)*len(arguments)):
        actual=builder(*changed,tag='actual',variables=context)
        assert _closed_formula('forall x y. '+actual)==_closed_formula('forall x y. '+reference(*changed))


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
@pytest.mark.parametrize('bad',('', 'S','forall','unknown','x y','x;y','x)','a /\\ b'))
def test_public_graph_rejects_invalid_terms_and_formula_injection(builder,arguments,reference,bad):
    for index in range(len(arguments)):
        changed=list(arguments)
        changed[index]=bad
        with pytest.raises(ValueError):
            builder(*changed,tag='actual',variables=arguments)


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
@pytest.mark.parametrize('bad',('', 'S','forall','1','a+b','x;y'))
def test_public_graph_rejects_invalid_tags(builder,arguments,reference,bad):
    with pytest.raises(ValueError):
        builder(*arguments,tag=bad,variables=arguments)


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
@pytest.mark.parametrize('context',((),('x','x'),('S',),('x y',),['x']))
def test_public_graph_requires_explicit_distinct_valid_context(builder,arguments,reference,context):
    with pytest.raises(ValueError):
        builder(*arguments,tag='actual',variables=context)


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
def test_public_graph_rejects_capture_in_every_nested_binder_namespace(builder,arguments,reference):
    formula=builder(*arguments,tag='actual',variables=arguments)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',formula) for name in clause.split()}
    representatives={}
    for name in sorted(binders):
        representatives.setdefault(name.split('_',1)[0],name)
    assert representatives
    for name in representatives.values():
        changed=(name,*arguments[1:])
        with pytest.raises(ValueError):
            builder(*changed,tag='actual',variables=changed)


def test_norm_one_iff_unit_preserves_given_actual_norm_and_actual_inverse():
    norm=ge._code_norm('z','N','expected_unit_norm')
    unit=reference_unit('z')
    expected=f'forall z N. ({norm}) -> ((({unit}) -> N=1) /\\ (N=1 -> ({unit})))'
    actual=next(row.statement for row in rows() if row.name=='gaussian_unit_iff_norm_one')
    assert _closed_formula(actual)==_closed_formula(expected)


@pytest.mark.parametrize('name,mutation',(
    ('gaussian_one_unit','fake_natural_identity'),
    ('gaussian_multiply_cancel_left','missing_nonzero_cancellation'),
    ('gaussian_add_zero_right','missing_carrier_domain'),
))
def test_semantic_domain_and_identity_mutations_are_rejected(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


def reference_code(z):
    real,imaginary=z
    a=2*real if real>=0 else -2*real-1
    b=2*imaginary if imaginary>=0 else -2*imaginary-1
    return (a+b)*(a+b+1)+2*b


def reference_decode(code):
    if code<0 or code%2:
        return None
    diagonal=(isqrt(1+4*code)-1)//2
    b=(code-diagonal*(diagonal+1))//2
    a=diagonal-b
    assert 0<=b<=diagonal
    return tuple(value//2 if value%2==0 else -(value+1)//2 for value in (a,b))


def numerical_add(a,b):
    return (a[0]+b[0],a[1]+b[1])


def numerical_neg(a):
    return (-a[0],-a[1])


def numerical_mul(a,b):
    return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])


def numerical_norm(z):
    return z[0]*z[0]+z[1]*z[1]


GRID=tuple((a,b) for a in range(-3,4) for b in range(-3,4))


@pytest.mark.parametrize('z',GRID)
def test_independent_signed_code_norm_and_ring_microaudit(z):
    assert reference_decode(reference_code(z))==z
    assert (numerical_norm(z)==0)==(z==(0,0))
    assert numerical_mul(z,(1,0))==z
    assert numerical_add(z,(0,0))==z
    for w in GRID:
        assert numerical_norm(numerical_mul(z,w))==numerical_norm(z)*numerical_norm(w)
        assert numerical_mul(z,w)==numerical_mul(w,z)
        if numerical_norm(z)==1:
            assert numerical_mul(z,(z[0],-z[1]))==(1,0)


def test_identity_units_and_zero_boundaries_in_actual_code_convention():
    assert reference_code((0,0))==0
    assert reference_code((1,0))==6
    assert reference_decode(1) is None
    assert {reference_code(z) for z in GRID if numerical_norm(z)==1}=={2,4,6,10}
    assert numerical_mul((0,0),(1,0))==numerical_mul((0,0),(0,0))
    assert (1,0)!=(0,0)


if __name__=='__main__':
    assert sys.argv[1]=='--body'
    resource.setrlimit(resource.RLIMIT_CPU,(45,50))
    print(json.dumps(check_body(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'none')))
