"""Fresh original-kernel candidate-body checks; no Alpha admission authority."""

from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass, replace
from functools import lru_cache
from hashlib import sha256
import json
import inspect
import os
from pathlib import Path
import resource
import re
import signal
import subprocess
import sys

import pytest

from peano_lab.library import prime_field_arithmetic_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT_SHA256 = "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
SOURCE_SHA256 = "d4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90"
NAMES_SHA256 = "649916815968663d6bf4fadbf8438a3f8d15bf6781e80679e18dd5451fe29eca"
LAWS_SHA256 = "d6c324daa2e1d8a11b13e15710ddcd43e3b3623790e0ad247ce18eae318f3f29"


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_arithmetic_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    raw = (ROOT / "artifacts/peano-library/alpha/catalog-v30.json").read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    document = json.loads(raw)
    assert document["theorem_count"] == document["checked_use_count"] == 3222
    assert document["stable_count"] == 432
    # Exact inherited statements are hypotheses for these curried body checks,
    # not a substitute for later actual closed dependency reconstruction.
    return {r["name"]: TheoremSpec(r["name"], r["statement"], tuple(r["dependencies"]),
                                 tuple(r["script"]), r["summary"]) for r in document["theorems"]}


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
    elif mutation == "zero_inverse_domain":
        row = replace(row, statement=f"forall p a. ({expected_prime('p')}) -> ({expected_lt('a','p')}) -> exists b. ({expected_inv('p','a','b')})")
    elif mutation == "composite_inverse_domain":
        row = replace(row, statement=f"forall p a. ({expected_lt('1','p')}) -> ({expected_lt('a','p')}) -> ~(a = 0) -> exists b. ({expected_inv('p','a','b')})")
    elif mutation != "none":
        raise ValueError("unknown prime-field proof mutation")
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
    assert receipt["name"] == name
    assert receipt["proof_depth"] <= 256
    assert receipt["proof_objects"] <= receipt["proof_nodes"]


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
@pytest.mark.parametrize("mutation", ("false_conclusion", "truncated_body"))
def test_false_or_incomplete_actual_proof_is_rejected(name, mutation):
    assert isolated_body(name, mutation)["rejected"] is True


@pytest.mark.parametrize("name", tuple(row.name for row in rows() if row.dependencies))
@pytest.mark.parametrize("mutation", ("removed_dependency", "corrupt_dependency"))
def test_missing_or_forged_actual_dependency_is_rejected(name, mutation):
    assert isolated_body(name, mutation)["rejected"] is True


@pytest.mark.parametrize("mutation", ("zero_inverse_domain", "composite_inverse_domain"))
def test_inverse_proof_cannot_drop_nonzero_or_prime_guards(mutation):
    assert isolated_body("prime_field_inverse_exists", mutation)["rejected"] is True


def test_exact_frozen_inventory_and_actual_dependency_topology():
    assert len(rows()) == 42
    assert sum(len(row.dependencies) for row in rows()) == 120
    assert sum(len(row.script) for row in rows()) == 1209
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest() == SOURCE_SHA256
    assert sha256(("\n".join(row.name for row in rows()) + "\n").encode()).hexdigest() == NAMES_SHA256
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(row.dependencies) == len(set(row.dependencies))
        for name in row.dependencies:
            assert re.search(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", "\n".join(row.script))
        assert row.script and not any(command.startswith(("use ", "admit", "sorry")) or "DNE" in command for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)
    # These identical historical contracts are reused rather than relabelled
    # as additional new facts.
    assert {"prime_field_residue_exists", "prime_field_residue_functional", "prime_field_one_below_prime"}.isdisjoint(available)
    dependencies = {name for row in rows() for name in row.dependencies}
    assert {"hensel_canonical_residue_exists", "binary_canonical_residue_functional", "prime_two_le"} <= dependencies


def expected_and(*parts):
    result = f"({parts[-1]})"
    for part in reversed(parts[:-1]):
        result = f"({part}) /\\ ({result})"
    return result


def expected_lt(a, b):
    return f"exists independent_gap. independent_gap + S ({a}) = ({b})"


def expected_mod(p, a, b):
    return f"exists independent_left independent_right. ({a}) + ({p}) * independent_left = ({b}) + ({p}) * independent_right"


def expected_prime(p):
    return f"~(({p}) = 1) /\\ forall independent_prime_a independent_prime_b. ({p}) = independent_prime_a * independent_prime_b -> independent_prime_a = 1 \\/ independent_prime_b = 1"


def expected_residue(p, n, r):
    return expected_and(expected_lt(r,p), expected_mod(p,n,r))


def expected_add(p, a, b, c):
    return expected_and(expected_lt(a,p), expected_lt(b,p), expected_lt(c,p), expected_mod(p,f"({a})+({b})",c))


def expected_mul(p, a, b, c):
    return expected_and(expected_lt(a,p), expected_lt(b,p), expected_lt(c,p), expected_mod(p,f"({a})*({b})",c))


def expected_neg(p, a, b):
    return expected_add(p,a,b,"0")


def expected_inv(p, a, b):
    return expected_and(f"~(({a})=0)", expected_mul(p,a,b,"1"))


def expected_laws(p):
    # Independently assembled mathematical contract; no candidate law or
    # operation builder is used on this expected side.
    clauses = [expected_lt("0",p), expected_lt("1",p), "~(0 = 1)"]
    for graph in (expected_add, expected_mul):
        clauses.append(f"forall a b. ({expected_lt('a',p)}) -> ({expected_lt('b',p)}) -> exists c. ({graph(p,'a','b','c')}) /\\ forall d. ({graph(p,'a','b','d')}) -> d = c")
        clauses.append(f"forall a b c. ({graph(p,'a','b','c')}) -> ({graph(p,'b','a','c')})")
        rels = (graph(p,'a','b','x'),graph(p,'x','c','u'),graph(p,'b','c','y'),graph(p,'a','y','v'))
        clauses.append("forall a b c x y u v. " + " -> ".join(f"({r})" for r in rels) + " -> u = v")
    for left in (True,False):
        factors = (('a','s'),('a','b'),('a','c')) if left else (('s','a'),('b','a'),('c','a'))
        rels = (expected_add(p,'b','c','s'),expected_mul(p,*factors[0],'u'),expected_mul(p,*factors[1],'x'),expected_mul(p,*factors[2],'y'),expected_add(p,'x','y','v'))
        clauses.append("forall a b c s x y u v. " + " -> ".join(f"({r})" for r in rels) + " -> u = v")
    for graph in (expected_add(p,'a','0','a'),expected_add(p,'0','a','a'),expected_mul(p,'a','1','a'),expected_mul(p,'1','a','a'),expected_mul(p,'a','0','0'),expected_mul(p,'0','a','0')):
        clauses.append(f"forall a. ({expected_lt('a',p)}) -> ({graph})")
    for graph, guard in ((expected_neg,""),(expected_inv,"~(a = 0) -> ")):
        clauses.append(f"forall a. ({expected_lt('a',p)}) -> {guard}exists b. ({graph(p,'a','b')}) /\\ forall c. ({graph(p,'a','c')}) -> c = b")
    clauses.append(f"forall a b. ({expected_mul(p,'a','b','0')}) -> a = 0 \\/ b = 0")
    assert len(clauses) == 20
    return expected_and(*clauses)


PUBLIC_CASES = (
    (candidate.prime_field_carrier_relation,("p","a"),lambda p,a: expected_and(expected_prime(p),expected_lt(a,p))),
    (candidate.prime_field_residue_relation,("p","n","r"),expected_residue),
    (candidate.prime_field_add_relation,("p","a","b","c"),expected_add),
    (candidate.prime_field_multiply_relation,("p","a","b","c"),expected_mul),
    (candidate.prime_field_negate_relation,("p","a","b"),expected_neg),
    (candidate.prime_field_inverse_relation,("p","a","b"),expected_inv),
    (candidate.prime_field_laws_relation,("p",),expected_laws),
)


def same_ast(left, right):
    """Iterative structural equality, including compact double-and-add DAGs."""
    pending, seen = [(left,right)], set()
    while pending:
        a,b = pending.pop()
        assert type(a) is type(b)
        pair = (id(a),id(b))
        if pair in seen:
            continue
        seen.add(pair)
        if is_dataclass(a):
            pending.extend((getattr(a,f.name),getattr(b,f.name)) for f in fields(a))
        else:
            assert a == b


@pytest.mark.parametrize("builder,args,expected", PUBLIC_CASES, ids=lambda value: value.__name__ if callable(value) else None)
def test_public_graphs_are_exact_independently_assembled_ha(builder,args,expected):
    binder = "forall " + " ".join(args) + ". "
    same_ast(_closed_formula(binder+builder(*args,tag="independent",variables=args)),_closed_formula(binder+expected(*args)))


@pytest.mark.parametrize("builder,args,expected", PUBLIC_CASES)
@pytest.mark.parametrize("term", ("p + 1", "p * p", "S (p + p)", "39614081257132168796771975177"))
def test_public_graphs_preserve_compound_and_large_terms(builder,args,expected,term):
    arguments = (term,)+args[1:]
    binder = "forall " + " ".join(args) + ". "
    same_ast(_closed_formula(binder+builder(*arguments,tag="compound",variables=args)),_closed_formula(binder+expected(*arguments)))


def capture_cases(public_cases):
    cases = []
    for builder,args,_ in public_cases:
        graph = builder(*args,tag="capture",variables=args)
        binders = sorted({name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.",graph) for name in clause.split()})
        cases.extend((builder,args,binder) for binder in binders)
    return tuple(cases)


@pytest.mark.parametrize("builder,args,binder", capture_cases(PUBLIC_CASES))
def test_every_generated_binder_rejects_entire_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match="captures"):
        builder(*args,tag="capture",variables=args+(binder,))


@pytest.mark.parametrize("builder,args,expected", PUBLIC_CASES)
@pytest.mark.parametrize("context", ((),[],("p","p"),("bad name",),("forall",)))
def test_invalid_declared_context_is_rejected(builder,args,expected,context):
    with pytest.raises(ValueError):
        builder(*("0" for _ in args),tag="context",variables=context)


@pytest.mark.parametrize("builder,args,expected", PUBLIC_CASES)
@pytest.mark.parametrize("term", ("unknown", "p -> p", "p = 0", "p; true", "", None, 7, False))
def test_nonterms_and_undeclared_variables_are_rejected(builder,args,expected,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag="bad_term",variables=args)


@pytest.mark.parametrize("builder,args,expected", PUBLIC_CASES)
@pytest.mark.parametrize("tag", ("bad tag","forall","S","",None,False))
def test_invalid_definition_tags_are_rejected(builder,args,expected,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


def test_full_field_laws_have_only_the_actual_prime_premise():
    root = next(row for row in rows() if row.name == "prime_field_arithmetic_laws")
    assert sha256(root.statement.encode()).hexdigest() == LAWS_SHA256
    same_ast(_closed_formula(root.statement),_closed_formula(f"forall p. ({expected_prime('p')}) -> ({expected_laws('p')})"))
    assert all("prime_field_arithmetic_laws" not in row.dependencies for row in rows())


@pytest.mark.parametrize("p", (2,3,5,7,11,13))
def test_independent_small_prime_field_model(p):
    # Exhaustive small examples are explanatory regression tests, NOT the
    # formal proof. The original-HA tests above handle arbitrary prime p.
    add = lambda a,b: (a+b)%p
    mul = lambda a,b: (a*b)%p
    for a in range(p):
        assert add(a,0)==a==add(0,a)
        assert mul(a,1)==a==mul(1,a)
        assert mul(a,0)==0==mul(0,a)
        negatives = [b for b in range(p) if add(a,b)==0]
        assert negatives==[(-a)%p]
        inverses = [b for b in range(p) if mul(a,b)==1]
        assert len(inverses)==(0 if a==0 else 1)
        for b in range(p):
            assert add(a,b)==add(b,a) and mul(a,b)==mul(b,a)
            assert (mul(a,b)==0)==(a==0 or b==0)
            for c in range(p):
                assert add(add(a,b),c)==add(a,add(b,c))
                assert mul(mul(a,b),c)==mul(a,mul(b,c))
                assert mul(a,add(b,c))==add(mul(a,b),mul(a,c))
                assert mul(add(b,c),a)==add(mul(b,a),mul(c,a))


def test_zero_composite_and_out_of_carrier_cases_are_real_boundaries():
    assert 2*2%4==0 and all(2*b%4!=1 for b in range(4))
    assert all(0*b%2!=1 for b in range(2))
    assert 1%1==0%1  # one is not a canonical representative modulo one
    assert not 0<0 and not 2<2
    assert ((1+1)%2,(-1)%2,(1*1)%2)==(0,1,1)


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    if sys.argv[1:2] == ["--body"]:
        print(json.dumps(check_body(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")), flush=True)
    else:
        for name in sys.argv[1:] or tuple(row.name for row in rows()):
            print(json.dumps(check_body(name)), flush=True)
