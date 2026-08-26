"""Original-kernel, hygiene, resource, and adversarial audit of G102's first layer."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library import binary_modular_exponentiation_candidate as candidate
from peano_lab.library import editions_v20
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "binary_modulus_nontrivial_nonzero",
    "binary_canonical_residue_exists",
    "binary_canonical_residue_functional",
    "binary_canonical_residue_exists_unique",
    "binary_exponent_split_exists",
    "binary_exponent_doubled_power",
    "binary_exponent_odd_power",
    "binary_modular_square_congruence",
    "binary_modular_multiply_congruence",
    "binary_modular_square_residue_exists",
    "binary_modular_multiply_residue_exists",
    "binary_modular_step_exists",
    "binary_modular_step_functional",
    "binary_modular_exponentiation_result_exists",
    "binary_modular_exponentiation_result_functional",
    "binary_modular_exponentiation_result_exists_unique",
)
EXPECTED_ORDERED_NAMES_SHA256 = (
    "b8165f5d62afded3312f199aa52c0a105e46943a47a2affe9835ee35e7507db8"
)
EXPECTED_STATEMENT_SHA256 = {
    "binary_modulus_nontrivial_nonzero": (
        "df3f3be5ae7d754326f0e766d53d1ffa784fcf4f01007049ff0c24ce56dceba0"
    ),
    "binary_canonical_residue_exists": (
        "706d0ba66fb532a65b37b61b26361fd923778d52c970750415c1f3e46a6fd265"
    ),
    "binary_canonical_residue_functional": (
        "6ceca7d1c5171f65ecad03675e8ac1c4a69bfaf38c82b9a3423795134e3c797d"
    ),
    "binary_canonical_residue_exists_unique": (
        "8ca2d35dd61d917caa15ccadc4c5587422812bed2b2e7b14d83235d12222e378"
    ),
    "binary_exponent_split_exists": (
        "b2326893e40c7faf7753ab6269ac5baaf0237b00954651b6d45634e9b4f5464b"
    ),
    "binary_exponent_doubled_power": (
        "0807f7552efeb57c6c5a1c2ed74a2635af2b06ab18d27e56bfeb8a2267a1539a"
    ),
    "binary_exponent_odd_power": (
        "2cd3019ccf6bc8147ba67b664de89adbc3ba0b38ad45d3f555182777f4b2c503"
    ),
    "binary_modular_square_congruence": (
        "dd7000cbba9db94eb6fdd43fdae304c5c5dadaa5677cb897b0a9e308fae3457e"
    ),
    "binary_modular_multiply_congruence": (
        "754a02c664355818e9b6a8c2ac217263043c9159955b23b72a9627c0906ef025"
    ),
    "binary_modular_square_residue_exists": (
        "b340cd21e4e115d0513971251ef10dd832a30730b872af306bcabf083d88c2e9"
    ),
    "binary_modular_multiply_residue_exists": (
        "ac16738fb62f093da4fb0dd71f9d94739d7d1631df4f70c90344116e30b17be0"
    ),
    "binary_modular_step_exists": (
        "5e460347370cb0ab996c0c8eff7b587c9d1eb29bd836503c791ce95c8b6160dc"
    ),
    "binary_modular_step_functional": (
        "67d1d84c903060b083196eab0de743722fb068cb4c176a4cd91f13bff253bed9"
    ),
    "binary_modular_exponentiation_result_exists": (
        "b04df34ba7fdadb96d3c20a5d07094d73012589ea9a5521dc6c1b181040da1d5"
    ),
    "binary_modular_exponentiation_result_functional": (
        "453385706238c475f61dd57108282cdfcb7b3b8b1e7aa4b98e3fdb5878a79e12"
    ),
    "binary_modular_exponentiation_result_exists_unique": (
        "7b9895f8ad3956c33e9fb06ea8040113f17f272be5e97d942ca71aed2a88f136"
    ),
}
EXPECTED_PROOF_NODES = (
    17, 39, 36, 25, 37, 60, 45, 30, 33, 15, 16, 31, 127, 21, 37, 28
)
EXPECTED_PROOF_DEPTHS = (
    11, 17, 17, 17, 16, 34, 20, 18, 21, 10, 11, 13, 30, 12, 21, 19
)
EXPECTED_COMMAND_COUNTS = (
    13, 32, 29, 21, 24, 20, 40, 12, 15, 7, 8, 29, 41, 18, 27, 24
)
EXPECTED_EXTERNAL_PREREQUISITES = {
    "add_eq_zero_right",
    "division_remainder_exists",
    "mod_eq_bounded_unique",
    "mod_eq_mul",
    "mod_eq_symm",
    "mod_eq_trans",
    "mul_comm",
    "parity_cases",
    "pow_add",
    "pow_exists",
    "pow_functional",
    "pow_successor_pair_mul",
    "remainder_decomposition_to_mod_eq",
    "succ_ne_zero",
    "two_mul_eq_add_self",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_binary_modular_exponentiation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v20.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def _receipts():
    return replay_candidate_bodies(_rows(), core=_core())


def test_sixteen_original_kernel_candidates_are_exact_ordered_and_unenrolled() -> None:
    rows = _rows()

    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert rows == candidate.make_binary_modular_exponentiation_candidate_theorems(
        TheoremSpec
    )
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        EXPECTED_ORDERED_NAMES_SHA256
    )
    assert {
        item.name: sha256(item.statement.encode()).hexdigest()
        for item in rows
    } == EXPECTED_STATEMENT_SHA256
    assert sum(len(item.script) for item in rows) == 360
    assert sum(len(item.dependencies) for item in rows) == 29

    earlier: set[str] = set()
    for item in rows:
        parsed, free = parse_formula_with_names(item.statement)
        assert not free
        assert parsed == _closed_formula(item.statement)
        assert item.name not in editions_v20.ALPHA_EDITION.by_name
        assert len(item.dependencies) == len(set(item.dependencies))
        assert set(item.dependencies) <= set(_core()) | earlier
        assert all(
            forbidden not in item.statement
            for forbidden in ("Pow(", "Mod(", "BitLen(", "Execution(", "%", "^")
        )
        assert all("DNE" not in command for command in item.script)
        earlier.add(item.name)


def test_all_sixteen_dependency_curried_proofs_pass_the_original_kernel() -> None:
    receipts = _receipts()

    assert tuple(item.name for item in receipts) == EXPECTED_NAMES
    assert tuple(item.proof_nodes for item in receipts) == EXPECTED_PROOF_NODES
    assert tuple(item.proof_depth for item in receipts) == EXPECTED_PROOF_DEPTHS
    assert tuple(item.command_count for item in receipts) == EXPECTED_COMMAND_COUNTS
    assert sum(item.proof_nodes for item in receipts) == 597
    assert max(item.proof_nodes for item in receipts) == 127
    assert max(item.proof_depth for item in receipts) == 34
    assert all(item.proof_nodes == item.proof_objects for item in receipts)
    assert all(item.proof_edges + 1 == item.proof_objects for item in receipts)


def test_all_external_prerequisites_have_sealed_checked_alpha_v20_authority() -> None:
    local = set(EXPECTED_NAMES)
    external = {
        dependency
        for item in _rows()
        for dependency in item.dependencies
        if dependency not in local
    }

    assert external == EXPECTED_EXTERNAL_PREREQUISITES
    assert all(editions_v20.ALPHA_EDITION.by_name[name].checked_use for name in external)


@pytest.mark.parametrize(
    ("builder", "arguments", "expected"),
    (
        (candidate.binary_modulus_relation, ("m",), {"m"}),
        (candidate.binary_exponent_split, ("e", "h", "b"), {"e", "h", "b"}),
        (candidate.canonical_modular_residue, ("m", "n", "r"), {"m", "n", "r"}),
        (
            candidate.binary_doubled_power,
            ("a", "h", "e", "x", "y"),
            {"a", "h", "e", "x", "y"},
        ),
        (
            candidate.binary_odd_power,
            ("a", "h", "e", "x", "z"),
            {"a", "h", "e", "x", "z"},
        ),
        (
            candidate.binary_modular_step,
            ("m", "x", "a", "b", "r"),
            {"m", "x", "a", "b", "r"},
        ),
        (
            candidate.binary_modular_power,
            ("a", "e", "m", "r"),
            {"a", "e", "m", "r"},
        ),
    ),
)
def test_public_definition_helpers_are_hygienic_and_tag_alpha_equivalent(
    builder,
    arguments: tuple[str, ...],
    expected: set[str],
) -> None:
    first, first_free = parse_formula_with_names(builder(*arguments, tag="first"))
    second, second_free = parse_formula_with_names(builder(*arguments, tag="second"))

    assert set(first_free) == set(second_free) == expected
    assert first == second
    for invalid in ("", "S", "forall", "0", "a+b", "a;b", "x y"):
        with pytest.raises(ValueError):
            builder(invalid, *arguments[1:], tag="safe")
        with pytest.raises(ValueError):
            builder(*arguments, tag=invalid)


@pytest.mark.parametrize(
    ("builder", "arguments"),
    (
        (candidate.binary_modulus_relation, ("ff_modulus_gap_binary_capture",)),
        (
            candidate.canonical_modular_residue,
            ("m", "ff_gap_binary_capture", "r"),
        ),
        (
            candidate.binary_modular_power,
            ("a", "e", "m", "ff_power_binary_capture"),
        ),
    ),
)
def test_definition_builders_reject_explicit_binder_capture(
    builder,
    arguments: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError, match="captures"):
        builder(*arguments, tag="capture")


def test_root_means_actual_unique_bounded_relational_power_but_not_an_execution() -> None:
    root = _closed_formula(_rows()[-1].statement)

    assert isinstance(root, Forall)
    assert isinstance(root.body, Forall)
    assert isinstance(root.body.body, Forall)
    implication = root.body.body.body
    assert isinstance(implication, Imp)
    assert isinstance(implication.left, Exists)
    assert isinstance(implication.right, Exists)
    assert isinstance(implication.right.body, And)
    assert isinstance(implication.right.body.left, Exists)
    assert isinstance(implication.right.body.right, Forall)
    assert " + S 1 = m" in _rows()[-1].statement
    assert "Execution(" not in _rows()[-1].statement
    assert "BitLen(" not in _rows()[-1].statement


def test_g102_blueprint_remains_honestly_open_without_formal_bitlength_trace() -> None:
    repository = Path(__file__).resolve().parents[3]
    campaign = json.loads(
        (
            repository
            / "book"
            / "_static"
            / "constructive-grand-campaign"
            / "campaign.json"
        ).read_text(encoding="utf-8")
    )
    goal = next(row for row in campaign["nodes"] if row["id"] == "G102")

    assert goal["status"] == "open"
    assert "Execution(BinaryPow" in goal["statement"]
    assert "BitLen(e)" in goal["statement"]


@pytest.mark.parametrize(
    "alteration",
    ("statement", "script", "unknown_parent", "missing_parent", "classical"),
)
def test_formal_evidence_mutations_fail_closed(alteration: str) -> None:
    rows = list(_rows())
    index = EXPECTED_NAMES.index("binary_modular_exponentiation_result_exists")
    original = rows[index]
    if alteration == "statement":
        rows[index] = replace(original, statement=original.statement.replace("forall a e m.", "forall a e m. m = 0 ->", 1))
    elif alteration == "script":
        rows[index] = replace(original, script=original.script[:-1])
    elif alteration == "unknown_parent":
        rows[index] = replace(original, dependencies=(*original.dependencies, "invented_parent"))
    elif alteration == "missing_parent":
        rows[index] = replace(original, dependencies=original.dependencies[1:])
    else:
        rows[index] = replace(original, script=("dne", *original.script))

    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(rows, core=_core())


@pytest.mark.parametrize(
    ("base", "exponent", "modulus"),
    (
        (0, 0, 2),
        (0, 1, 2),
        (0, 99, 97),
        (1, 0, 2),
        (2, 1, 2),
        (2, 2, 3),
        (2, 17, 19),
        (7, 128, 101),
        (25, 255, 97),
        (1_000_000, 65_537, 1_000_003),
        ((1 << 255) - 19, (1 << 255) - 21, (1 << 127) - 1),
    ),
)
def test_actual_binary_execution_has_exact_modular_result_and_logarithmic_bound(
    base: int,
    exponent: int,
    modulus: int,
) -> None:
    receipt = candidate.execute_binary_modular_exponentiation(base, exponent, modulus)

    assert candidate.verify_binary_modular_execution(receipt)
    assert receipt.result == pow(base, exponent, modulus)
    assert 0 <= receipt.result < modulus
    assert receipt.base_residue == base % modulus
    assert receipt.bit_length == max(1, exponent.bit_length())
    assert len(receipt.steps) == exponent.bit_length()
    assert receipt.operation_count == 2 + 2 * exponent.bit_length() + exponent.bit_count()
    assert receipt.operation_count <= 3 * receipt.bit_length + 2
    for index, row in enumerate(receipt.steps):
        assert row.index == index
        assert row.bit in {0, 1}
        assert row.previous == (1 % modulus if index == 0 else receipt.steps[index - 1].result)
        assert row.squared == row.previous * row.previous % modulus
        assert row.result == (
            row.squared * receipt.base_residue % modulus if row.bit else row.squared
        )
        assert row.prefix == exponent >> (exponent.bit_length() - index - 1)
        assert row.result == pow(base, row.prefix, modulus)


@pytest.mark.parametrize("modulus", range(2, 15))
def test_binary_algorithm_agrees_exhaustively_with_small_natural_powers(
    modulus: int,
) -> None:
    for base in range(18):
        for exponent in range(20):
            receipt = candidate.execute_binary_modular_exponentiation(
                base, exponent, modulus
            )
            assert receipt.result == pow(base, exponent, modulus)
            assert receipt.operation_count <= 3 * receipt.bit_length + 2


@pytest.mark.parametrize(
    ("base", "exponent", "modulus", "message"),
    (
        (-1, 1, 3, "base"),
        (True, 1, 3, "base"),
        (1.0, 1, 3, "base"),
        ("1", 1, 3, "base"),
        (1, -1, 3, "exponent"),
        (1, True, 3, "exponent"),
        (1, 1.0, 3, "exponent"),
        (1, 1, 0, "modulus"),
        (1, 1, 1, "modulus"),
        (1, 1, -2, "modulus"),
        (1, 1, True, "modulus"),
        (1, 1, 3.0, "modulus"),
    ),
)
def test_binary_execution_rejects_invalid_naturals_and_trivial_moduli(
    base,
    exponent,
    modulus,
    message: str,
) -> None:
    with pytest.raises(candidate.BinaryModularExponentiationError, match=message):
        candidate.execute_binary_modular_exponentiation(base, exponent, modulus)


def test_binary_execution_respects_every_reviewed_resource_boundary() -> None:
    maximal_base = (1 << candidate.MAX_BINARY_BASE_BITS) - 1
    maximal_modulus = (1 << candidate.MAX_BINARY_MODULUS_BITS) - 1

    assert candidate.verify_binary_modular_execution(
        candidate.execute_binary_modular_exponentiation(maximal_base, 1, 3)
    )
    assert candidate.verify_binary_modular_execution(
        candidate.execute_binary_modular_exponentiation(2, 1, maximal_modulus)
    )
    with pytest.raises(candidate.BinaryModularExponentiationError, match="base"):
        candidate.execute_binary_modular_exponentiation(maximal_base + 1, 1, 3)
    with pytest.raises(candidate.BinaryModularExponentiationError, match="exponent"):
        candidate.execute_binary_modular_exponentiation(
            2, 1 << candidate.MAX_BINARY_EXPONENT_BITS, 3
        )
    with pytest.raises(candidate.BinaryModularExponentiationError, match="modulus"):
        candidate.execute_binary_modular_exponentiation(2, 1, maximal_modulus + 1)


@pytest.mark.parametrize(
    "field",
    ("base", "exponent", "modulus", "base_residue", "bit_length", "operation_count", "result"),
)
def test_binary_execution_verifier_rejects_forged_top_level_values(field: str) -> None:
    receipt = candidate.execute_binary_modular_exponentiation(7, 13, 97)

    assert not candidate.verify_binary_modular_execution(
        replace(receipt, **{field: getattr(receipt, field) + 1})
    )
    assert not candidate.verify_binary_modular_execution(
        replace(receipt, **{field: True})
    )


@pytest.mark.parametrize(
    "field",
    ("index", "bit", "prefix", "previous", "squared", "result"),
)
def test_binary_execution_verifier_rejects_forged_transition_values(field: str) -> None:
    receipt = candidate.execute_binary_modular_exponentiation(7, 13, 97)
    first = receipt.steps[0]
    forged = replace(first, **{field: getattr(first, field) + 1})
    forged_bool = replace(first, **{field: True})

    assert not candidate.verify_binary_modular_execution(
        replace(receipt, steps=(forged, *receipt.steps[1:]))
    )
    assert not candidate.verify_binary_modular_execution(
        replace(receipt, steps=(forged_bool, *receipt.steps[1:]))
    )


def test_binary_execution_verifier_rejects_omitted_reordered_and_malformed_rows() -> None:
    receipt = candidate.execute_binary_modular_exponentiation(7, 13, 97)

    assert not candidate.verify_binary_modular_execution(None)
    assert not candidate.verify_binary_modular_execution(replace(receipt, steps=()))
    assert not candidate.verify_binary_modular_execution(
        replace(receipt, steps=tuple(reversed(receipt.steps)))
    )
    assert not candidate.verify_binary_modular_execution(
        replace(receipt, steps=(*receipt.steps, receipt.steps[-1]))
    )
    assert not candidate.verify_binary_modular_execution(
        replace(receipt, steps=list(receipt.steps))
    )
    assert not candidate.verify_binary_modular_execution(
        replace(receipt, steps=(None, *receipt.steps[1:]))
    )


@pytest.mark.parametrize(
    ("base", "exponent", "modulus"),
    ((0, 0, 2), (5, 1, 7), (2, 13, 17), (11, 255, 97)),
)
def test_concrete_beta_trace_encodes_every_actual_execution_coordinate(
    base: int,
    exponent: int,
    modulus: int,
) -> None:
    receipt = candidate.execute_binary_modular_exponentiation(base, exponent, modulus)
    encoded = candidate.encode_binary_modular_execution(receipt)

    assert candidate.verify_binary_modular_trace_code(receipt, encoded)
    assert len(encoded.entries) == 4 + 5 * exponent.bit_length()
    assert encoded.code.bit_length() <= candidate.MAX_BINARY_BETA_CODE_BITS
    assert encoded.entries[:4] == (
        receipt.base_residue, exponent, modulus, receipt.result
    )
    assert all(
        encoded.code % (1 + (index + 1) * encoded.scale) == value
        for index, value in enumerate(encoded.entries)
    )


def test_beta_trace_encoding_rejects_oversized_lengths_entries_and_code() -> None:
    too_long = candidate.execute_binary_modular_exponentiation(2, 1 << 24, 3)
    oversized_entry = candidate.execute_binary_modular_exponentiation(
        2, 1, 1 << candidate.MAX_BINARY_BETA_ENTRY_BITS
    )
    oversized_code = candidate.execute_binary_modular_exponentiation(
        2, (1 << 23) - 1, (1 << 255) - 19
    )

    with pytest.raises(candidate.BinaryModularExponentiationError, match="length"):
        candidate.encode_binary_modular_execution(too_long)
    with pytest.raises(candidate.BinaryModularExponentiationError, match="entry bit"):
        candidate.encode_binary_modular_execution(oversized_entry)
    with pytest.raises(candidate.BinaryModularExponentiationError, match="code bit"):
        candidate.encode_binary_modular_execution(oversized_code)


def test_beta_trace_encoding_and_verification_reject_all_mutations() -> None:
    receipt = candidate.execute_binary_modular_exponentiation(7, 13, 97)
    encoded = candidate.encode_binary_modular_execution(receipt)

    with pytest.raises(candidate.BinaryModularExponentiationError, match="invalid"):
        candidate.encode_binary_modular_execution(replace(receipt, result=0))
    assert not candidate.verify_binary_modular_trace_code(receipt, None)
    for forged in (
        replace(encoded, code=encoded.code + 1),
        replace(encoded, code=-1),
        replace(encoded, code=True),
        replace(encoded, scale=encoded.scale + 1),
        replace(encoded, scale=0),
        replace(encoded, scale=True),
        replace(encoded, entries=encoded.entries[:-1]),
        replace(encoded, entries=(True, *encoded.entries[1:])),
        replace(encoded, entries=(-1, *encoded.entries[1:])),
        replace(encoded, entries=tuple(reversed(encoded.entries))),
        replace(encoded, entries=list(encoded.entries)),
    ):
        assert not candidate.verify_binary_modular_trace_code(receipt, forged)
    other = candidate.execute_binary_modular_exponentiation(8, 13, 97)
    assert not candidate.verify_binary_modular_trace_code(other, encoded)


def test_constructive_binary_candidate_does_not_modify_immutable_v20_release() -> None:
    previous = (
        editions_v20.ALPHA_V20_IDENTITY_SHA256,
        len(editions_v20.ALPHA_CHECKED_SPECS),
        tuple(item.name for item in editions_v20.ALPHA_CHECKED_SPECS),
    )

    _rows()
    _receipts()
    candidate.execute_binary_modular_exponentiation(2, 257, 97)

    assert previous == (
        editions_v20.ALPHA_V20_IDENTITY_SHA256,
        len(editions_v20.ALPHA_CHECKED_SPECS),
        tuple(item.name for item in editions_v20.ALPHA_CHECKED_SPECS),
    )
