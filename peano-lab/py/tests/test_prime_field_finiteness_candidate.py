"""Actual finite-cardinality and repeated-addition characteristic candidate checks."""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import re
import signal
import subprocess
import sys

import pytest

from peano_lab.library import prime_field_finiteness_candidate as candidate
from peano_lab.library import prime_field_tables_candidate as tables
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from test_prime_field_tables_candidate import (
    ROOT, core as previous_core, encode_beta, decode_beta, expected_at, expected_tables,
)
from test_prime_field_arithmetic_candidate import (
    capture_cases, expected_add, expected_and, expected_laws, expected_lt,
    expected_prime, expected_residue, same_ast,
)


SOURCE_SHA256 = "a86bc0d8913ebfc1ea84c8dad691db5f90e21029c612ee87ad804657b1971b28"
NAMES_SHA256 = "8a751bbad4c2ebd3c9f3ad89fbdc42e8721ca9151791c281ac9b4818e390af9b"
PRINCIPAL_SHA256 = {
    "prime_field_characteristic_exact": "119e9da82eb4dfcd882fcefc8bde1880e04409ef085417c7a1c6c121e47bfd16",
    "prime_field_of_prime_order_exists": "f0a61089155f5bb6cd5e6fa79774756a296253a412e2b131bf8f491e8099b8a7",
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_finiteness_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return previous_core() | {row.name: row for row in tables.make_prime_field_tables_candidate_theorems(TheoremSpec)}


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
    elif mutation == "no_trace_steps":
        source=expected_and(expected_at('b','c','0','0'),expected_at('b','c','n','r'))
        row=replace(row,statement=f"forall p n b c r. ({expected_prime('p')}) -> ({source}) -> ({expected_residue('p','n','r')})")
    elif mutation == "wrong_characteristic":
        row=replace(row,statement=f"forall p. ({expected_prime('p')}) -> ({expected_characteristic('S p')})")
    elif mutation == "no_prime_structure":
        args=('p','ab','ac','mb','mc','nb','nc','ib','ic','eb','ec')
        row=replace(row,statement=f"forall p. exists {' '.join(args[1:])}. ({expected_structure(*args)})")
    elif mutation != "none":
        raise ValueError("unknown prime-field finiteness proof mutation")
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


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
@pytest.mark.parametrize('mutation',('false_conclusion','truncated_body','removed_dependency','corrupt_dependency'))
def test_counterfeit_proofs_or_dependencies_are_rejected(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


@pytest.mark.parametrize('name,mutation',(
    ('prime_field_unit_trace_residue','no_trace_steps'),
    ('prime_field_characteristic_exact','wrong_characteristic'),
    ('prime_field_of_prime_order_exists','no_prime_structure'),
))
def test_execution_steps_characteristic_and_prime_guards_cannot_be_forged(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


def test_exact_frozen_finiteness_inventory_and_dependency_order():
    assert len(rows())==14
    assert sum(len(r.dependencies) for r in rows())==41
    assert sum(len(r.script) for r in rows())==562
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
    assert 'prime_field_enumeration_exists' not in available
    assert 'matrix_lattice_identity_selector_exists' in next(r.dependencies for r in rows() if r.name=='prime_field_cardinality_exists')


def expected_enumeration(p,b,c):
    i='independent_enumeration_index'
    return f"forall {i}. ({expected_lt(i,p)}) -> ({expected_at(b,c,i,i)})"


def expected_cardinality(p,b,c):
    bounded=f"forall i a. ({expected_lt('i',p)}) -> ({expected_at(b,c,'i','a')}) -> ({expected_lt('a',p)})"
    injective=f"forall i j a. ({expected_lt('i',p)}) -> ({expected_lt('j',p)}) -> ({expected_at(b,c,'i','a')}) -> ({expected_at(b,c,'j','a')}) -> i = j"
    surjective=f"forall a. ({expected_lt('a',p)}) -> exists i. ({expected_lt('i',p)}) /\\ ({expected_at(b,c,'i','a')})"
    return expected_and(expected_enumeration(p,b,c),bounded,injective,surjective)


def expected_steps(p,b,c,n):
    i,u,v='independent_trace_index','independent_trace_before','independent_trace_after'
    return f"forall {i}. ({expected_lt(i,n)}) -> exists {u} {v}. "+expected_and(expected_at(b,c,i,u),expected_at(b,c,f'S ({i})',v),expected_add(p,u,'1',v))


def expected_trace(p,b,c,n,r):
    return expected_and(expected_at(b,c,'0','0'),expected_at(b,c,n,r),expected_steps(p,b,c,n))


def expected_multiple(p,n,r):
    b,c='independent_unit_code','independent_unit_scale'
    return f"exists {b} {c}. ({expected_trace(p,b,c,n,r)})"


def expected_characteristic(p):
    n='independent_smaller_positive'
    return expected_and(expected_multiple(p,p,'0'),f"forall {n}. ({expected_lt(n,p)}) -> ~({n} = 0) -> ~({expected_multiple(p,n,'0')})")


def expected_structure(p,ab,ac,mb,mc,nb,nc,ib,ic,eb,ec):
    return expected_and(expected_tables(p,ab,ac,mb,mc,nb,nc,ib,ic),expected_cardinality(p,eb,ec),expected_laws(p),expected_characteristic(p))


PUBLIC_CASES=(
    (candidate.prime_field_enumeration_relation,('p','b','c'),expected_enumeration),
    (candidate.prime_field_cardinality_relation,('p','b','c'),expected_cardinality),
    (candidate.prime_field_unit_steps_relation,('p','b','c','n'),expected_steps),
    (candidate.prime_field_unit_trace_relation,('p','b','c','n','r'),expected_trace),
    (candidate.prime_field_unit_multiple_relation,('p','n','r'),expected_multiple),
    (candidate.prime_field_characteristic_relation,('p',),expected_characteristic),
    (candidate.prime_field_finite_structure_relation,('p','ab','ac','mb','mc','nb','nc','ib','ic','eb','ec'),expected_structure),
)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
def test_exact_independent_cardinality_trace_and_structure_definitions(builder,args,expected):
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*args,tag='independent',variables=args)),_closed_formula(binder+expected(*args)))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('term',('p+1','p*p','S (p+p)','39614081257132168796771975177'))
def test_compound_moduli_and_double_and_add_numerals_preserve_exact_ast(builder,args,expected,term):
    arguments=(term,)+args[1:]
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*arguments,tag='compound',variables=args)),_closed_formula(binder+expected(*arguments)))


@pytest.mark.parametrize('builder,args,binder',capture_cases(PUBLIC_CASES))
def test_every_nested_trace_beta_table_and_law_binder_is_hygienic(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=args+(binder,))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('context',((),[],('p','p'),('bad name',),('forall',)))
def test_malformed_finiteness_contexts_rejected(builder,args,expected,context):
    with pytest.raises(ValueError):
        builder(*('0' for _ in args),tag='context',variables=context)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('term',('unknown','p -> p','p = 0','p; true','',None,7,False))
def test_malformed_finiteness_terms_rejected(builder,args,expected,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='term',variables=args)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('tag',('bad tag','forall','S','',None,False))
def test_malformed_finiteness_tags_rejected(builder,args,expected,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


def test_trace_invariant_is_proved_from_actual_steps_not_assumed_in_definition():
    root=next(r for r in rows() if r.name=='prime_field_unit_trace_residue')
    expected=f"forall p n b c r. ({expected_prime('p')}) -> ({expected_trace('p','b','c','n','r')}) -> ({expected_residue('p','n','r')})"
    same_ast(_closed_formula(root.statement),_closed_formula(expected))
    assert 'induction n' in root.script
    assert 'prime_field_unit_trace_exists' not in root.dependencies
    constructor=next(r for r in rows() if r.name=='prime_field_unit_trace_exists')
    expected=f"forall p n. ({expected_prime('p')}) -> exists b c r. ({expected_trace('p','b','c','n','r')})"
    same_ast(_closed_formula(constructor.statement),_closed_formula(expected))
    assert 'induction n' in constructor.script


def test_exact_prime_order_structure_has_all_codes_no_extension_or_law_oracle_premise():
    root=next(r for r in rows() if r.name=='prime_field_of_prime_order_exists')
    args=('p','ab','ac','mb','mc','nb','nc','ib','ic','eb','ec')
    expected=f"forall p. ({expected_prime('p')}) -> exists {' '.join(args[1:])}. ({expected_structure(*args)})"
    same_ast(_closed_formula(root.statement),_closed_formula(expected))
    assert sha256(root.statement.encode()).hexdigest()==PRINCIPAL_SHA256[root.name]
    assert root.dependencies==('prime_field_operation_tables_exists','prime_field_cardinality_exists','prime_field_arithmetic_laws','prime_field_characteristic_exact')
    assert all('prime_field_of_prime_order_exists' not in r.dependencies for r in rows())


def test_characteristic_is_exact_positive_minimal_repeated_addition_length():
    root=next(r for r in rows() if r.name=='prime_field_characteristic_exact')
    expected=f"forall p. ({expected_prime('p')}) -> ({expected_characteristic('p')})"
    same_ast(_closed_formula(root.statement),_closed_formula(expected))
    assert sha256(root.statement.encode()).hexdigest()==PRINCIPAL_SHA256[root.name]


def test_existing_identity_selector_is_reused_without_new_fact_or_definition():
    inherited=core()['matrix_lattice_identity_selector_exists'].statement
    expected=f"forall p. exists b c. ({expected_enumeration('p','b','c')})"
    same_ast(_closed_formula(inherited),_closed_formula(expected))


@pytest.mark.parametrize('p',(0,1,2,3,5,7,11))
def test_actual_beta_bijection_has_exactly_p_canonical_elements(p):
    code=encode_beta(range(p))
    values=[decode_beta(*code,i) for i in range(p)]
    assert values==list(range(p))
    assert all(0<=a<p for a in values)
    assert len(set(values))==p
    assert all(any(decode_beta(*code,i)==a for i in range(p)) for a in range(p))


@pytest.mark.parametrize('p',(2,3,5,7))
@pytest.mark.parametrize('case',('empty','one','before','characteristic','after','twice','later'))
def test_actual_beta_unit_histories_include_initial_terminal_and_wrap_boundaries(p,case):
    n={'empty':0,'one':1,'before':p-1,'characteristic':p,'after':p+1,'twice':2*p,'later':2*p+3}[case]
    values=[i%p for i in range(n+1)]
    code=encode_beta(values)
    assert decode_beta(*code,0)==0
    assert decode_beta(*code,n)==n%p
    for i in range(n):
        before,after=decode_beta(*code,i),decode_beta(*code,i+1)
        assert 0<=before<p and 0<=after<p and (before+1)%p==after
    if 0<n<p:
        assert decode_beta(*code,n)!=0
    if n==p:
        assert decode_beta(*code,n)==0


def test_trace_steps_and_prime_guards_are_mathematically_necessary():
    # The all-zero two-entry code has start=0, end=0 and bounded entries, but
    # is NOT a one-step addition of one in F_2. Endpoint data alone cannot
    # justify the residue invariant.
    fake=encode_beta((0,0))
    assert decode_beta(*fake,0)==decode_beta(*fake,1)==0
    assert (decode_beta(*fake,0)+1)%2!=decode_beta(*fake,1)
    assert (2+1)%2!=0
    assert not 0<0 and not 1<1
    assert all((2*b)%4!=1 for b in range(4))


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    if sys.argv[1:2] == ["--body"]:
        print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")), flush=True)
    else:
        for name in sys.argv[1:] or tuple(row.name for row in rows()):
            print(json.dumps(check_body(name)), flush=True)
