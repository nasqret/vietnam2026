"""Actual integer-span closure: original-kernel proofs and bounded examples."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from itertools import product
import json
from math import factorial, gcd
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library import integer_column_span_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.finite_sum_theorems import _at
from peano_lab.library.matrix_coded_product_candidate import _pointwise_add_terms, _signed_matrix_product_terms
from peano_lab.library.theorems import TheoremSpec, _closed_formula


REPO = Path(__file__).resolve().parents[3]
PARENT_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
EXPECTED_NAMES = (
    "integer_span_dot_product_pointwise_add",
    "integer_span_natural_cell_add_right",
    "integer_span_natural_product_entry",
    "integer_span_natural_product_add_right",
    "integer_span_pointwise_add_interchange",
    "integer_span_signed_product_negate",
    "integer_span_signed_product_equal_coefficients",
    "integer_span_signed_product_add_right",
    "integer_span_pair_equal_transitive",
    "integer_span_pair_add_congruence",
    "integer_vector_equal_reflexive",
    "integer_vector_equal_transitive",
    "integer_vector_equal_negated",
    "integer_vector_equal_components_zero",
    "integer_vector_equal_zero_from_same_components",
    "integer_vector_add_from_component_sums",
    "integer_vector_add_exists",
    "integer_vector_add_transport_inputs",
    "integer_vector_add_functional",
    "integer_matrix_vector_product_exists",
    "integer_matrix_vector_product_transport",
    "integer_matrix_vector_product_zero",
    "integer_matrix_vector_product_negated",
    "integer_matrix_vector_add_coefficients",
    "integer_matrix_vector_add_constructive",
    "integer_column_span_transport",
    "integer_column_span_zero",
    "integer_column_span_contains_zero",
    "integer_column_span_negated",
    "integer_column_span_negate_closed",
    "integer_column_span_add_closed",
    "integer_column_span_add_exists",
    "integer_column_span_negate_exists",
)
EXPECTED_NAMES_SHA256 = "49f25c6350493038f10c863b3cf549f0bfa29b2a248f9806bc78daa2985ea715"
EXPECTED_BODY_NODES = (
    162, 276, 132, 240, 141, 90, 62, 302, 46, 26, 37, 78, 50, 35, 47,
    60, 51, 135, 109, 47, 100, 41, 136, 200, 146, 106, 59, 63, 83, 121,
    85, 66, 82,
)
EXPECTED_STATEMENTS = {
    "integer_span_natural_product_add_right": "ddb97f384fd5979784c83de5cac3e7b16aa13caeb295a83be9d13020b2fa7049",
    "integer_span_signed_product_negate": "8a8a573c3154c1f71fd73cd5577b4baa2e8ee096f4c19d21afb3b01316659392",
    "integer_span_signed_product_add_right": "b791214474e0471436f7e3c93c45ecd338d4d1034646463b1e39aa87f47143d9",
    "integer_matrix_vector_add_constructive": "eccbefbe383084f67b9846ac5719cd08f7e008ed1654d36dce91cac03da06aff",
    "integer_column_span_transport": "5078153e18a76dc36591d5fc048f0d9c968758cb4c1040ef353255ce551147dd",
    "integer_column_span_zero": "2a8054ab3ed1dc514d476f56adfdb91901fe5788b6c25ddd460351b66dc32b20",
    "integer_column_span_contains_zero": "1df52e34af59b05182acebe099349fc54eb8b6ca59ac55dccdc096bc8aaf0d01",
    "integer_column_span_negate_closed": "6e851a3b673718d8af101b7f38fe625a3de92e63d11df94cc2f27758532ef002",
    "integer_column_span_add_closed": "ae7784648a8b9f249d0b14e83e6a0fd818a48ab39603ba9336736b6c907248d4",
    "integer_column_span_add_exists": "4c3ef723161578a73747c914a683d2b50ad3a80d087ee222b56a14ef4a1e296a",
    "integer_column_span_negate_exists": "c6723d098ae92d7069c1ae12d5207fb1c133bd40ec63ad6bd596df954791736a",
}
A = ("ab", "ac", "db", "dc")
B = ("eb", "ec", "fb", "fc")
C = ("gb", "gc", "hb", "hc")
D = ("ib", "ic", "jb", "jc")
X = ("pb", "pc", "nb", "nc")
Y = ("qb", "qc", "mb", "mc")
Z = ("rb", "rc", "sb", "sc")
RELATIONS = (
    (candidate.integer_vector_equal, (*A, *B, "l")),
    (candidate.integer_vector_zero, (*A, "l")),
    (candidate.integer_vector_add, (*A, *B, *X, "l")),
    (candidate.integer_vector_negate, (*A, *B, "l")),
    (candidate.integer_matrix_vector_product, (*A, *B, "w", "r", *X)),
    (candidate.integer_column_span, (*A, "w", "r", *X)),
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_integer_column_span_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    raw = (REPO / "artifacts/peano-library/alpha/catalog-v26.json").read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    rows = json.loads(raw)["theorems"]
    assert len(rows) == 2_138
    return {
        row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row.get("summary", ""))
        for row in rows
    }


@lru_cache(maxsize=1)
def _all() -> dict[str, TheoremSpec]:
    return _core() | {row.name: row for row in _rows()}


@lru_cache(maxsize=1)
def _receipts():
    # One theorem per independent original-kernel call. The pinned parent
    # replaces expensive edition reconstruction, never logical body checking.
    return tuple(replay_candidate_bodies((row,), core=_all())[0] for row in _rows())


def _conjunction(*parts: str) -> str:
    return parts[0] if len(parts) == 1 else f"({parts[0]}) /\\ ({_conjunction(*parts[1:])})"


def _pointwise(codes: tuple[str, ...], values: tuple[str, ...], equation: str) -> str:
    return "forall i " + " ".join(values) + ". (exists k. k + S i = l) -> " + "".join(
        f"({_at(codes[2*j],codes[2*j+1],'i',value,tag=f'audit{j}')}) -> " for j, value in enumerate(values)
    ) + equation


def test_inventory_is_closed_additive_dependency_ordered_and_deterministic() -> None:
    assert _rows() == candidate.make_integer_column_span_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert len(_rows()) == 33
    assert sum(len(row.dependencies) for row in _rows()) == 66
    assert sum(len(row.script) for row in _rows()) == 2_220
    assert max(len(row.statement) for row in _rows()) == 202_908
    available = set(_core())
    for row in _rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        formula, free = parse_formula_with_names(row.statement)
        assert not free and formula == _closed_formula(row.statement)
        assert all(not any(token in command for token in ("DNE", "sorry", "admit", "oracle", "axiom")) and not command.startswith("use ") for command in row.script)
        available.add(row.name)


def test_every_body_passes_original_heyting_kernel_in_bounded_one_row_batches() -> None:
    assert tuple(receipt.name for receipt in _receipts()) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in _receipts()) == EXPECTED_BODY_NODES
    assert sum(receipt.proof_nodes for receipt in _receipts()) == 3_414
    assert max(receipt.proof_nodes for receipt in _receipts()) == 302
    assert max(receipt.proof_depth for receipt in _receipts()) == 90


@pytest.mark.parametrize(("name", "digest"), EXPECTED_STATEMENTS.items())
def test_exact_endpoint_hashes(name: str, digest: str) -> None:
    assert sha256(_all()[name].statement.encode()).hexdigest() == digest


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_conclusion_mutation_is_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=f"({row.statement}) /\\ false"),), core=_all())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_body_is_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_all())


@pytest.mark.parametrize("name", tuple(name for name in EXPECTED_NAMES if name not in {
    "integer_span_signed_product_negate", "integer_vector_add_from_component_sums",
}))
def test_missing_dependency_is_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, dependencies=row.dependencies[:-1]),), core=_all())


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_public_definitions_are_hygienic_alpha_invariant_native_formulas(builder, arguments) -> None:
    first, free = parse_formula_with_names(builder(*arguments, tag="first"))
    second, other = parse_formula_with_names(builder(*arguments, tag="second"))
    assert first == second
    assert set(free) == set(other) == set(arguments)
    assert all(token not in builder(*arguments, tag="audit") for token in ("Span", "MatrixProduct", "VectorEqual", "Basis", "Beta"))


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "x + y", "0", "a;b"))
def test_public_definitions_reject_unsafe_arguments(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError):
        builder(fragment, *arguments[1:], tag="safe")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "x + y", "0", "a;b"))
def test_public_definitions_reject_unsafe_tags(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError):
        builder(*arguments, tag=fragment)


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("ics_index_capture", "ff_pp_capture", "fs_h_capture", "mcp_gap_capture", "dot_value_capture", "fpmp_target_capture"))
def test_public_definitions_reject_generated_name_capture(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError, match="capture"):
        builder(fragment, *arguments[1:], tag="capture")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_public_definitions_reject_duplicate_arguments(builder, arguments) -> None:
    with pytest.raises(ValueError, match="distinct"):
        builder(arguments[1], *arguments[1:], tag="safe")


def test_integer_vector_equality_is_balanced_not_component_equality() -> None:
    expected = _pointwise((*A, *B), ("a", "b", "c", "d"), "a + d = c + b")
    actual = candidate.integer_vector_equal(*A, *B, "l", tag="audit_equal")
    assert _closed_formula(f"forall {' '.join((*A,*B,'l'))}. {actual}") == _closed_formula(f"forall {' '.join((*A,*B,'l'))}. {expected}")


def test_zero_accepts_noncanonical_equal_positive_and_negative_entries() -> None:
    expected = _pointwise(A, ("a", "b"), "a = b")
    actual = candidate.integer_vector_zero(*A, "l", tag="audit_zero")
    assert _closed_formula(f"forall {' '.join((*A,'l'))}. {actual}") == _closed_formula(f"forall {' '.join((*A,'l'))}. {expected}")


def test_addition_is_actual_coordinatewise_integer_addition() -> None:
    expected = _pointwise((*A, *B, *X), ("a", "b", "c", "d", "e", "f"), "e + (b + d) = (a + c) + f")
    actual = candidate.integer_vector_add(*A, *B, *X, "l", tag="audit_add")
    assert _closed_formula(f"forall {' '.join((*A,*B,*X,'l'))}. {actual}") == _closed_formula(f"forall {' '.join((*A,*B,*X,'l'))}. {expected}")


def test_negation_is_equality_to_the_swapped_integer_pair() -> None:
    expected = candidate.integer_vector_equal(*A[2:], *A[:2], *B, "l", tag="audit_swapped_equal")
    actual = candidate.integer_vector_negate(*A, *B, "l", tag="audit_negative")
    assert _closed_formula(f"forall {' '.join((*A,*B,'l'))}. {actual}") == _closed_formula(f"forall {' '.join((*A,*B,'l'))}. {expected}")


def test_matrix_vector_product_contains_the_exact_frozen_width_one_product() -> None:
    raw_output = ("P", "C", "N", "D")
    raw = _signed_matrix_product_terms(*A, *B, "w", "1", "r", *raw_output, tag="audit_frozen_product")
    equality = candidate.integer_vector_equal(*raw_output, *X, "r", tag="audit_image_equal")
    expected = "exists P C N D. (" + _conjunction(raw, equality) + ")"
    actual = candidate.integer_matrix_vector_product(*A, *B, "w", "r", *X, tag="audit_product")
    header = f"forall {' '.join((*A,*B,'w','r',*X))}. "
    assert _closed_formula(header + actual) == _closed_formula(header + expected)


def test_span_quantifies_actual_coefficient_codes_and_does_not_assume_a_basis() -> None:
    expected = "exists eb ec fb fc. (" + candidate.integer_matrix_vector_product(*A, *B, "w", "r", *X, tag="audit_coefficient_image") + ")"
    actual = candidate.integer_column_span(*A, "w", "r", *X, tag="audit_span")
    header = f"forall {' '.join((*A,'w','r',*X))}. "
    assert _closed_formula(header + actual) == _closed_formula(header + expected)
    formula, _ = parse_formula_with_names(actual)
    for _ in range(8):  # Four coefficient codes, then four exact raw output codes.
        assert isinstance(formula, Exists)
        formula = formula.body
    assert isinstance(formula, And)


def test_constructive_addition_returns_the_actual_sums_of_coefficient_streams() -> None:
    first = candidate.integer_matrix_vector_product(*A, *B, "w", "r", *X, tag="audit_first_image")
    second = candidate.integer_matrix_vector_product(*A, *C, "w", "r", *Y, tag="audit_second_image")
    total = candidate.integer_vector_add(*X, *Y, *Z, "r", tag="audit_output_sum")
    output = _conjunction(
        _pointwise_add_terms(*B[:2], *C[:2], *D[:2], "w", tag="audit_coefficient_p"),
        _pointwise_add_terms(*B[2:], *C[2:], *D[2:], "w", tag="audit_coefficient_n"),
        candidate.integer_matrix_vector_product(*A, *D, "w", "r", *Z, tag="audit_total_image"),
    )
    expected = f"forall {' '.join((*A,*B,*C,'w','r',*X,*Y,*Z))}. ({first}) -> ({second}) -> ({total}) -> exists {' '.join(D)}. ({output})"
    assert _closed_formula(_all()["integer_matrix_vector_add_constructive"].statement) == _closed_formula(expected)


def test_addition_closure_has_only_membership_and_actual_sum_premises() -> None:
    expected = (
        f"forall {' '.join((*A,'w','r',*X,*Y,*Z))}. "
        f"({candidate.integer_column_span(*A,'w','r',*X,tag='audit_first')}) -> "
        f"({candidate.integer_column_span(*A,'w','r',*Y,tag='audit_second')}) -> "
        f"({candidate.integer_vector_add(*X,*Y,*Z,'r',tag='audit_sum')}) -> "
        f"({candidate.integer_column_span(*A,'w','r',*Z,tag='audit_result')})"
    )
    assert _closed_formula(_all()["integer_column_span_add_closed"].statement) == _closed_formula(expected)


def test_negation_closure_accepts_any_equal_negative_encoding() -> None:
    expected = (
        f"forall {' '.join((*A,'w','r',*X,*Y))}. "
        f"({candidate.integer_column_span(*A,'w','r',*X,tag='audit_member')}) -> "
        f"({candidate.integer_vector_negate(*X,*Y,'r',tag='audit_negative')}) -> "
        f"({candidate.integer_column_span(*A,'w','r',*Y,tag='audit_result')})"
    )
    assert _closed_formula(_all()["integer_column_span_negate_closed"].statement) == _closed_formula(expected)


def test_zero_membership_includes_all_noncanonical_zero_vectors() -> None:
    expected = (
        f"forall {' '.join((*A,'w','r',*X))}. "
        f"({candidate.integer_vector_zero(*X,'r',tag='audit_zero')}) -> "
        f"({candidate.integer_column_span(*A,'w','r',*X,tag='audit_result')})"
    )
    assert _closed_formula(_all()["integer_column_span_zero"].statement) == _closed_formula(expected)
    assert _all()["integer_column_span_zero"].script.count("exists 0") == 4
    literal = _closed_formula(_all()["integer_column_span_contains_zero"].statement)
    for _ in range(6):
        assert isinstance(literal, Forall)
        literal = literal.body
    assert isinstance(literal, Exists), "The literal zero theorem must not have an independence or positive-dimension premise."


def test_proof_dag_reaches_real_finite_sums_and_real_coded_matrix_products() -> None:
    reached: set[str] = set()

    def visit(name: str) -> None:
        if name in reached:
            return
        reached.add(name)
        for dependency in _all()[name].dependencies:
            visit(dependency)

    for name in ("integer_column_span_contains_zero", "integer_column_span_add_exists", "integer_column_span_negate_exists", "integer_column_span_transport"):
        visit(name)
    assert {
        "beta_signed_matrix_product_exists", "beta_pointwise_add_prefix_exists",
        "beta_sum_pointwise_add", "integer_span_dot_product_pointwise_add",
        "integer_span_natural_product_entry", "integer_span_signed_product_add_right",
        "integer_matrix_vector_add_constructive", "integer_vector_equal_transitive",
    } <= reached
    assert not any("determinant" in name or "rank" in name or "smith" in name or "hermite" in name for name in reached)


def _split(values: tuple[int, ...], offset: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return (
        tuple(max(value, 0) + offset + i for i, value in enumerate(values)),
        tuple(max(-value, 0) + offset + i for i, value in enumerate(values)),
    )


def _equal_values(left, right) -> bool:
    p, n = left
    q, m = right
    return len(p) == len(n) == len(q) == len(m) and all(a + d == c + b for a, b, c, d in zip(p, n, q, m))


def _sum_values(first, second, result) -> bool:
    a, b = first
    c, d = second
    e, f = result
    return len(a) == len(b) == len(c) == len(d) == len(e) == len(f) and all(
        z + (n + m) == (p + q) + s for p, n, q, m, z, s in zip(a, b, c, d, e, f)
    )


def _raw_product_values(matrix_p, matrix_n, coefficient):
    p, n = coefficient
    assert len(matrix_p) == len(matrix_n) and len(p) == len(n)
    assert all(len(row) == len(p) for row in (*matrix_p, *matrix_n))
    return (
        tuple(sum(a * c + b * d for a, b, c, d in zip(row_p, row_n, p, n)) for row_p, row_n in zip(matrix_p, matrix_n)),
        tuple(sum(a * d + b * c for a, b, c, d in zip(row_p, row_n, p, n)) for row_p, row_n in zip(matrix_p, matrix_n)),
    )


def _code(values: tuple[int, ...]) -> tuple[int, int]:
    scale = (max(values, default=0) + 1) * factorial(len(values))
    code, modulus = 0, 1
    for i, value in enumerate(values):
        next_modulus = 1 + (i + 1) * scale
        assert gcd(modulus, next_modulus) == 1 and value < next_modulus
        code += modulus * (((value - code) * pow(modulus, -1, next_modulus)) % next_modulus)
        modulus *= next_modulus
    return code, scale


@pytest.mark.parametrize(("matrix", "width"), (
    ((), 0), ((), 3), (((), (), ()), 0),
    (((0, 0), (0, 0)), 2), (((2, 4), (1, 2)), 2),
    (((2, -3, 0), (0, 5, -1)), 3), (((-5,),), 1),
))
def test_zero_add_neg_witnesses_for_rectangular_dependent_and_zero_dimension_examples(matrix, width: int) -> None:
    assert all(len(row) == width for row in matrix)
    components = [_split(tuple(row), 2 + i) for i, row in enumerate(matrix)]
    matrix_p = tuple(pair[0] for pair in components)
    matrix_n = tuple(pair[1] for pair in components)
    for values in (tuple(a for row in matrix_p for a in row), tuple(a for row in matrix_n for a in row)):
        code, scale = _code(values)
        for row in range(len(matrix)):
            for column in range(width):
                index = row * width + column
                assert code % (1 + (index + 1) * scale) == values[index]
    for first_values in product((-2, 0, 3), repeat=width):
        second_values = tuple(1 - value for value in first_values)
        first = _split(first_values, 1)
        second = _split(second_values, 4)
        coefficients_sum = (tuple(a + b for a, b in zip(first[0], second[0])), tuple(a + b for a, b in zip(first[1], second[1])))
        raw_first = _raw_product_values(matrix_p, matrix_n, first)
        raw_second = _raw_product_values(matrix_p, matrix_n, second)
        raw_sum = _raw_product_values(matrix_p, matrix_n, coefficients_sum)
        assert raw_sum == (tuple(a + b for a, b in zip(raw_first[0], raw_second[0])), tuple(a + b for a, b in zip(raw_first[1], raw_second[1])))
        actual_first = tuple(sum(a * b for a, b in zip(row, first_values)) for row in matrix)
        actual_second = tuple(sum(a * b for a, b in zip(row, second_values)) for row in matrix)
        actual_sum = tuple(a + b for a, b in zip(actual_first, actual_second))
        first_output, second_output, sum_output = _split(actual_first, 7), _split(actual_second, 11), _split(actual_sum, 19)
        assert _equal_values(raw_first, first_output) and _equal_values(raw_second, second_output)
        assert _sum_values(first_output, second_output, sum_output) and _equal_values(raw_sum, sum_output)
        negated = _raw_product_values(matrix_p, matrix_n, (first[1], first[0]))
        assert negated == (raw_first[1], raw_first[0])
        assert _equal_values(negated, _split(tuple(-value for value in actual_first), 23))
        zeros = (tuple(0 for _ in range(width)), tuple(0 for _ in range(width)))
        raw_zero = _raw_product_values(matrix_p, matrix_n, zeros)
        assert _equal_values(raw_zero, _split(tuple(0 for _ in matrix), 29))
        for values in (*coefficients_sum, *sum_output):
            code, scale = _code(values)
            assert tuple(code % (1 + (i + 1) * scale) for i in range(len(values))) == values


def test_integer_equality_regressions_accept_distinct_components_but_reject_false_values() -> None:
    assert _equal_values(((5,), (2,)), ((10,), (7,)))
    assert ((5,), (2,)) != ((10,), (7,))
    assert not _equal_values(((5,), (2,)), ((10,), (6,)))
    assert _sum_values(((5,), (2,)), ((1,), (4,)), ((20,), (20,)))
    assert not _sum_values(((5,), (2,)), ((1,), (4,)), ((21,), (20,)))


def test_corrupted_coefficient_sum_fails_to_witness_the_actual_output() -> None:
    matrix_p, matrix_n = ((4, 1),), ((2, 2),)  # Actual row [2,-1].
    first, second = _split((1, 2), 3), _split((-2, 1), 5)
    correct = (tuple(a+b for a,b in zip(first[0],second[0])), tuple(a+b for a,b in zip(first[1],second[1])))
    output = _raw_product_values(matrix_p, matrix_n, correct)
    corrupted = ((correct[0][0] + 1, correct[0][1]), correct[1])
    assert not _equal_values(_raw_product_values(matrix_p, matrix_n, corrupted), output)
