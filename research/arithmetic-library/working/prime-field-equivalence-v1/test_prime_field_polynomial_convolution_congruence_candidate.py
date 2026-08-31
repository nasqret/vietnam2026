"""Independent mixed-length contracts, beta models and original HA checks.

Only actual source-provider specifications are used as conditional premises.
No Alpha edition or Lean checker is loaded and no proof bundle is decoded.
Old proof bytes are read only for preservation hashes. No saved receipt or
successful proof simulation is used, and these checks admit no working row.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import gc
import importlib.util
import itertools
import json
from pathlib import Path
import resource
import signal
import sys
import time

STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from peano_lab.kernel.formulas import parse_formula_with_names
from working_equivalence_support import REPRESENTATION_ALIAS, temporary_representation_alias


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "prime-field-euclidean-v1"


def load_source(path, alias):
    if alias in sys.modules:
        module = sys.modules[alias]
        assert Path(module.__file__).resolve() == path
        return module
    specification = importlib.util.spec_from_file_location(alias, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[alias] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(alias) is module:
            del sys.modules[alias]
        raise
    return module


# This frozen test module supplies independently expanded elementary syntax
# and actual CRT/beta-sum examples, not a mathematical acceptance fixture.
# The unchanged model loader borrows only this scope's actual representation
# module. Its retained references do not require a persistent library alias.
with temporary_representation_alias():
    models = load_source(PRIOR / "test_prime_field_polynomial_convolution_padding_candidate.py",
                         "working_congruence_independent_padding_models")
    candidate = load_source(HERE / "prime_field_polynomial_convolution_congruence_candidate.py",
                            "working_prime_field_polynomial_convolution_congruence_candidate")
    converse = load_source(HERE / "prime_field_polynomial_equivalence_candidate.py",
                           "working_congruence_actual_equivalence_provider")

EXPECTED_NAMES = (
    "prime_field_polynomial_convolution_equivalent_congruent_left",
    "prime_field_polynomial_convolution_equivalent_congruent_right",
    "prime_field_polynomial_convolution_equivalent_congruent",
)
EXPECTED_METRICS = ((162, 48), (162, 48), (118, 55))
SOURCE_SHA256 = "effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70"
CONVERSE_SHA256 = "929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373"
EXPECTED_SPECS_SHA256 = "b0da9dd22a52c42045fd22ac189fb9d7fc92365527818f5a61e0f4a71d1be7e6"
PRESERVED = {
    "prime_field_polynomial_convolution_triangular_candidate.py": "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f",
    "prime_field_polynomial_representation_candidate.py": "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a",
    "prime_field_polynomial_division_candidate.py": "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2",
    "prime_field_polynomial_distributivity_candidate.py": "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86",
    "prime_field_polynomial_division_uniqueness_candidate.py": "6a9d9ebe1f72202743e5df2c069b9aa367fdb3d61108f1d9354cdc9276ab2d15",
    "prime_field_polynomial_convolution_padding_candidate.py": "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007",
    "test_prime_field_polynomial_convolution_padding_candidate.py": "7632654e36e18cf7c872bd29dd783a55cf597e33e7b5369be178a2d2f42b87f9",
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_convolution_congruence_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    result = dict(models.body_core())
    actual = converse.make_prime_field_polynomial_equivalence_candidate_theorems(TheoremSpec)
    assert type(actual) is tuple
    for row in actual:
        assert type(row) is TheoremSpec
        assert row.name not in result or result[row.name] == row
        result[row.name] = row
    assert "prime_field_polynomial_equivalent_implies_left_pad" in result
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


def contracts():
    result = []
    for side in ("left", "right"):
        source = ("ab", "ac", "L") if side == "left" else ("bb", "bc", "M")
        replacement = ("AB", "AC", "H") if side == "left" else ("BB", "BC", "H")
        factors = (*replacement, "bb", "bc", "M") if side == "left" else ("ab", "ac", "L", *replacement)
        parameters = ("p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "N", *replacement, "CB", "CC", "K")
        result.append((" ".join(parameters), (
            "~(p=0)", models.equivalent(*source, *replacement),
            models.product("p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "N"),
            models.product("p", *factors, "CB", "CC", "K"),
        ), models.equivalent("cb", "cc", "N", "CB", "CC", "K")))
    result.append(("p ab ac L bb bc M cb cc N AB AC H BB BC I CB CC K", (
        "~(p=0)", models.equivalent("ab", "ac", "L", "AB", "AC", "H"),
        models.equivalent("bb", "bc", "M", "BB", "BC", "I"),
        models.product("p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "N"),
        models.product("p", "AB", "AC", "H", "BB", "BC", "I", "CB", "CC", "K"),
    ), models.equivalent("cb", "cc", "N", "CB", "CC", "K")))
    return tuple(result)


def test_exact_local_names_order_and_distinct_direct_provider_statements():
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert len(rows()) == len(contracts()) == 3
    records = [[row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
               for row in rows()]
    serialized = "".join(json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n"
                         for record in records)
    assert sha256(serialized.encode()).hexdigest() == EXPECTED_SPECS_SHA256
    old = provider_core()
    positions = {row.name: index for index, row in enumerate(rows())}
    identities = []
    for row in rows():
        assert type(row) is TheoremSpec and row.script
        assert len(row.dependencies) == len(set(row.dependencies))
        assert all(name in old or name in positions and positions[name] < positions[row.name]
                   for name in row.dependencies)
        identity = models.exact_ast(row.statement)
        assert identity not in identities
        identities.append(identity)
    for row in old.values():
        assert models.exact_ast(row.statement) not in identities


@pytest.mark.parametrize("name", tuple(PRESERVED))
def test_preserved_working113_sources_remain_byte_exact(name):
    assert sha256((PRIOR / name).read_bytes()).hexdigest() == PRESERVED[name]


@pytest.mark.parametrize("name,digest", (
    ("prime_field_polynomial_convolution_congruence_candidate.py", SOURCE_SHA256),
    ("prime_field_polynomial_equivalence_candidate.py", CONVERSE_SHA256),
))
def test_new_candidate_and_actual_converse_source_have_final_pins(name, digest):
    assert type(digest) is str and len(digest) == 64
    assert sha256((HERE / name).read_bytes()).hexdigest() == digest


def test_only_actual_source_syntax_and_existing_graphs_are_loaded():
    assert not any(name.startswith("peano_lab.library.editions") for name in sys.modules)
    assert candidate.__all__ == ["make_prime_field_polynomial_convolution_congruence_candidate_theorems"]
    source = (HERE / "prime_field_polynomial_convolution_congruence_candidate.py").read_text()
    assert "import editions" not in source and "def _equivalent(" not in source
    assert "def _convolution(" not in source and "def _left_pad(" not in source
    import peano_lab.library as library
    assert REPRESENTATION_ALIAS not in sys.modules
    assert REPRESENTATION_ALIAS.rsplit(".", 1)[1] not in vars(library)


@pytest.mark.parametrize("index", range(3))
def test_independently_expanded_original_contract(index):
    expected = models.format_contract(*contracts()[index])
    assert models.exact_ast(rows()[index].statement) == models.exact_ast(expected)
    formula, free = parse_formula_with_names(rows()[index].statement)
    assert free == () and formula == _closed_formula(expected)


def test_real_converse_is_exact_and_has_no_domain_or_output_identity_premise():
    row = provider_core()["prime_field_polynomial_equivalent_implies_left_pad"]
    expected = models.format_contract("b c L t d e",
        (models.equivalent("b", "c", "L", "d", "e", "t+L"),),
        models.left_pad("b", "c", "L", "t", "d", "e"))
    assert models.exact_ast(row.statement) == models.exact_ast(expected)


def check_actual_body(row):
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == row.name and receipt.dependency_count == len(row.dependencies)
    assert receipt.command_count == len(row.script)
    assert 0 < receipt.proof_objects <= receipt.proof_nodes
    print(json.dumps(asdict(receipt), sort_keys=True), flush=True)
    gc.collect()
    return receipt


@pytest.mark.parametrize("index", range(3), ids=EXPECTED_NAMES)
def test_original_ha_body(index):
    receipt = check_actual_body(rows()[index])
    assert len(EXPECTED_METRICS) == 3
    assert (receipt.proof_nodes, receipt.proof_depth) == EXPECTED_METRICS[index]


@pytest.mark.parametrize("index", range(3))
def test_false_conclusion_is_rejected(index):
    names, premises, _ = contracts()[index]
    changed = replace(rows()[index], statement=models.format_contract(names, premises, "0=1"))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_missing_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=()),), core=body_core())


EDGES = tuple((row, name) for row in rows() for name in row.dependencies)


@pytest.mark.parametrize("row,dependency", EDGES, ids=lambda item: item.name if hasattr(item, "name") else item)
def test_each_removed_dependency_is_rejected(row, dependency):
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize("row,dependency", EDGES, ids=lambda item: item.name if hasattr(item, "name") else item)
def test_each_poisoned_dependency_is_rejected(row, dependency):
    core = body_core()
    core[dependency] = replace(core[dependency], statement="0=0")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,), core=core)


REMOVED_PREMISES = tuple((index, position) for index, (_, premises, _) in enumerate(contracts())
                         for position in range(len(premises)))


@pytest.mark.parametrize("index,position", REMOVED_PREMISES)
def test_each_actual_equivalence_product_or_modulus_premise_is_required(index, position):
    names, premises, conclusion = contracts()[index]
    changed = replace(rows()[index], statement=models.format_contract(names,
        tuple(premise for at, premise in enumerate(premises) if at != position), conclusion))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


def hostile_contracts():
    result = []
    for index, (names, premises, conclusion) in enumerate(contracts()):
        for label, wrong in (
            ("raw_beta_codes", "cb=CB"),
            ("representation_lengths", "N=K"),
            ("unshifted_prefix_equality", models.equal("cb", "cc", "CB", "CC", "N")),
        ):
            result.append((index, label, models.format_contract(names, premises, wrong)))
        for position in range(1, len(premises)):
            changed = list(premises)
            changed[position] = "0=0"
            result.append((index, "same_arity_missing_actual_premise_" + str(position),
                           models.format_contract(names, tuple(changed), conclusion)))
    return tuple(result)


@pytest.mark.parametrize("index,label,statement", hostile_contracts(), ids=lambda value: value if isinstance(value, str) and len(value) < 90 else None)
def test_stronger_or_unjustified_representation_contract_is_rejected(index, label, statement):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())


def formal_equivalent(first, first_length, second, second_length):
    return all(models.model_power(first, first_length, k) == models.model_power(second, second_length, k)
               for k in range(max(first_length, second_length) + 3))


def assert_actual_padding_in_comparable_direction(first, L, second, H):
    if H < L:
        first, L, second, H = second, H, first, L
    count = H - L
    assert all(models.beta(second, j) == 0 for j in range(count))
    assert all(models.beta(first, i) == models.beta(second, count + i) for i in range(L))


def actual_cross_product(p, A, L, B, M, salt):
    N = L + M - 1 if L and M else 0
    values = tuple(models.actual_coefficient(p, A, L, B, M, i)[0] for i in range(N))
    result = models.encode_beta((*values, p + 29, p + 31), salt)
    assert all(models.beta(result, i) == value for i, value in enumerate(values))
    assert models.beta(result, N) >= p
    return result, N


MODEL_CASES = tuple((p, A, B, pads_a, pads_b)
    for p in (1, 2, 3, 5, 6)
    for A, B in (
        ((), ()), ((), (1 % p, 1 % p)), ((1 % p, 1 % p), ()),
        ((0,), (0,)), ((1 % p, p - 1), (p - 1, 1 % p)),
        ((0, 1 % p, p - 1), (0, p - 1)),
    )
    for pads_a, pads_b in itertools.product(((0, 0), (0, 2), (2, 0)), repeat=2))


@pytest.mark.parametrize("p,A,B,pads_a,pads_b", MODEL_CASES)
def test_actual_beta_products_cover_every_independent_length_direction(p, A, B, pads_a, pads_b):
    first_a, other_a = ((0,) * count + A for count in pads_a)
    first_b, other_b = ((0,) * count + B for count in pads_b)
    a, b, c, values = models.actual_product(p, first_a, first_b, 2)
    Acode, Bcode, Ccode, other_values = models.actual_product(p, other_a, other_b, 11)
    L, M, H, I = map(len, (first_a, first_b, other_a, other_b))
    assert formal_equivalent(a, L, Acode, H)
    assert formal_equivalent(b, M, Bcode, I)
    assert_actual_padding_in_comparable_direction(a, L, Acode, H)
    assert_actual_padding_in_comparable_direction(b, M, Bcode, I)
    middle, J = actual_cross_product(p, Acode, H, b, M, 23)
    assert formal_equivalent(c, len(values), middle, J)
    assert formal_equivalent(middle, J, Ccode, len(other_values))
    assert formal_equivalent(c, len(values), Ccode, len(other_values))
    assert c != Ccode


def test_real_counterexamples_exclude_code_length_evaluation_and_unit_shortcuts():
    assert len(MODEL_CASES) == 270 and {case[0] for case in MODEL_CASES} == {1, 2, 3, 5, 6}
    directions = {tuple((pair[1] > pair[0]) - (pair[1] < pair[0]) for pair in (pa, pb))
                  for _p, _a, _b, pa, pb in MODEL_CASES}
    assert directions == set(itertools.product((-1, 0, 1), repeat=2))
    _, _, first, values = models.actual_product(2, (1,), (1,), 1)
    _, _, padded, padded_values = models.actual_product(2, (0, 1), (1,), 9)
    assert formal_equivalent(first, len(values), padded, len(padded_values))
    assert len(values) != len(padded_values) and first != padded
    assert models.beta(first, 0) != models.beta(padded, 0)
    _, _, false_output, zeros = models.actual_product(2, (0,), (1,), 3)
    assert not formal_equivalent(first, len(values), false_output, len(zeros))
    _, _, evaluation_zero, evaluation_values = models.actual_product(2, (1, 1, 0), (1,), 4)
    assert all((x * x + x) % 2 == 0 for x in (0, 1))
    assert not formal_equivalent(evaluation_zero, len(evaluation_values), false_output, len(zeros))
    _, _, one, ones = models.actual_product(3, (1,), (1,), 6)
    _, _, unit_multiple, twos = models.actual_product(3, (2,), (1,), 7)
    assert not formal_equivalent(one, len(ones), unit_multiple, len(twos))
    assert all(0 <= value < 0 for value in ())
    assert not all(0 <= value < 0 for value in (0,))


def _main(arguments):
    if arguments[:1] == ["--bodies"]:
        start = int(arguments[1]) if len(arguments) > 1 else 0
        count = int(arguments[2]) if len(arguments) > 2 else len(rows())
        assert start >= 0 and count > 0
        chosen = rows()[start:start + count]
        assert len(chosen) == count
        for row in chosen:
            check_actual_body(row)
        status = 0
    elif arguments[:1] == ["--pytest"]:
        class Outcomes:
            def __init__(self):
                self.selected, self.passed, self.bad = [], set(), []

            def pytest_collection_finish(self, session):
                self.selected = [item.nodeid for item in session.items]

            def pytest_runtest_logreport(self, report):
                if report.when == "call" and report.passed:
                    self.passed.add(report.nodeid)
                if report.failed or report.skipped or hasattr(report, "wasxfail"):
                    self.bad.append(report.nodeid)

        outcomes = Outcomes()
        status = int(pytest.main([str(Path(__file__).resolve()), "-p", "no:cacheprovider", *arguments[1:]], plugins=[outcomes]))
        if "--collect-only" not in arguments:
            assert outcomes.selected and len(outcomes.selected) == len(set(outcomes.selected))
            assert not outcomes.bad and outcomes.passed == set(outcomes.selected)
        print(json.dumps({"selected": len(outcomes.selected), "passed": len(outcomes.passed),
            "selected_ids_sha256": sha256(("\n".join(outcomes.selected) + "\n").encode()).hexdigest()}, sort_keys=True), flush=True)
    else:
        raise SystemExit("expected --bodies START COUNT or --pytest PYTEST_ARGUMENTS")
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    if sys.platform != "darwin":
        peak *= 1024
    assert 0 < peak <= 1536 * 1024 * 1024 and time.monotonic() - STARTED < 180
    print(json.dumps({"status": status, "seconds": time.monotonic() - STARTED,
        "cpu_seconds": time.process_time(), "peak_rss_bytes": peak,
        "cpu_limits": list(resource.getrlimit(resource.RLIMIT_CPU)), "wall_seconds": 180}, sort_keys=True), flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
