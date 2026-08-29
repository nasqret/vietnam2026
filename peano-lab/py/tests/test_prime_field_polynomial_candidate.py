"""Independent finite-coefficient contracts and ordinary HA body regressions.

These are dependency-curried body checks, not a substitute for the separate
complete dependency bundle and independent compiled-Lean verification.
The integer examples below diagnose encoding/contract mistakes, not proofs.
"""

from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass, replace
from functools import lru_cache
from hashlib import sha256
import gc
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time

import pytest

from peano_lab.library import prime_field_arithmetic_candidate as arithmetic
from peano_lab.library import prime_field_polynomial_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT_SHA256 = 'ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7'
PARENT_BYTES = 66503303
ARITHMETIC_SHA256 = 'd4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90'
SOURCE_SHA256 = '644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72'
NAMES_SHA256 = 'db3dadceb07584ff6be8f664663a6ac09b14c12223c0b8b86df9f3810b2517c3'
MAX_RSS_BYTES = 1536 * 1024 * 1024


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def evaluation_rows():
    from peano_lab.library.prime_field_polynomial_evaluation_candidate import make_prime_field_polynomial_evaluation_candidate_theorems
    return make_prime_field_polynomial_evaluation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    raw = (ROOT / 'artifacts/peano-library/alpha/catalog-v30.json').read_bytes()
    assert len(raw) == PARENT_BYTES and sha256(raw).hexdigest() == PARENT_SHA256
    document = json.loads(raw)
    assert document['theorem_count'] == document['checked_use_count'] == 3222
    assert document['stable_count'] == 432
    # Metadata supplies the exact types of ordinary hypotheses ONLY. All
    # actual inherited proof bodies are checked by the separate full closure.
    result = {r['name']: TheoremSpec(r['name'],r['statement'],tuple(r['dependencies']),tuple(r['script']),r['summary']) for r in document['theorems']}
    assert sha256(Path(arithmetic.__file__).read_bytes()).hexdigest() == ARITHMETIC_SHA256
    earlier = arithmetic.make_prime_field_arithmetic_candidate_theorems(TheoremSpec)
    assert len(earlier) == 42 and not (set(result) & {row.name for row in earlier})
    result.update((row.name,row) for row in earlier)
    return result


def rss_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == 'darwin' else raw * 1024


def fresh(*arguments):
    environment = os.environ.copy()
    environment['PYTHONPATH'] = os.pathsep.join((str(ROOT/'peano-lab/py'),str(ROOT/'scripts')))
    environment['PYTHONMALLOC'] = 'malloc'
    result = subprocess.run([sys.executable,str(Path(__file__).resolve()),*arguments],cwd=ROOT,env=environment,text=True,capture_output=True,timeout=185)
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output['peak_rss_bytes'] <= MAX_RSS_BYTES
    assert output['cpu_limits'] == [170,175] and output['wall_alarm_seconds'] == 180
    return output


def _body_batch(family, mutation):
    selected = rows() if family == 'coefficients' else evaluation_rows()
    table = core() | {row.name:row for row in (*rows(),*evaluation_rows())}
    receipts = []
    for original in selected:
        gc.collect()
        row, current = original, table
        if mutation == 'false_conclusion':
            row = replace(row,statement=f'({row.statement}) /\\ false')
        elif mutation == 'truncated_body':
            row = replace(row,script=row.script[:-1])
        elif mutation == 'removed_dependency':
            if not row.dependencies:
                continue
            row = replace(row,dependencies=row.dependencies[:-1])
        elif mutation == 'forged_dependency':
            if not row.dependencies:
                continue
            name = row.dependencies[0]
            current = table | {name:replace(table[name],statement='0=0')}
        elif mutation != 'none':
            raise ValueError('unknown polynomial body mutation')
        if mutation == 'none':
            receipts.append(asdict(replay_candidate_bodies((row,),core=current)[0]))
        else:
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((row,),core=current)
            receipts.append({'name':original.name,'rejected':mutation})
    return {'receipts':receipts}


@pytest.mark.parametrize('mutation',('none','false_conclusion','truncated_body','removed_dependency','forged_dependency'))
def test_all_actual_coefficient_bodies_and_hostile_variants_in_fresh_bounded_processes(mutation):
    report = fresh('--bodies','coefficients',mutation)
    expected = [row.name for row in rows() if mutation not in ('removed_dependency','forged_dependency') or row.dependencies]
    assert [r['name'] for r in report['receipts']] == expected
    if mutation == 'none':
        assert sum(r['proof_nodes'] for r in report['receipts']) == 2669
        assert max(r['proof_nodes'] for r in report['receipts']) == 301
        assert max(r['proof_depth'] for r in report['receipts']) == 62
        assert all(r['proof_depth'] <= 256 and r['proof_objects'] <= r['proof_nodes'] for r in report['receipts'])
    else:
        assert all(r['rejected'] == mutation for r in report['receipts'])


def assert_inventory(specs, available):
    available = set(available)
    for row in specs:
        assert type(row) is TheoremSpec and row.name not in available
        assert row.script and len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= available
        for dependency in row.dependencies:
            assert re.search(r"(?<![\w'])"+re.escape(dependency)+r"(?![\w'])",'\n'.join(row.script))
        assert not any(command.startswith(('use ','admit','sorry')) or 'DNE' in command for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


def test_exact_coefficient_inventory_and_actual_dependency_order():
    assert len(rows()) == 31
    assert sum(len(row.dependencies) for row in rows()) == 53
    assert sum(len(row.script) for row in rows()) == 1680
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest() == SOURCE_SHA256
    assert sha256(('\n'.join(row.name for row in rows())+'\n').encode()).hexdigest() == NAMES_SHA256
    assert_inventory(rows(),core())
    dependencies = {name for row in rows() for name in row.dependencies}
    assert {'beta_division_prefix_exists','beta_pointwise_add_prefix_exists','beta_pointwise_mul_prefix_exists','beta_repeat_exists','binary_canonical_residue_functional'} <= dependencies
    assert not {'prime_field_polynomial_coefficients_empty','prime_field_polynomial_prefix_symmetric'} & {row.name for row in rows()}


def test_no_new_statement_duplicates_any_of_the_3392_earlier_or_other_new_statements():
    report = fresh('--duplicates')
    assert report['new_count'] == 49
    assert report['duplicates'] == []


def same_ast(left,right):
    pending, seen = [(left,right)], set()
    while pending:
        a,b = pending.pop()
        assert type(a) is type(b)
        key = id(a),id(b)
        if key in seen:
            continue
        seen.add(key)
        if is_dataclass(a):
            pending.extend((getattr(a,f.name),getattr(b,f.name)) for f in fields(a))
        else:
            assert a == b


def expected_and(*parts):
    result = f'({parts[-1]})'
    for part in reversed(parts[:-1]):
        result = f'({part}) /\\ ({result})'
    return result


def expected_lt(a,b):
    return f'exists independent_gap. independent_gap+S ({a})=({b})'


def expected_mod(p,a,b):
    return f'exists independent_u independent_v. ({a})+({p})*independent_u=({b})+({p})*independent_v'


def expected_prime(p):
    return f'~(({p})=1) /\\ forall independent_a independent_b. ({p})=independent_a*independent_b -> independent_a=1 \\/ independent_b=1'


def expected_at(b,c,i,a):
    return expected_and(f'exists independent_height. independent_height+S ({a})=S ((S ({i}))*({c}))',f'exists independent_quotient. ({b})=independent_quotient*S ((S ({i}))*({c}))+({a})')


def expected_residue(p,a,r):
    return expected_and(expected_lt(r,p),expected_mod(p,a,r))


def expected_field_add(p,a,b,r):
    return expected_and(expected_lt(a,p),expected_lt(b,p),expected_residue(p,f'({a})+({b})',r))


def expected_field_mul(p,a,b,r):
    return expected_and(expected_lt(a,p),expected_lt(b,p),expected_residue(p,f'({a})*({b})',r))


def expected_coeff(p,b,c,length):
    return f'forall independent_index. ({expected_lt("independent_index",length)}) -> exists independent_value. '+expected_and(expected_at(b,c,'independent_index','independent_value'),expected_lt('independent_value',p))


def expected_equal(b,c,d,e,length):
    return f'forall independent_index independent_value. ({expected_lt("independent_index",length)}) -> ({expected_at(b,c,"independent_index","independent_value")}) -> ({expected_at(d,e,"independent_index","independent_value")})'


def expected_repeat(b,c,a,length):
    return f'forall independent_index. ({expected_lt("independent_index",length)}) -> ({expected_at(b,c,"independent_index",a)})'


def expected_normalization(p,b,c,d,e,length):
    return f'forall independent_index. ({expected_lt("independent_index",length)}) -> exists independent_source independent_target. '+expected_and(expected_at(b,c,'independent_index','independent_source'),expected_at(d,e,'independent_index','independent_target'),expected_residue(p,'independent_source','independent_target'))


def expected_add(p,ab,ac,bb,bc,cb,cc,length):
    return f'forall independent_index. ({expected_lt("independent_index",length)}) -> exists independent_left independent_right independent_result. '+expected_and(expected_at(ab,ac,'independent_index','independent_left'),expected_at(bb,bc,'independent_index','independent_right'),expected_at(cb,cc,'independent_index','independent_result'),expected_field_add(p,'independent_left','independent_right','independent_result'))


def expected_scale(p,k,ab,ac,bb,bc,length):
    point = f'forall independent_index. ({expected_lt("independent_index",length)}) -> exists independent_source independent_target. '+expected_and(expected_at(ab,ac,'independent_index','independent_source'),expected_at(bb,bc,'independent_index','independent_target'),expected_field_mul(p,k,'independent_source','independent_target'))
    return expected_and(expected_lt(k,p),point)


PUBLIC_CASES = (
    (candidate.prime_field_polynomial_coefficients_relation,('p','b','c','l'),expected_coeff),
    (candidate.prime_field_polynomial_equal_relation,('b','c','d','e','l'),expected_equal),
    (candidate.prime_field_polynomial_normalization_relation,('p','b','c','d','e','l'),expected_normalization),
    (candidate.prime_field_polynomial_add_relation,('p','ab','ac','bb','bc','cb','cc','l'),expected_add),
    (candidate.prime_field_polynomial_scale_relation,('p','k','ab','ac','bb','bc','l'),expected_scale),
)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES,ids=lambda x:x.__name__ if callable(x) else None)
def test_public_coefficient_graphs_match_independent_exact_ha(builder,args,expected):
    binder = 'forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*args,tag='independent',variables=args)),_closed_formula(binder+expected(*args)))


def test_generic_bounded_prefix_and_prefix_equality_reuse_exact_existing_graphs():
    from peano_lab.library.finite_omission_candidate import _bounded_into_term
    from peano_lab.library.matrix_recursive_determinant_candidate import _prefix
    binder = 'forall p b c d e l. '
    same_ast(_closed_formula(binder+candidate.prime_field_polynomial_coefficients_relation('p','b','c','l',tag='reuse',variables=('p','b','c','d','e','l'))),_closed_formula(binder+_bounded_into_term('b','c','l','p',tag='old',avoid=())))
    same_ast(_closed_formula(binder+candidate.prime_field_polynomial_equal_relation('b','c','d','e','l',tag='reuse',variables=('p','b','c','d','e','l'))),_closed_formula(binder+_prefix('b','c','d','e','l','old')))


def compound_cases(public_cases):
    return tuple((builder,args,expected,index,term) for builder,args,expected in public_cases for index,name in enumerate(args) for term in (f'{name}+1',f'{name}*{name}',f'S ({name}+{name})','39614081257132168796771975177'))


@pytest.mark.parametrize('builder,args,expected,index,term',compound_cases(PUBLIC_CASES))
def test_every_coefficient_argument_accepts_actual_compound_and_large_terms(builder,args,expected,index,term):
    values = (*args[:index],term,*args[index+1:])
    binder = 'forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*values,tag='compound',variables=args)),_closed_formula(binder+expected(*values)))


def capture_cases(public_cases):
    result = []
    for builder,args,_ in public_cases:
        formula = builder(*args,tag='capture',variables=args)
        binders = sorted({name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',formula) for name in clause.split()})
        result.extend((builder,args,binder) for binder in binders)
    return tuple(result)


@pytest.mark.parametrize('builder,args,binder',capture_cases(PUBLIC_CASES))
def test_every_generated_coefficient_binder_rejects_even_unused_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=args+(binder,))
    with pytest.raises(ValueError,match='captures'):
        builder(f'{args[0]}+{binder}',*args[1:],tag='capture',variables=args+(binder,))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('context',((),[],('p','p'),('bad name',),('forall',)))
def test_invalid_coefficient_context_rejected(builder,args,expected,context):
    with pytest.raises(ValueError):
        builder(*('0' for _ in args),tag='invalid',variables=context)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('term',('undeclared','p -> p','p = 0','p; true','',None,7,False))
def test_invalid_coefficient_term_rejected(builder,args,expected,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='invalid',variables=args)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('tag',('bad tag','forall','S','',None,False))
def test_invalid_coefficient_tag_rejected(builder,args,expected,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


PRINCIPAL_CONTRACTS = {
    'prime_field_polynomial_normalization_exists':f"forall p b c l. ~(p=0) -> exists d e. ({expected_normalization('p','b','c','d','e','l')})",
    'prime_field_polynomial_normalization_functional':f"forall p b c d e f g l. ({expected_normalization('p','b','c','d','e','l')}) -> ({expected_normalization('p','b','c','f','g','l')}) -> ({expected_equal('d','e','f','g','l')})",
    'prime_field_polynomial_normalization_idempotent':f"forall p b c d e f g l. ({expected_normalization('p','b','c','d','e','l')}) -> ({expected_normalization('p','d','e','f','g','l')}) -> ({expected_equal('d','e','f','g','l')})",
    'prime_field_polynomial_zero_exists':f"forall p l. ({expected_prime('p')}) -> exists b c. {expected_and(expected_coeff('p','b','c','l'),expected_repeat('b','c','0','l'))}",
    'prime_field_polynomial_add_exists':f"forall p ab ac bb bc l. ~(p=0) -> ({expected_coeff('p','ab','ac','l')}) -> ({expected_coeff('p','bb','bc','l')}) -> exists cb cc. ({expected_add('p','ab','ac','bb','bc','cb','cc','l')})",
    'prime_field_polynomial_add_functional':f"forall p ab ac bb bc cb cc db dc l. ({expected_add('p','ab','ac','bb','bc','cb','cc','l')}) -> ({expected_add('p','ab','ac','bb','bc','db','dc','l')}) -> ({expected_equal('cb','cc','db','dc','l')})",
    'prime_field_polynomial_scale_exists':f"forall p k ab ac l. ~(p=0) -> ({expected_lt('k','p')}) -> ({expected_coeff('p','ab','ac','l')}) -> exists bb bc. ({expected_scale('p','k','ab','ac','bb','bc','l')})",
    'prime_field_polynomial_scale_functional':f"forall p k ab ac bb bc cb cc l. ({expected_scale('p','k','ab','ac','bb','bc','l')}) -> ({expected_scale('p','k','ab','ac','cb','cc','l')}) -> ({expected_equal('bb','bc','cb','cc','l')})",
    'prime_field_polynomial_scale_one':f"forall p b c l. ({expected_prime('p')}) -> ({expected_coeff('p','b','c','l')}) -> ({expected_scale('p','1','b','c','b','c','l')})",
    'prime_field_polynomial_scale_zero':f"forall p b c zb zc l. ({expected_prime('p')}) -> ({expected_coeff('p','b','c','l')}) -> ({expected_repeat('zb','zc','0','l')}) -> ({expected_scale('p','0','b','c','zb','zc','l')})",
}


GUARD_CASES = {
    'zero_modulus':('prime_field_polynomial_normalization_exists',f"forall p b c l. 0=0 -> exists d e. ({expected_normalization('p','b','c','d','e','l')})"),
    'unbounded_addend':('prime_field_polynomial_add_exists',f"forall p ab ac bb bc l. ~(p=0) -> 0=0 -> ({expected_coeff('p','bb','bc','l')}) -> exists cb cc. ({expected_add('p','ab','ac','bb','bc','cb','cc','l')})"),
    'unbounded_scalar':('prime_field_polynomial_scale_exists',f"forall p k ab ac l. ~(p=0) -> 0=0 -> ({expected_coeff('p','ab','ac','l')}) -> exists bb bc. ({expected_scale('p','k','ab','ac','bb','bc','l')})"),
    'raw_code_uniqueness':('prime_field_polynomial_add_functional',f"forall p ab ac bb bc cb cc db dc l. ({expected_add('p','ab','ac','bb','bc','cb','cc','l')}) -> ({expected_add('p','ab','ac','bb','bc','db','dc','l')}) -> cb=db /\\ cc=dc"),
}


@pytest.mark.parametrize('mutation',tuple(GUARD_CASES))
def test_coefficient_proofs_reject_removed_guards_and_raw_code_uniqueness(mutation):
    assert fresh('--guard','coefficients',mutation)['rejected'] == mutation


@pytest.mark.parametrize('name,expected',tuple(PRINCIPAL_CONTRACTS.items()),ids=tuple(PRINCIPAL_CONTRACTS))
def test_principal_coefficient_statements_have_exact_constructive_contracts(name,expected):
    row = next(r for r in rows() if r.name == name)
    same_ast(_closed_formula(row.statement),_closed_formula(expected))


def encode_beta(values, multiplier=1):
    """Independent concrete CRT encoding, used only in diagnostic examples."""
    values = tuple(values)
    assert all(type(v) is int and v >= 0 for v in values)
    assert type(multiplier) is int and multiplier > 0
    scale = (max(values,default=0)+1)*math.factorial(max(1,len(values)))*multiplier
    code, product = 0,1
    for i,value in enumerate(values):
        modulus = 1+(i+1)*scale
        assert value < modulus and math.gcd(product,modulus) == 1
        correction = ((value-code)*pow(product,-1,modulus))%modulus
        code += product*correction
        product *= modulus
    return code,scale


def decode_beta(code,index):
    b,c = code
    return b%(1+(index+1)*c)


def decoded_prefix(code,length):
    return tuple(decode_beta(code,i) for i in range(length))


def model_coeff(p,code,length):
    return all(decode_beta(code,i)<p for i in range(length))


def model_normalization(p,source,target,length):
    return all(0<=decode_beta(target,i)<p and decode_beta(source,i)%p==decode_beta(target,i) for i in range(length))


def model_add(p,left,right,target,length):
    return all(0<=decode_beta(left,i)<p and 0<=decode_beta(right,i)<p and 0<=decode_beta(target,i)<p and (decode_beta(left,i)+decode_beta(right,i))%p==decode_beta(target,i) for i in range(length))


def model_scale(p,k,source,target,length):
    return 0<=k<p and all(0<=decode_beta(source,i)<p and 0<=decode_beta(target,i)<p and (k*decode_beta(source,i))%p==decode_beta(target,i) for i in range(length))


@pytest.mark.parametrize('p',(2,3,5,7,11,13))
@pytest.mark.parametrize('raw',((),(0,),(0,0,0),(2,3,4),(19,0,7,25),(2**96+17,2**80+3)))
def test_actual_beta_normalization_recoding_addition_and_scalar_examples(p,raw):
    source = encode_beta(raw)
    reduced_values = tuple(a%p for a in raw)
    first,second = encode_beta(reduced_values),encode_beta(reduced_values,3)
    assert first != second
    assert decoded_prefix(source,len(raw)) == raw
    assert decoded_prefix(first,len(raw)) == decoded_prefix(second,len(raw)) == reduced_values
    assert model_normalization(p,source,first,len(raw))
    assert model_normalization(p,first,second,len(raw))
    assert model_coeff(p,first,len(raw))
    reverse_values = tuple(reversed(reduced_values))
    other = encode_beta(reverse_values)
    added = encode_beta(tuple((a+b)%p for a,b in zip(reduced_values,reverse_values)))
    assert model_add(p,first,other,added,len(raw)) and model_add(p,other,second,added,len(raw))
    zero = encode_beta((0,)*len(raw))
    assert model_add(p,second,zero,second,len(raw))
    for k in (0,1,p-1):
        product = encode_beta(tuple(k*a%p for a in reduced_values))
        assert model_scale(p,k,first,product,len(raw)) and model_scale(p,k,second,product,len(raw))
    assert model_scale(p,0,first,zero,len(raw)) and model_scale(p,1,first,second,len(raw))


def test_length_zero_and_modulus_or_scalar_boundaries_are_not_silently_conflated():
    empty = encode_beta(())
    assert model_coeff(0,empty,0) and model_normalization(0,empty,empty,0)
    assert not model_normalization(0,encode_beta((0,)),encode_beta((0,)),1)
    assert not model_scale(0,0,empty,empty,0)
    assert model_scale(2,1,empty,empty,0) and not model_scale(2,2,empty,empty,0)
    assert not model_add(3,encode_beta((3,)),encode_beta((0,)),encode_beta((0,)),1)
    assert model_add(2,encode_beta((1,)),encode_beta((1,)),encode_beta((0,)),1)


@pytest.mark.parametrize('p',(2,3,5,7))
def test_actual_recoded_beta_tables_obey_associativity_and_both_scalar_distributivities(p):
    a,b,c = ((0,1,p-1,0),(p-1,0,1,1),(1,1,0,p-1))
    add = lambda left,right: tuple((x+y)%p for x,y in zip(left,right))
    scale = lambda k,values: tuple(k*x%p for x in values)
    first,second = add(add(a,b),c),add(a,add(b,c))
    assert first == second
    left,right = encode_beta(first),encode_beta(second,3)
    assert left != right and decoded_prefix(left,4) == decoded_prefix(right,4)
    assert model_add(p,encode_beta(add(a,b)),encode_beta(c),left,4)
    assert model_add(p,encode_beta(a),encode_beta(add(b,c)),right,4)
    for k in range(p):
        assert scale(k,add(a,b)) == add(scale(k,a),scale(k,b))
        assert model_scale(p,k,encode_beta(add(a,b)),encode_beta(add(scale(k,a),scale(k,b))),4)
        for h in range(p):
            assert scale(k,scale(h,a)) == scale(k*h%p,a)
            assert scale((k+h)%p,a) == add(scale(k,a),scale(h,a))
            assert model_scale(p,(k+h)%p,encode_beta(a),encode_beta(add(scale(k,a),scale(h,a)),2),4)


if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    started = time.monotonic()
    if sys.argv[1:2] == ['--bodies']:
        report = _body_batch(sys.argv[2],sys.argv[3])
    elif sys.argv[1:2] == ['--guard']:
        family,mutation = sys.argv[2:4]
        if family == 'evaluation':
            from test_prime_field_polynomial_evaluation_candidate import GUARD_CASES as guards
        else:
            guards = GUARD_CASES
        name,statement = guards[mutation]
        table = core() | {row.name:row for row in (*rows(),*evaluation_rows())}
        row = replace(table[name],statement=statement)
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,),core=table)
        report = {'name':name,'rejected':mutation}
    elif sys.argv[1:] == ['--duplicates']:
        from constructive_lower_tier_support import statement_duplicates
        all_rows = (*rows(),*evaluation_rows())
        report = {'new_count':len(all_rows),'duplicates':statement_duplicates(all_rows)}
    else:
        raise SystemExit('expected --bodies FAMILY MUTATION, --guard FAMILY MUTATION, or --duplicates')
    report.update(cpu_limits=list(resource.getrlimit(resource.RLIMIT_CPU)),wall_alarm_seconds=180,peak_rss_bytes=rss_bytes(),seconds=time.monotonic()-started)
    assert report['peak_rss_bytes'] <= MAX_RSS_BYTES
    print(json.dumps(report,sort_keys=True),flush=True)
