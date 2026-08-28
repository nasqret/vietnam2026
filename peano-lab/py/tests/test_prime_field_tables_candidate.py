"""Non-admitting, fresh original-HA checks of actual prime-field table witnesses."""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import json
from math import factorial, gcd
import os
from pathlib import Path
import resource
import re
import signal
import subprocess
import sys

import pytest

from peano_lab.library import prime_field_arithmetic_candidate as arithmetic
from peano_lab.library import prime_field_tables_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from test_prime_field_arithmetic_candidate import (
    ROOT, capture_cases, core as parent_core, expected_add, expected_and, expected_inv,
    expected_lt, expected_mul, expected_neg, expected_prime, same_ast,
)


SOURCE_SHA256 = "2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400"
NAMES_SHA256 = "b64ad1def3da48c2eee682332759501c50aa1ef5461a16c89d25e8836c2fc09e"
ROOT_SHA256 = "8f17f00aa07c9b5c8371ed89a747163c853b687a2b4dc3d74af2ef67f87e3e6e"


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_tables_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return parent_core() | {row.name: row for row in arithmetic.make_prime_field_arithmetic_candidate_theorems(TheoremSpec)}


def check_body(name: str, mutation: str = "none"):
    table = core() | {row.name: row for row in rows()}
    row = table[name]
    if mutation == "false_conclusion":
        row = replace(row, statement=f"({row.statement}) /\\ false")
    elif mutation == "truncated_body":
        row = replace(row, script=row.script[:-1])
    elif mutation == "removed_dependency":
        row = replace(row, dependencies=row.dependencies[:-1])
    elif mutation == "corrupt_dependency":
        dependency = row.dependencies[0]
        table = table | {dependency: replace(table[dependency], statement="0 = 0")}
    elif mutation == "unbounded_grid":
        row = replace(row, statement=f"forall p i. ({expected_prime('p')}) -> exists v. ({expected_grid('add','p','i','v')})")
    elif mutation == "zero_inverse_table":
        row = replace(row, statement=f"forall p B C a v. ({expected_table('inverse','p','B','C')}) -> ({expected_lt('a','p')}) -> ({expected_at('B','C','a','v')}) -> ({expected_mul('p','a','v','1')})")
    elif mutation != "none":
        raise ValueError("unknown prime-field table proof mutation")
    if mutation != "none":
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,), core=table)
        return {"rejected": True, "mutation": mutation}
    return asdict(replay_candidate_bodies((row,), core=table)[0])


def isolated_body(name: str, mutation: str = "none"):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "peano-lab/py")
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--body", name, mutation],
                            cwd=ROOT, env=environment, text=True, capture_output=True, timeout=185)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_original_kernel_body(name):
    receipt = isolated_body(name)
    assert receipt["name"] == name and receipt["proof_depth"] <= 256


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
@pytest.mark.parametrize("mutation", ("false_conclusion", "truncated_body", "removed_dependency", "corrupt_dependency"))
def test_corrupted_proof_or_prerequisite_is_rejected(name,mutation):
    assert isolated_body(name,mutation)["rejected"] is True


@pytest.mark.parametrize("name,mutation", (("prime_field_add_grid_value_exists","unbounded_grid"),("prime_field_inverse_table_nonzero","zero_inverse_table")))
def test_row_major_and_inverse_domain_guards_cannot_be_dropped(name,mutation):
    assert isolated_body(name,mutation)["rejected"] is True


def test_exact_frozen_table_inventory_and_topology():
    assert len(rows())==31
    assert sum(len(r.dependencies) for r in rows())==93
    assert sum(len(r.script) for r in rows())==1389
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest()==SOURCE_SHA256
    assert sha256(('\n'.join(r.name for r in rows())+'\n').encode()).hexdigest()==NAMES_SHA256
    available=set(core())
    for row in rows():
        assert row.name not in available and set(row.dependencies)<=available
        assert len(row.dependencies)==len(set(row.dependencies))
        for name in row.dependencies:
            assert re.search(r"(?<![\w'])"+re.escape(name)+r"(?![\w'])",'\n'.join(row.script))
        assert row.script and not any(c.startswith(('use ','admit','sorry')) or 'DNE' in c for c in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


def expected_at(b,c,i,value):
    modulus=f"S ((S ({i})) * ({c}))"
    return (f"(exists independent_beta_gap. independent_beta_gap + S ({value}) = {modulus}) /\\ "
            f"(exists independent_beta_quotient. ({b}) = independent_beta_quotient * {modulus} + ({value}))")


def expected_zero_inverse(p,a,b):
    return expected_and(expected_lt(a,p),expected_lt(b,p),f"(({a}) = 0 /\\ ({b}) = 0) \\/ ({expected_inv(p,a,b)})")


def expected_grid(kind,p,i,value):
    a,b='independent_grid_row','independent_grid_column'
    graph=expected_add if kind=='add' else expected_mul
    return f"exists {a} {b}. "+expected_and(f"({i}) = {a} * ({p}) + {b}",graph(p,a,b,value))


def expected_value(kind,p,i,value):
    if kind in ('add','multiply'):
        return expected_grid(kind,p,i,value)
    return (expected_neg if kind=='negate' else expected_zero_inverse)(p,i,value)


def expected_prefix(kind,p,b,c,length):
    i,v='independent_prefix_index','independent_prefix_value'
    return f"forall {i}. ({expected_lt(i,length)}) -> exists {v}. "+expected_and(expected_at(b,c,i,v),expected_value(kind,p,i,v))


def expected_table(kind,p,b,c):
    return expected_prefix(kind,p,b,c,f"({p})*({p})" if kind in ('add','multiply') else p)


def expected_tables(p,ab,ac,mb,mc,nb,nc,ib,ic):
    return expected_and(expected_table('add',p,ab,ac),expected_table('multiply',p,mb,mc),expected_table('negate',p,nb,nc),expected_table('inverse',p,ib,ic))


PUBLIC_CASES=(
    (candidate.prime_field_zero_extended_inverse_relation,('p','a','b'),expected_zero_inverse),
    (candidate.prime_field_add_grid_value_relation,('p','i','value'),lambda p,i,v:expected_grid('add',p,i,v)),
    (candidate.prime_field_multiply_grid_value_relation,('p','i','value'),lambda p,i,v:expected_grid('multiply',p,i,v)),
    (candidate.prime_field_add_prefix_relation,('p','b','c','length'),lambda p,b,c,l:expected_prefix('add',p,b,c,l)),
    (candidate.prime_field_multiply_prefix_relation,('p','b','c','length'),lambda p,b,c,l:expected_prefix('multiply',p,b,c,l)),
    (candidate.prime_field_negate_prefix_relation,('p','b','c','length'),lambda p,b,c,l:expected_prefix('negate',p,b,c,l)),
    (candidate.prime_field_inverse_prefix_relation,('p','b','c','length'),lambda p,b,c,l:expected_prefix('inverse',p,b,c,l)),
    (candidate.prime_field_operation_tables_relation,('p','ab','ac','mb','mc','nb','nc','ib','ic'),expected_tables),
)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
def test_public_table_graphs_match_independent_raw_arithmetic(builder,args,expected):
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*args,tag='independent',variables=args)),_closed_formula(binder+expected(*args)))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('term',('p+1','p*p','S (p+p)','39614081257132168796771975177'))
def test_table_graphs_preserve_compound_and_large_terms(builder,args,expected,term):
    arguments=(term,)+args[1:]
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*arguments,tag='compound',variables=args)),_closed_formula(binder+expected(*arguments)))


@pytest.mark.parametrize('builder,args,binder',capture_cases(PUBLIC_CASES))
def test_all_local_and_inherited_beta_binders_reject_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=args+(binder,))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('context',((),[],('p','p'),('bad name',),('forall',)))
def test_bad_table_contexts_fail_closed(builder,args,expected,context):
    with pytest.raises(ValueError):
        builder(*('0' for _ in args),tag='context',variables=context)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('term',('unknown','p -> p','p = 0','p; true','',None,7,False))
def test_bad_table_terms_fail_closed(builder,args,expected,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='term',variables=args)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('tag',('bad tag','forall','S','',None,False))
def test_bad_table_tags_fail_closed(builder,args,expected,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


def test_all_four_actual_tables_are_constructed_from_primality_alone():
    root=next(row for row in rows() if row.name=='prime_field_operation_tables_exists')
    args=('p','ab','ac','mb','mc','nb','nc','ib','ic')
    expected=f"forall p. ({expected_prime('p')}) -> exists {' '.join(args[1:])}. ({expected_tables(*args)})"
    same_ast(_closed_formula(root.statement),_closed_formula(expected))
    assert sha256(root.statement.encode()).hexdigest()==ROOT_SHA256
    assert all('prime_field_operation_tables_exists' not in r.dependencies for r in rows())


@pytest.mark.parametrize('kind',('add','multiply','negate','inverse'))
def test_finite_choice_premise_is_pointwise_arithmetic_not_assumed_field_laws(kind):
    row=next(r for r in rows() if r.name=='prime_field_'+kind+'_prefix_choice')
    total=f"forall i. ({expected_lt('i','l')}) -> exists v. ({expected_value(kind,'p','i','v')})"
    result=f"exists b c. ({expected_prefix(kind,'p','b','c','l')})"
    same_ast(_closed_formula(row.statement),_closed_formula(f"forall p l. ({total}) -> ({result})"))
    assert row.dependencies==('lt_not_le','zero_le','le_succ','zero_add','beta_prefix_extend','finite_lt_succ_eq_or_lt')
    actual=next(r for r in rows() if r.name=='prime_field_'+kind+'_table_exists')
    assert 'prime_field_'+kind+'_prefix_choice' in actual.dependencies
    assert len(actual.dependencies)==2  # the genuine pointwise constructor


@pytest.mark.parametrize('kind,graph',(('add',expected_add),('multiply',expected_mul)))
def test_lookup_has_actual_row_major_index_and_bidirectional_meaning(kind,graph):
    lookup=next(r for r in rows() if r.name=='prime_field_'+kind+'_table_lookup')
    statement=(f"forall p B C a b v. ({expected_table(kind,'p','B','C')}) -> ({expected_lt('a','p')}) -> ({expected_lt('b','p')}) -> "
               f"({expected_at('B','C','a*p+b','v')}) -> ({graph('p','a','b','v')})")
    same_ast(_closed_formula(lookup.statement),_closed_formula(statement))
    reflection=next(r for r in rows() if r.name=='prime_field_'+kind+'_table_reflect')
    statement=f"forall p B C a b v. ({expected_table(kind,'p','B','C')}) -> ({graph('p','a','b','v')}) -> ({expected_at('B','C','a*p+b','v')})"
    same_ast(_closed_formula(reflection.statement),_closed_formula(statement))


def encode_beta(values):
    """Independent small-example CRT encoding, never a formal proof oracle."""
    values=tuple(values)
    scale=factorial(len(values))*(max(values,default=0)+1)
    code,modulus=0,1
    for i,value in enumerate(values):
        current=1+(i+1)*scale
        assert gcd(modulus,current)==1 and 0<=value<current
        code+=modulus*((value-code)*pow(modulus,-1,current)%current)
        modulus*=current
    return code,scale


def decode_beta(code,scale,index):
    return code%(1+(index+1)*scale)


@pytest.mark.parametrize('p',(2,3,5))
def test_actual_finite_beta_encoded_prime_field_tables(p):
    add_values=[(a+b)%p for a in range(p) for b in range(p)]
    mul_values=[a*b%p for a in range(p) for b in range(p)]
    neg_values=[(-a)%p for a in range(p)]
    inv_values=[0]+[pow(a,-1,p) for a in range(1,p)]
    add_code,mul_code,neg_code,inv_code=tuple(encode_beta(v) for v in (add_values,mul_values,neg_values,inv_values))
    add=lambda a,b:decode_beta(*add_code,a*p+b)
    mul=lambda a,b:decode_beta(*mul_code,a*p+b)
    assert decode_beta(*inv_code,0)==0
    for a in range(p):
        negative=decode_beta(*neg_code,a)
        inverse=decode_beta(*inv_code,a)
        assert 0<=negative<p and 0<=inverse<p
        assert add(a,negative)==0
        assert mul(a,inverse)==(0 if a==0 else 1)
        assert add(a,0)==a==add(0,a)
        assert mul(a,1)==a==mul(1,a)
        for b in range(p):
            assert 0<=add(a,b)<p and 0<=mul(a,b)<p
            assert add(a,b)==add(b,a) and mul(a,b)==mul(b,a)
            for c in range(p):
                assert add(add(a,b),c)==add(a,add(b,c))
                assert mul(mul(a,b),c)==mul(a,mul(b,c))
                assert mul(a,add(b,c))==add(mul(a,b),mul(a,c))
                assert mul(add(b,c),a)==add(mul(b,a),mul(c,a))
    assert all(a*p+b<p*p for a in range(p) for b in range(p))
    assert not any(a*p+b==p*p for a in range(p) for b in range(p))
    corrupt=(add_code[0]+1,add_code[1])
    assert any(decode_beta(*corrupt,i)!=value for i,value in enumerate(add_values))


def test_zero_inverse_convention_does_not_assert_zero_inverse():
    assert (0*0)%2==0 and (0*0)%2!=1
    assert [(a,b) for a in range(2) for b in range(2) if a*b%2==1]==[(1,1)]
    assert not any(2*b%4==1 for b in range(4))


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    if sys.argv[1:2] == ["--body"]:
        print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")), flush=True)
    else:
        for name in sys.argv[1:] or tuple(row.name for row in rows()):
            print(json.dumps(check_body(name)), flush=True)
