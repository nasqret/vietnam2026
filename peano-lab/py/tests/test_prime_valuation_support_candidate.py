"""Non-admitting body checks against exact immutable Alpha-v28 hypotheses."""

from functools import lru_cache
from dataclasses import fields, is_dataclass, replace
import gc
from hashlib import sha256
import json
from math import prod
from pathlib import Path
import re

import pytest

from peano_lab.library import prime_valuation_support_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.bertrand_power_divisibility_candidate import _power_valuation_terms
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.finite_fold_surface import _beta_at_term, _product_relation_term
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "artifacts/peano-library/alpha/catalog-v28.json"
PARENT_SHA256 = "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9"


@lru_cache(maxsize=1)
def core():
    raw = PARENT.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    catalog = json.loads(raw)
    assert catalog["theorem_count"] == catalog["checked_use_count"] == 2764
    assert catalog["stable_count"] == 432
    return {r["name"]: TheoremSpec(r["name"], r["statement"], tuple(r["dependencies"]), tuple(r["script"]), r["summary"]) for r in catalog["theorems"]}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_valuation_support_candidate_theorems(TheoremSpec)


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_original_kernel_body(row):
    try:
        receipt = replay_candidate_bodies((row,), core=core() | {r.name: r for r in rows()})[0]
        assert receipt.name == row.name
        assert receipt.proof_depth <= 256
        assert receipt.proof_objects <= receipt.proof_nodes
        print(f"{row.name}: {receipt.proof_nodes}/{receipt.proof_depth}/{receipt.proof_objects}")
    finally:
        gc.collect()


def test_additive_dependency_order_and_ordinary_commands():
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert all(re.search(r"(?<![\w'])" + re.escape(d) + r"(?![\w'])", "\n".join(row.script)) for d in row.dependencies)
        assert not any(command.startswith(("use ", "admit", "sorry", "DNE", "ring")) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


def _at(b, c, i, p, tag):
    return _beta_at_term(b, c, i, p, tag=tag, avoid=())


def _expected_support(n="n"):
    # Deliberately independent assembly from the historical PA relations.
    injective = (
        "forall i j p. (exists h. h + S i = l) -> (exists h. h + S j = l) -> "
        f"({_at('pb','pc','i','p','expected_first')}) -> "
        f"({_at('pb','pc','j','p','expected_second')}) -> i = j"
    )
    entry = (
        "forall i. (exists h. h + S i = l) -> exists p e v. "
        f"({_at('pb','pc','i','p','expected_p')}) /\\ "
        f"(({_at('eb','ec','i','e','expected_e')}) /\\ "
        f"(({_at('vb','vc','i','v','expected_v')}) /\\ "
        f"(({prime('p',tag='expected_prime')}) /\\ (~(e = 0) /\\ "
        f"(({_power_valuation_terms('p',n,'e',tag='expected_val')}) /\\ "
        f"({_power_terms('p','e','v',tag='expected_power')}))))))"
    )
    cover = (
        f"forall p. ({prime('p',tag='expected_cover_prime')}) -> "
        f"(exists q. {n} = p * q) -> exists i. "
        f"(exists h. h + S i = l) /\\ ({_at('pb','pc','i','p','expected_cover_at')})"
    )
    product = _product_relation_term("vb","vc","l",n,tag="expected_product",avoid=())
    return f"~({n} = 0) /\\ (({injective}) /\\ (({entry}) /\\ (({cover}) /\\ ({product}))))"


def _assert_same_ast(left, right):
    # A structural audit, not proof checking.  Avoid recursive dataclass __eq__
    # for deeply nested double-and-add numerals; no process/kernel cap changes.
    pending, seen = [(left,right)], set()
    while pending:
        first, second = pending.pop()
        assert type(first) is type(second)
        pair = (id(first),id(second))
        if pair in seen:
            continue
        seen.add(pair)
        if is_dataclass(first):
            pending.extend((getattr(first,f.name),getattr(second,f.name)) for f in fields(first))
        else:
            assert first == second


def test_public_support_is_the_exact_non_oracular_contract():
    names = ("n","pb","pc","eb","ec","vb","vc","l")
    rendered = candidate.prime_valuation_support_relation(*names,tag="contract",variables=names)
    binder = "forall " + " ".join(names) + ". "
    assert _closed_formula(binder+rendered) == _closed_formula(binder+_expected_support())
    expected_root = "forall n. ~(n = 0) -> exists pb pc eb ec vb vc l. (" + _expected_support() + ")"
    root = next(r for r in rows() if r.name == "prime_valuation_support_exists")
    assert _closed_formula(root.statement) == _closed_formula(expected_root)


@pytest.mark.parametrize("name,output", [
    ("prime_power_valuation_pow_value", "f = k * e"),
    ("prime_power_valuation_pow", None),
])
def test_scalar_power_contract_independently_matches(name, output):
    prefix = "forall p a k e z" + (" f" if output else "") + ". "
    expected = prefix + (
        f"({prime('p',tag='expected_scalar_domain')}) -> ~(a = 0) -> "
        f"({_power_valuation_terms('p','a','e',tag='expected_scalar_base')}) -> "
        f"({_power_terms('a','k','z',tag='expected_scalar_power')}) -> "
    )
    if output:
        expected += f"({_power_valuation_terms('p','z','f',tag='expected_scalar_target')}) -> {output}"
    else:
        expected += _power_valuation_terms("p","z","k * e",tag="expected_scalar_target")
    assert _closed_formula(next(r for r in rows() if r.name == name).statement) == _closed_formula(expected)


@pytest.mark.parametrize("value", ["n + 1", "n * n", "S (n + n)", "123456789012345678901234567890"])
def test_public_relation_accepts_compound_and_large_terms(value):
    names = ("n","pb","pc","eb","ec","vb","vc","l")
    actual = candidate.prime_valuation_support_relation(value,*names[1:],tag="compound",variables=names)
    binder = "forall " + " ".join(names) + ". "
    _assert_same_ast(_closed_formula(binder+actual), _closed_formula(binder+_expected_support("("+value+")")))


@pytest.mark.parametrize("tag,variables,argument", [
    ("bad tag", ("n",), "n"),
    ("t", (), "0"),
    ("t", ("n","n"), "n"),
    ("t", ("n",), "unknown"),
    ("t", ("pvs_index_tentries",), "pvs_index_tentries"),
    ("t", ("n",), "n -> n"),
])
def test_public_hygiene_rejects_capture_or_malformed_inputs(tag, variables, argument):
    with pytest.raises(ValueError):
        candidate.prime_valuation_support_relation(argument,"0","0","0","0","0","0","0",tag=tag,variables=variables)


@pytest.mark.parametrize("name", ["prime_power_valuation_pow", "prime_valuation_support_exists"])
def test_poisoned_endpoint_rejected_by_unchanged_kernel(name):
    original = next(r for r in rows() if r.name == name)
    poisoned = replace(original, statement="0 = 1")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((poisoned,), core=core() | {r.name:r for r in rows()})


def _integer_profile(n):
    if n < 1:
        raise ValueError("the support theorem concerns positive naturals")
    remaining, p, result = n, 2, []
    while p*p <= remaining:
        exponent = 0
        while remaining % p == 0:
            remaining //= p
            exponent += 1
        if exponent:
            result.append((p,exponent,p**exponent))
        p += 1
    if remaining > 1:
        result.append((remaining,1,remaining))
    return result


@pytest.mark.parametrize("n", [1,2,4,8,9,12,30,36,72,210,360,1024,99991,2**17*3**5*13])
def test_support_mathematical_boundary_examples(n):
    # Independent executable examples, not a substitute for the HA derivations.
    profile = _integer_profile(n)
    primes = [p for p,e,v in profile]
    assert len(primes) == len(set(primes))
    assert prod(v for p,e,v in profile) == n
    for p,e,v in profile:
        assert all(p%d for d in range(2,int(p**0.5)+1))
        assert e > 0 and v == p**e and n%v == 0 and (n//v)%p != 0
    if n == 1:
        assert profile == []
    else:
        assert profile


@pytest.mark.parametrize("prime_value", [2,3,5,7,11])
@pytest.mark.parametrize("base", [1,2,9,12,72])
@pytest.mark.parametrize("exponent", [0,1,2,5])
def test_power_valuation_integer_examples(prime_value,base,exponent):
    def valuation(n):
        result = 0
        while n%prime_value == 0:
            n //= prime_value
            result += 1
        return result
    assert valuation(base**exponent) == exponent*valuation(base)


def test_zero_not_given_a_positive_support_profile():
    with pytest.raises(ValueError):
        _integer_profile(0)
