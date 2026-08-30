"""Independent monic graphs, real beta diagnostics and original HA bodies.

The small provider map supplies exact ordinary hypotheses, not accepted
dependency proofs.  Full current-parent novelty, dependency closure and any
independent compiled checker belong to the separate tranche integration.
These tests do not create an admission receipt or a polynomial field oracle.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import math
from pathlib import Path
import re

import pytest

from peano_lab.library import prime_field_polynomial_monic_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula


SOURCE_SHA256 = "3bf93aff71b48a332920b1a6174e44167bf78238caac3b6d35634f3591582eef"
PROVIDER_PINS = {
    "theorems.py": "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "bertrand_power_valuation_laws_candidate.py": "7b95e4f2a16df3866cb3e01f17d1b455000706454a1a241948957c4548a0a17f",
    "matrix_rank_finite_coding_candidate.py": "9a72aed5aa215816b5e26868c04453e0a3042486580e79a13234431b5f45952d",
    "prime_field_arithmetic_candidate.py": "d4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90",
    "prime_field_polynomial_candidate.py": "644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72",
    "prime_field_polynomial_degree_candidate.py": "3419cefca1f8e4b130a7c8935218815153eaf9865fe1eeed89118ced8bf339e5",
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_monic_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    """Exact source-derived types only; no parent edition or proof replay."""
    from peano_lab.library.bertrand_power_valuation_laws_candidate import make_bertrand_power_valuation_law_candidate_theorems
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_degree_candidate import make_prime_field_polynomial_degree_candidate_theorems

    directory = Path(candidate.__file__).parent
    for name, digest in PROVIDER_PINS.items():
        assert sha256((directory / name).read_bytes()).hexdigest() == digest
    result = {row.name: row for row in THEOREMS}
    for factory in (
        make_bertrand_power_valuation_law_candidate_theorems,
        make_matrix_rank_finite_coding_candidate_theorems,
        make_prime_field_arithmetic_candidate_theorems,
        make_prime_field_polynomial_candidate_theorems,
        make_prime_field_polynomial_degree_candidate_theorems,
    ):
        for row in factory(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


NAMES = (
    "prime_field_polynomial_monic_leading_value",
    "prime_field_polynomial_monic_represented_degree",
    "prime_field_polynomial_monic_transport",
    "prime_field_polynomial_monic_constant",
    "prime_field_polynomial_monic_normalization_inverse",
    "prime_field_polynomial_monic_normalization_scalar_nonzero",
    "prime_field_polynomial_monic_normalization_entry",
    "prime_field_polynomial_monic_normalization_bounded",
    "prime_field_polynomial_monic_normalization_leading",
    "prime_field_polynomial_monic_normalization_monic",
    "prime_field_polynomial_monic_normalization_represented_degree",
    "prime_field_polynomial_monic_normalization_exists",
    "prime_field_polynomial_monic_normalization_scalar_functional",
    "prime_field_polynomial_monic_normalization_functional",
    "prime_field_polynomial_monic_normalization_value_functional",
    "prime_field_polynomial_monic_normalization_transport",
    "prime_field_polynomial_monic_normalization_fixed",
    "prime_field_polynomial_monic_normalization_constant",
    "prime_field_polynomial_monic_normalization_exists_unique",
    "prime_field_polynomial_monic_normalization_degree_zero_exists",
)
METRICS = (
    (49, 29), (39, 25), (77, 35), (31, 16), (56, 24),
    (56, 34), (80, 48), (26, 19), (107, 34), (36, 23),
    (75, 44), (102, 26), (72, 28), (80, 31), (50, 39),
    (118, 52), (81, 32), (54, 32), (92, 39), (36, 22),
)


def exact_ast(source):
    return FormulaArena().freeze(_closed_formula(source)).to_json()


def conjoin(*parts):
    if len(parts) == 1:
        return f"({parts[0]})"
    return f"({parts[0]}) /\\ ({conjoin(*parts[1:])})"


def expected_lt(a, b):
    return f"exists ind_gap. ind_gap+S ({a})=({b})"


def expected_at(b, c, i, a):
    modulus = f"S ((S ({i}))*({c}))"
    return conjoin(
        f"exists ind_height. ind_height+S ({a})={modulus}",
        f"exists ind_quotient. ({b})=ind_quotient*{modulus}+({a})",
    )


def expected_prime(p):
    return f"~(({p})=1) /\\ forall ind_factor_a ind_factor_b. ({p})=ind_factor_a*ind_factor_b -> ind_factor_a=1 \\/ ind_factor_b=1"


def expected_multiply(p, a, b, r):
    residue = conjoin(
        expected_lt(r, p),
        f"exists ind_offset_a ind_offset_b. ({a})*({b})+({p})*ind_offset_a=({r})+({p})*ind_offset_b",
    )
    return conjoin(expected_lt(a, p), expected_lt(b, p), residue)


def expected_inverse(p, a, k):
    return conjoin(f"~(({a})=0)", expected_multiply(p, a, k, "1"))


def expected_coeff(p, b, c, length):
    return (
        f"forall ind_coeff_i. ({expected_lt('ind_coeff_i',length)}) -> exists ind_coeff_a. "
        + conjoin(expected_at(b, c, "ind_coeff_i", "ind_coeff_a"), expected_lt("ind_coeff_a", p))
    )


def expected_equal(b, c, B, C, length):
    return (
        f"forall ind_equal_i ind_equal_a. ({expected_lt('ind_equal_i',length)}) -> "
        f"({expected_at(b,c,'ind_equal_i','ind_equal_a')}) -> "
        f"({expected_at(B,C,'ind_equal_i','ind_equal_a')})"
    )


def expected_repeat(b, c, a, length):
    return f"forall ind_repeat_i. ({expected_lt('ind_repeat_i',length)}) -> ({expected_at(b,c,'ind_repeat_i',a)})"


def expected_scale(p, k, ab, ac, bb, bc, length):
    point = (
        f"forall ind_scale_i. ({expected_lt('ind_scale_i',length)}) -> exists ind_scale_a ind_scale_r. "
        + conjoin(
            expected_at(ab, ac, "ind_scale_i", "ind_scale_a"),
            expected_at(bb, bc, "ind_scale_i", "ind_scale_r"),
            expected_multiply(p, k, "ind_scale_a", "ind_scale_r"),
        )
    )
    return conjoin(expected_lt(k, p), point)


def expected_degree(p, b, c, length, d):
    leading = "exists ind_degree_a. " + conjoin(
        expected_at(b, c, "0", "ind_degree_a"), "~(ind_degree_a=0)",
    )
    return conjoin(f"({length})=S ({d})", expected_coeff(p, b, c, length), leading)


def expected_monic(p, b, c, length):
    return conjoin(f"~(({length})=0)", expected_coeff(p, b, c, length), expected_at(b, c, "0", "1"))


def expected_normalization(p, k, ab, ac, bb, bc, length):
    leading = "exists ind_normalization_a. " + conjoin(
        expected_at(ab, ac, "0", "ind_normalization_a"),
        expected_inverse(p, "ind_normalization_a", k),
    )
    return conjoin(f"~(({length})=0)", leading, expected_scale(p, k, ab, ac, bb, bc, length))


def format_contract(names, premises, result):
    return "forall " + names + ". " + " -> ".join(f"({part})" for part in (*premises, result))


def contracts():
    M, N, D = expected_monic, expected_normalization, expected_degree
    A, C, E, P = expected_at, expected_coeff, expected_equal, expected_prime
    normal = N("p", "k", "ab", "ac", "bb", "bc", "L")
    first = N("p", "k", "ab", "ac", "bb", "bc", "L")
    second = N("p", "j", "ab", "ac", "cb", "cc", "L")
    args = "p k ab ac bb bc L"
    comparison = "p k j ab ac bb bc cb cc L"
    unique = "forall j cb cc. (" + second + ") -> " + conjoin("j=k", E("cb", "cc", "bb", "bc", "L"))
    return {
        NAMES[0]: ("p b c L a", (M("p", "b", "c", "L"), A("b", "c", "0", "a")), "a=1"),
        NAMES[1]: ("p b c L d", (M("p", "b", "c", "L"), "L=S d"), D("p", "b", "c", "L", "d")),
        NAMES[2]: ("p b c B C L", (E("b", "c", "B", "C", "L"), M("p", "b", "c", "L")), M("p", "B", "C", "L")),
        NAMES[3]: ("p b c", (M("p", "b", "c", "1"),), expected_repeat("b", "c", "1", "1")),
        NAMES[4]: (args + " a", (normal, A("ab", "ac", "0", "a")), expected_inverse("p", "a", "k")),
        NAMES[5]: (args, (P("p"), normal), "~(k=0)"),
        NAMES[6]: (args + " i a r", (normal, expected_lt("i", "L"), A("ab", "ac", "i", "a"), A("bb", "bc", "i", "r")), expected_multiply("p", "k", "a", "r")),
        NAMES[7]: (args, (normal,), conjoin(expected_lt("k", "p"), C("p", "ab", "ac", "L"), C("p", "bb", "bc", "L"))),
        NAMES[8]: (args, (normal,), A("bb", "bc", "0", "1")),
        NAMES[9]: (args, (normal,), M("p", "bb", "bc", "L")),
        NAMES[10]: (args + " d", (D("p", "ab", "ac", "L", "d"), normal), D("p", "bb", "bc", "L", "d")),
        NAMES[11]: ("p ab ac L d", (P("p"), D("p", "ab", "ac", "L", "d")), "exists k bb bc. " + normal),
        NAMES[12]: (comparison, (first, second), "k=j"),
        NAMES[13]: (comparison, (first, second), E("bb", "bc", "cb", "cc", "L")),
        NAMES[14]: (comparison + " i a b", (first, second, expected_lt("i", "L"), A("bb", "bc", "i", "a"), A("cb", "cc", "i", "b")), "a=b"),
        NAMES[15]: ("p k ab ac bb bc AB AC BB BC L", (E("ab", "ac", "AB", "AC", "L"), E("bb", "bc", "BB", "BC", "L"), normal), N("p", "k", "AB", "AC", "BB", "BC", "L")),
        NAMES[16]: ("p b c L", (P("p"), M("p", "b", "c", "L")), N("p", "1", "b", "c", "b", "c", "L")),
        NAMES[17]: ("p k ab ac bb bc", (N("p", "k", "ab", "ac", "bb", "bc", "1"),), expected_repeat("bb", "bc", "1", "1")),
        NAMES[18]: ("p ab ac L d", (P("p"), D("p", "ab", "ac", "L", "d")), "exists k bb bc. " + conjoin(normal, M("p", "bb", "bc", "L"), D("p", "bb", "bc", "L", "d"), unique)),
        NAMES[19]: ("p ab ac", (P("p"), D("p", "ab", "ac", "1", "0")), "exists k bb bc. " + conjoin(N("p", "k", "ab", "ac", "bb", "bc", "1"), expected_repeat("bb", "bc", "1", "1"))),
    }


def test_exact_source_inventory_topology_and_only_actual_declared_dependencies():
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert len(rows()) == 20
    assert sum(len(row.dependencies) for row in rows()) == 45
    assert sum(len(row.script) for row in rows()) == 715
    assert sum(nodes for nodes, _ in METRICS) == 1317
    available = set(provider_core())
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in available
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= available
        assert all(any(re.search(r"\b" + re.escape(dep) + r"\b", command) for command in row.script)
                   for dep in row.dependencies)
        assert not any(command.startswith(("use ", "admit", "sorry", "DNE", "ring")) for command in row.script)
        available.add(row.name)
    assert candidate.__all__ == [
        "prime_field_polynomial_monic_relation",
        "prime_field_polynomial_monic_normalization_relation",
        "make_prime_field_polynomial_monic_candidate_theorems",
    ]


def test_exact_peer_novelty_and_no_alias_of_a_direct_dependency_statement():
    seen = {}
    for row in rows():
        encoded = exact_ast(row.statement)
        assert encoded not in seen
        seen[encoded] = row.name
    direct = {dep for row in rows() for dep in row.dependencies} - set(NAMES)
    assert all(exact_ast(provider_core()[name].statement) not in seen for name in direct)


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_every_statement_is_an_independently_expanded_constructive_contract(row):
    assert exact_ast(row.statement) == exact_ast(format_contract(*contracts()[row.name]))


def instantiate(template, replacements, tag):
    binders = tuple(dict.fromkeys(
        name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", template) for name in clause.split()
    ))
    renames = {name: "ind_inst_" + tag + "_" + str(index) for index, name in enumerate(binders)}
    token = r"\b[A-Za-z_][A-Za-z_0-9']*"
    renamed = re.sub(token, lambda match: renames.get(match.group(), match.group()), template)
    return re.sub(token, lambda match: "(" + replacements[match.group()] + ")"
                  if match.group() in replacements else match.group(), renamed)


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
@pytest.mark.parametrize("mode", ("compound", "zero", "repeated", "large"))
def test_every_quantified_contract_preserves_compound_zero_repeated_and_large_terms(row, mode):
    names = contracts()[row.name][0].split()
    replacements = {name: ("left+right" if i % 2 else "S (left*right)") for i, name in enumerate(names)}
    if mode == "zero":
        replacements = dict.fromkeys(names, "0")
    elif mode == "repeated":
        replacements = dict.fromkeys(names, "left")
    elif mode == "large":
        replacements = dict.fromkeys(names, "79228162514264337593543950335")
    actual = instantiate(row.statement.split(".", 1)[1], replacements, "actual")
    expected = instantiate(format_contract(*contracts()[row.name]).split(".", 1)[1], replacements, "expected")
    assert exact_ast("forall left right unused. " + actual) == exact_ast("forall left right unused. " + expected)


PUBLIC = (
    (candidate.prime_field_polynomial_monic_relation, ("p", "b", "c", "L"), expected_monic),
    (candidate.prime_field_polynomial_monic_normalization_relation, ("p", "k", "ab", "ac", "bb", "bc", "L"), expected_normalization),
)


@pytest.mark.parametrize("builder,args,expected", PUBLIC)
@pytest.mark.parametrize("mode", ("identifiers", "zero", "repeated"))
def test_two_public_graphs_have_only_the_exact_canonical_data_constraints(builder, args, expected, mode):
    values = args if mode == "identifiers" else tuple("0" if mode == "zero" else args[0] for _ in args)
    actual = builder(*values, tag="public", variables=args + ("unused",))
    binder = "forall " + " ".join(args + ("unused",)) + ". "
    assert exact_ast(binder + actual) == exact_ast(binder + expected(*values))


COMPOUND = tuple((builder, args, expected, index, term)
                 for builder, args, expected in PUBLIC for index in range(len(args))
                 for term in ("S (left+right)", "79228162514264337593543950335"))


@pytest.mark.parametrize("builder,args,expected,index,term", COMPOUND)
def test_every_public_argument_preserves_compound_and_96bit_terms(builder, args, expected, index, term):
    context = args + ("left", "right", "unused")
    values = args[:index] + (term,) + args[index + 1:]
    binder = "forall " + " ".join(context) + ". "
    assert exact_ast(binder + builder(*values, tag="compound", variables=context)) == exact_ast(binder + expected(*values))


CAPTURES = tuple(
    (builder, args, name)
    for builder, args, _ in PUBLIC
    for name in dict.fromkeys(
        name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", builder(*args, tag="capture", variables=args))
        for name in clause.split()
    )
)


@pytest.mark.parametrize("builder,args,name", CAPTURES)
def test_every_generated_binder_rejects_both_unused_and_used_context_capture(builder, args, name):
    with pytest.raises(ValueError, match="captures"):
        builder(*args, tag="capture", variables=args + (name,))
    with pytest.raises(ValueError, match="captures"):
        builder(args[0] + "+" + name, *args[1:], tag="capture", variables=args + (name,))


@pytest.mark.parametrize("builder,args,expected", PUBLIC)
@pytest.mark.parametrize("variables", ((), [], ("p", "p"), ("bad name",), ("forall",)))
def test_invalid_public_context_is_rejected(builder, args, expected, variables):
    with pytest.raises(ValueError):
        builder(*("0" for _ in args), tag="invalid", variables=variables)


@pytest.mark.parametrize("builder,args,expected", PUBLIC)
@pytest.mark.parametrize("term", ("undeclared", "p -> p", "p=0", "p; true", "", None, 7, False))
def test_invalid_public_term_is_rejected(builder, args, expected, term):
    with pytest.raises(ValueError):
        builder(term, *args[1:], tag="invalid", variables=args)


@pytest.mark.parametrize("builder,args,expected", PUBLIC)
@pytest.mark.parametrize("tag", ("", "two words", "forall", "1", "x.y"))
def test_invalid_public_tag_is_rejected(builder, args, expected, tag):
    with pytest.raises(ValueError):
        builder(*args, tag=tag, variables=args)


@pytest.mark.parametrize("row,metrics", tuple(zip(rows(), METRICS)), ids=lambda value: value.name if hasattr(value, "name") else str(value))
def test_original_ha_body_exact_nodes_and_depth(row, metrics):
    try:
        report = replay_candidate_bodies((row,), core=body_core())[0]
        assert report.name == row.name and report.dependency_count == len(row.dependencies)
        assert report.command_count == len(row.script)
        assert (report.proof_nodes, report.proof_depth) == metrics
        assert 0 < report.proof_objects <= report.proof_nodes
    finally:
        gc.collect()


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_false_conclusion_with_the_same_original_quantifiers_and_premises_is_rejected(row):
    names, premises, _ = contracts()[row.name]
    changed = replace(row, statement=format_contract(names, premises, "0=1"))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_missing_body_is_not_accepted(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=()),), core=body_core())


EDGES = tuple((row, dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize("row,dependency", EDGES, ids=lambda value: value.name if hasattr(value, "name") else value)
def test_every_removed_dependency_is_rejected_by_actual_replay(row, dependency):
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize("row,dependency", EDGES, ids=lambda value: value.name if hasattr(value, "name") else value)
def test_every_poisoned_dependency_is_rejected_by_actual_replay(row, dependency):
    table = body_core()
    table[dependency] = replace(table[dependency], statement="0=0")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,), core=table)


def hostile_contracts():
    data = contracts()
    result = []

    def change(index, label, *, premises=None, conclusion=None):
        names, previous, target = data[NAMES[index]]
        result.append((NAMES[index], label, format_contract(
            names, previous if premises is None else premises,
            target if conclusion is None else conclusion,
        )))

    change(11, "existence_needs_prime", premises=data[NAMES[11]][1][1:])
    change(11, "existence_needs_nonzero_leading_representation", premises=(expected_prime("p"), expected_coeff("p", "ab", "ac", "L")))
    change(11, "canonical_length_alone_does_not_exclude_zero_head", premises=(expected_prime("p"), conjoin("L=S d", expected_coeff("p", "ab", "ac", "L"))))
    change(8, "scaling_without_the_actual_inverse_is_not_monic", premises=(conjoin("~(L=0)", expected_scale("p", "k", "ab", "ac", "bb", "bc", "L")),))
    inverse = "exists a. " + conjoin(expected_at("ab", "ac", "0", "a"), expected_inverse("p", "a", "k"))
    change(8, "empty_scaling_does_not_constrain_the_output_head", premises=(conjoin(inverse, expected_scale("p", "k", "ab", "ac", "bb", "bc", "L")),))
    change(13, "decoded_uniqueness_is_not_beta_code_uniqueness", conclusion=conjoin("bb=cb", "bc=cc"))
    change(14, "value_uniqueness_is_only_inside_the_prefix", premises=tuple(p for i, p in enumerate(data[NAMES[14]][1]) if i != 2))
    change(15, "input_reencoding_needs_actual_prefix_equality", premises=data[NAMES[15]][1][1:])
    change(15, "output_reencoding_needs_actual_prefix_equality", premises=(data[NAMES[15]][1][0], data[NAMES[15]][1][2]))
    change(16, "scalar_one_requires_monic_input", premises=(expected_prime("p"), conjoin("~(L=0)", expected_coeff("p", "b", "c", "L"))))
    change(17, "constant_case_does_not_constrain_the_next_entry", conclusion=expected_repeat("bb", "bc", "1", "2"))
    change(7, "canonical_bounds_do_not_extend_past_length", conclusion=conjoin(expected_lt("k", "p"), expected_coeff("p", "ab", "ac", "S L"), expected_coeff("p", "bb", "bc", "S L")))
    change(6, "entry_law_needs_index_bound", premises=tuple(p for i, p in enumerate(data[NAMES[6]][1]) if i != 1))
    change(10, "normalization_preserves_not_increases_degree", conclusion=expected_degree("p", "bb", "bc", "L", "S d"))
    change(1, "represented_degree_needs_the_actual_length_annotation", premises=data[NAMES[1]][1][:1])
    change(2, "monicity_transport_needs_the_actual_reencoding", premises=data[NAMES[2]][1][1:])
    return tuple(result)


@pytest.mark.parametrize("name,label,statement", hostile_contracts(), ids=lambda value: value if len(value) < 120 else None)
def test_substantively_stronger_or_missing_guard_contracts_are_rejected(name, label, statement):
    row = next(row for row in rows() if row.name == name)
    assert exact_ast(statement) != exact_ast(row.statement)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=statement),), core=body_core())


def encode_beta(values, multiplier=1):
    """Independent finite CRT examples; numerical diagnostics, not proofs."""
    values = tuple(values)
    assert all(type(value) is int and value >= 0 for value in values)
    assert type(multiplier) is int and multiplier > 0
    scale = (max(values, default=0) + 1) * math.factorial(max(1, len(values))) * multiplier
    code, product = 0, 1
    for i, value in enumerate(values):
        modulus = 1 + (i + 1) * scale
        assert value < modulus and math.gcd(product, modulus) == 1
        correction = ((value - code) * pow(product, -1, modulus)) % modulus
        code += product * correction
        product *= modulus
    return code, scale


def decode_beta(code, index):
    return code[0] % (1 + (index + 1) * code[1])


def prefix(code, length):
    return tuple(decode_beta(code, i) for i in range(length))


def model_coeff(p, code, length):
    return all(decode_beta(code, i) < p for i in range(length))


def model_monic(p, code, length):
    return length != 0 and model_coeff(p, code, length) and decode_beta(code, 0) == 1


def model_degree(p, code, length, degree):
    return length == degree + 1 and model_coeff(p, code, length) and decode_beta(code, 0) != 0


def model_scale(p, k, source, output, length):
    return 0 <= k < p and all(
        decode_beta(source, i) < p and decode_beta(output, i) < p
        and k * decode_beta(source, i) % p == decode_beta(output, i)
        for i in range(length)
    )


def model_normalization(p, k, source, output, length):
    a = decode_beta(source, 0)
    return (
        length != 0 and 0 < a < p and 0 <= k < p and 1 < p and a * k % p == 1
        and model_scale(p, k, source, output, length)
    )


PRIME_LEADING = tuple((p, a) for p in (2, 3, 5, 7, 11) for a in range(1, p))


@pytest.mark.parametrize("p,a", PRIME_LEADING)
def test_actual_beta_normalizations_construct_monic_prefixes_and_preserve_every_tested_degree(p, a):
    k = pow(a, -1, p)
    for degree in range(4):
        values = (a,) + tuple((p - 1 - i) % p for i in range(degree))
        source = encode_beta(values)
        output_values = tuple(k * value % p for value in values)
        output = encode_beta(output_values, 3)
        assert prefix(source, degree + 1) == values
        assert prefix(output, degree + 1) == output_values
        assert model_degree(p, source, degree + 1, degree)
        assert model_normalization(p, k, source, output, degree + 1)
        assert model_monic(p, output, degree + 1)
        assert model_degree(p, output, degree + 1, degree)
        assert 0 < k < p
        for i in range(degree + 1):
            for code, value in ((source, values[i]), (output, output_values[i])):
                modulus = 1 + (i + 1) * code[1]
                gap, quotient = modulus - value - 1, code[0] // modulus
                assert gap >= 0 and gap + value + 1 == modulus
                assert code[0] == quotient * modulus + value
            quotient, remainder = divmod(k * values[i], p)
            assert remainder == output_values[i] < p
            assert k * values[i] + p * 0 == output_values[i] + p * quotient


@pytest.mark.parametrize("p,a", PRIME_LEADING)
def test_degree_zero_normalization_is_actual_constant_one_with_unique_inverse(p, a):
    source = encode_beta((a,))
    output = encode_beta((1,), 4)
    choices = [k for k in range(p) if model_normalization(p, k, source, output, 1)]
    assert choices == [pow(a, -1, p)]
    assert model_degree(p, source, 1, 0) and model_degree(p, output, 1, 0)
    assert prefix(output, 1) == (1,)


def test_characteristic_two_uses_natural_one_not_signed_code_two():
    source = encode_beta((1, 0, 1, 1))
    assert model_normalization(2, 1, source, source, 4)
    assert model_monic(2, source, 4)
    assert not model_normalization(2, 2, source, source, 4)
    assert not model_monic(2, encode_beta((2, 0, 1)), 3)


@pytest.mark.parametrize("p", (2, 3, 5, 7))
def test_zero_leading_residue_is_not_normalizable_even_when_coefficients_are_canonical(p):
    source = encode_beta((0, 1))
    assert model_coeff(p, source, 2) and not model_degree(p, source, 2, 1)
    assert not any(model_normalization(p, k, source, encode_beta((1, 0)), 2) for k in range(p))
    assert not model_normalization(p, 0, source, encode_beta((0, 0)), 2)


def test_composite_nonzero_nonunit_is_the_counterexample_to_unrestricted_existence():
    source = encode_beta((2, 1))
    assert model_degree(4, source, 2, 1)
    assert all(2 * k % 4 != 1 for k in range(4))
    assert not any(model_normalization(4, k, source, encode_beta((1, r)), 2)
                   for k in range(4) for r in range(4))


def test_recorded_unit_consequences_do_not_need_to_assume_primality():
    source, output = encode_beta((3, 2)), encode_beta((1, 2))
    assert model_normalization(4, 3, source, output, 2)
    assert model_monic(4, output, 2) and model_degree(4, output, 2, 1)


def test_normalization_is_highest_degree_first_and_keeps_trailing_zero_coefficients():
    source, output = encode_beta((2, 3, 4)), encode_beta((1, 4, 2))
    assert model_normalization(5, 3, source, output, 3)
    assert decode_beta(output, 0) == 1 and decode_beta(output, 2) != 1
    source, output = encode_beta((2, 0)), encode_beta((1, 0))
    assert model_normalization(5, 3, source, output, 2)
    assert model_degree(5, output, 2, 1) and not model_degree(5, output, 2, 0)


def test_an_arbitrary_monic_output_is_not_a_normalization_or_a_construction_oracle():
    source = encode_beta((2, 3))
    correct, unrelated = encode_beta((1, 4)), encode_beta((1, 0))
    assert model_monic(5, correct, 2) and model_monic(5, unrelated, 2)
    assert model_normalization(5, 3, source, correct, 2)
    assert not model_normalization(5, 3, source, unrelated, 2)
    assert model_scale(5, 1, source, source, 2) and not model_monic(5, source, 2)


def test_empty_prefix_and_noncanonical_inputs_are_not_silently_normalized():
    unit, other = encode_beta((1,)), encode_beta((0,))
    assert model_scale(5, 1, unit, other, 0)
    assert not model_normalization(5, 1, unit, other, 0)
    assert not model_monic(5, unit, 0)
    noncanonical = encode_beta((7, 1))
    assert not model_normalization(5, 3, noncanonical, encode_beta((1, 3)), 2)
    assert not model_normalization(0, 0, unit, unit, 1)
    assert not model_normalization(1, 0, unit, unit, 1)


def test_actual_reencoding_preserves_values_but_not_codes_or_outside_entries():
    source = encode_beta((2, 1, 0, 4))
    recoded_source = encode_beta((2, 1, 0, 3), 2)
    output = encode_beta((1, 3, 0, 1))
    recoded_output = encode_beta((1, 3, 0, 4), 3)
    assert source != recoded_source and output != recoded_output
    assert prefix(source, 3) == prefix(recoded_source, 3)
    assert prefix(output, 3) == prefix(recoded_output, 3)
    assert model_normalization(5, 3, source, output, 3)
    assert model_normalization(5, 3, recoded_source, recoded_output, 3)
    assert decode_beta(output, 3) != decode_beta(recoded_output, 3)
    assert decode_beta(output, 3) != 3 * decode_beta(source, 3) % 5


def test_monic_fixed_point_can_keep_its_actual_original_code_pair():
    source = encode_beta((1, 2, 0, 4))
    assert model_monic(5, source, 4)
    assert model_normalization(5, 1, source, source, 4)
    recoded = encode_beta((1, 2, 0, 4), 3)
    assert source != recoded and model_normalization(5, 1, source, recoded, 4)


def test_unchecked_endpoint_can_exceed_the_field_bound():
    source, output = encode_beta((2, 100)), encode_beta((1, 200))
    assert model_normalization(5, 3, source, output, 1)
    assert model_coeff(5, source, 1) and model_coeff(5, output, 1)
    assert not model_coeff(5, source, 2) and not model_coeff(5, output, 2)
