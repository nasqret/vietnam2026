"""Original-HA proofs of an actual, terminating Cornacchia execution.

Small integer runs below are regression examples, never proof evidence.  The
formal bodies are replayed one at a time with exact, hash-pinned v26 formulas.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from itertools import product
import json
from math import factorial, gcd, isqrt
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library import cornacchia_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.finite_fold_surface import _beta_at_term
from peano_lab.library.theorems import TheoremSpec, _closed_formula


REPO = Path(__file__).resolve().parents[3]
PARENT_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
EXPECTED_NAMES = (
    "cornacchia_prime_not_square",
    "cornacchia_prime_square_strictly_above",
    "cornacchia_prime_square_comparison",
    "cornacchia_division_quotient_nonzero",
    "cornacchia_coprime_euclidean_step",
    "cornacchia_above_threshold_remainder_nonzero",
    "cornacchia_coefficient_step_nonzero",
    "cornacchia_coefficient_step_exists",
    "cornacchia_cross_identity_step",
    "cornacchia_coefficient_square_below_prime",
    "cornacchia_mod_subtraction_transport",
    "cornacchia_signed_step_direct",
    "cornacchia_signed_step_opposite",
    "cornacchia_alternating_congruences_step",
    "cornacchia_alternating_congruences_norm_multiple",
    "cornacchia_stopping_state_represents_prime",
    "cornacchia_root_nonzero",
    "cornacchia_root_coprime",
    "cornacchia_root_exists",
    "cornacchia_initial_alternating_congruences",
    "cornacchia_initial_invariant",
    "cornacchia_invariant_euclidean_step",
    "cornacchia_invariant_stop_correct",
    "cornacchia_stopped_trace",
    "cornacchia_stopped_trace_exists",
    "cornacchia_trace_extend",
    "cornacchia_complete_from_invariant_up_to",
    "cornacchia_complete_from_invariant",
    "cornacchia_from_any_bounded_negative_one_root",
    "cornacchia_prime_two_squares_complete",
)
EXPECTED_NAMES_SHA256 = "8c7bb874131422c19eadc54046271bccfe638d138dddaaf971cb8683791abd02"
EXPECTED_BODY_NODES = (
    87, 57, 28, 37, 54, 76, 38, 5, 94, 64, 47, 143, 126, 128, 49,
    132, 55, 57, 53, 44, 62, 162, 128, 40, 77, 210, 194, 22, 39, 18,
)
EXPECTED_STATEMENTS = {
    "cornacchia_root_exists": "f49a5afb5955e03851ca818a143cf6958d3f5826d797cf5a7f8af0c3f35ca834",
    "cornacchia_invariant_euclidean_step": "59ad5af0d1727b7794bcba6f4b1f426063d8360a2f29a3f92813b59cfd3d0c0f",
    "cornacchia_invariant_stop_correct": "20e9bd7cc9323eb533c1d6264157891a9477154e89e131c187ca10f8ed6a126b",
    "cornacchia_trace_extend": "78e38912134bd98c5e7317551e9a44631ff824bb573daea139bf3b2d3940a5b0",
    "cornacchia_complete_from_invariant_up_to": "948b1f1dd0e1b07d862ac03d20234143e5aeb47a5ef4ac62402a9bd9192bdbfe",
    "cornacchia_complete_from_invariant": "3b284ad66bc7a1ac62e352afe4ba18368affad0f3dd228e6af735aaedb85bbc9",
    "cornacchia_from_any_bounded_negative_one_root": "b473b37393a7202423d12f928eacdeda26ce6c851793864e2431eab1fa713195",
    "cornacchia_prime_two_squares_complete": "becd01e6f073d37e512d385ffbc5e4e929ea3113f9d900fcc189718fc83eefc7",
}
RELATIONS = (
    (candidate.cornacchia_root, ("p", "z")),
    (candidate.cornacchia_alternating_congruences, ("p", "z", "a", "r", "u", "t")),
    (candidate.cornacchia_state_invariant, ("p", "z", "a", "r", "u", "t")),
    (candidate.cornacchia_state_at, ("h", "e", "i", "a", "r", "u", "t", "q")),
    (candidate.cornacchia_transition_at, ("p", "h", "e", "i")),
    (candidate.cornacchia_euclidean_run, ("p", "a", "r", "u", "t", "R", "T", "h", "e", "l")),
    (candidate.cornacchia_trace, ("p", "z", "R", "T", "h", "e", "l")),
)


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_cornacchia_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    # Importing a release rebuilds every historical registry and is unnecessary
    # for body checks. Authenticate the same immutable formulas/scripts instead.
    raw = (REPO / "artifacts/peano-library/alpha/catalog-v26.json").read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    rows = json.loads(raw)["theorems"]
    assert len(rows) == 2_138
    return {
        row["name"]: TheoremSpec(
            row["name"], row["statement"], tuple(row["dependencies"]),
            tuple(row["script"]), row.get("summary", ""),
        )
        for row in rows
    }


@lru_cache(maxsize=1)
def _all() -> dict[str, TheoremSpec]:
    return _core() | {row.name: row for row in _rows()}


@lru_cache(maxsize=1)
def _receipts():
    return tuple(replay_candidate_bodies((row,), core=_all())[0] for row in _rows())


def _conjunction(*formulas: str) -> str:
    if len(formulas) == 1:
        return formulas[0]
    return f"({formulas[0]}) /\\ ({_conjunction(*formulas[1:])})"


def _state(h: str, e: str, i: str, a: str, r: str, u: str, t: str, q: str, tag: str) -> str:
    return candidate._state(h, e, i, a, r, u, t, q, tag=tag)


def test_inventory_is_additive_dependency_ordered_closed_and_deterministic() -> None:
    assert _rows() == candidate.make_cornacchia_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in _rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert len(_rows()) == 30
    assert sum(len(row.dependencies) for row in _rows()) == 112
    assert sum(len(row.script) for row in _rows()) == 1_190
    assert max(len(row.statement) for row in _rows()) == 31_110
    available = set(_core())
    for row in _rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        formula, free = parse_formula_with_names(row.statement)
        assert not free and formula == _closed_formula(row.statement)
        assert all(
            not any(token in command for token in ("DNE", "sorry", "admit", "oracle", "axiom"))
            and not command.startswith("use ")
            for command in row.script
        )
        available.add(row.name)


def test_all_bodies_pass_original_heyting_kernel_in_one_row_microbatches() -> None:
    assert tuple(receipt.name for receipt in _receipts()) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in _receipts()) == EXPECTED_BODY_NODES
    assert sum(receipt.proof_nodes for receipt in _receipts()) == 2_326
    assert max(receipt.proof_nodes for receipt in _receipts()) == 210
    assert max(receipt.proof_depth for receipt in _receipts()) == 69


@pytest.mark.parametrize(("name", "digest"), EXPECTED_STATEMENTS.items())
def test_exact_major_statement_hashes(name: str, digest: str) -> None:
    assert sha256(_all()[name].statement.encode()).hexdigest() == digest


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_false_conclusion_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=f"({row.statement}) /\\ false"),), core=_all())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_body_rejected(name: str) -> None:
    row = _all()[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=row.script[:-1]),), core=_all())


@pytest.mark.parametrize("name", tuple(name for name in EXPECTED_NAMES if name not in {
    "cornacchia_prime_not_square", "cornacchia_coefficient_step_exists", "cornacchia_stopped_trace",
}))
def test_missing_dependency_rejected(name: str) -> None:
    row = _all()[name]
    assert row.dependencies
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, dependencies=row.dependencies[:-1]),), core=_all())


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_definitions_are_native_hygienic_alpha_invariant_expansions(builder, arguments) -> None:
    first, free = parse_formula_with_names(builder(*arguments, tag="first"))
    second, other = parse_formula_with_names(builder(*arguments, tag="second"))
    assert first == second
    assert set(free) == set(other) == set(arguments)
    assert all(token not in builder(*arguments, tag="audit") for token in (
        "Cornacchia", "IsGCD", "Coprime", "ModEq", "Beta", "Rep2",
    ))


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "x + y", "0", "x;y"))
def test_definitions_reject_formula_injection_in_arguments(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError):
        builder(fragment, *arguments[1:], tag="safe")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", ("", "S", "forall", "x + y", "0", "x;y"))
def test_definitions_reject_formula_injection_in_tags(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError):
        builder(*arguments, tag=fragment)


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
@pytest.mark.parametrize("fragment", (
    "cor_a_capture", "cf_i_capture", "ff_value_capture", "frm_prime_left_capture",
    "frp_divisor_capture", "hgcrt_witness_capture", "ec_gcd_common_capture",
))
def test_definitions_reject_all_generated_binder_names(builder, arguments, fragment: str) -> None:
    with pytest.raises(ValueError, match="capture"):
        builder(fragment, *arguments[1:], tag="capture")


@pytest.mark.parametrize(("builder", "arguments"), RELATIONS)
def test_definitions_reject_duplicate_arguments(builder, arguments) -> None:
    with pytest.raises(ValueError, match="distinct"):
        builder(arguments[1], *arguments[1:], tag="safe")


def test_exact_root_is_prime_positive_bounded_and_a_root_of_minus_one() -> None:
    expected = _conjunction(
        prime("p", tag="audit"), "~(z=0)", "exists k. k+S z=p", "exists q. z*z+1=p*q",
    )
    actual = candidate.cornacchia_root("p", "z", tag="root_audit")
    assert _closed_formula(f"forall p z. {actual}") == _closed_formula(f"forall p z. {expected}")


def test_state_really_encodes_both_remainders_both_coefficients_and_the_quotient() -> None:
    def pair(a: str, b: str) -> str:
        return f"(({a}+{b})*S({a}+{b})+({b}+{b}))"

    # Independent literal doubled-Cantor shape, rather than a symbolic tuple
    # whose components could accidentally be omitted from the beta relation.
    packed = pair(pair("a", "r"), pair(pair("u", "t"), "q"))
    expected = _beta_at_term("h", "e", "i", packed, tag="audit_beta", avoid=("h", "e", "i", "a", "r", "u", "t", "q"))
    actual = candidate.cornacchia_state_at("h", "e", "i", "a", "r", "u", "t", "q", tag="state_audit")
    assert _closed_formula(f"forall h e i a r u t q. {actual}") == _closed_formula(f"forall h e i a r u t q. {expected}")


def test_transition_links_adjacent_encoded_states_and_has_the_actual_guarded_recurrence() -> None:
    expected = "exists a r u t q A R U T Q. (" + _conjunction(
        _state("h", "e", "S i", "a", "r", "u", "t", "q", "audit_before"),
        _state("h", "e", "i", "A", "R", "U", "T", "Q", "audit_after"),
        _conjunction("A=r", "U=t", "a=r*q+R", "exists k. k+S R=r", "T=q*t+u", "exists k. k+S p=r*r"),
    ) + ")"
    actual = candidate.cornacchia_transition_at("p", "h", "e", "i", tag="transition_audit")
    assert _closed_formula(f"forall p h e i. {actual}") == _closed_formula(f"forall p h e i. {expected}")


def test_run_identifies_both_endpoints_and_every_transition_before_the_first_stop() -> None:
    expected = "exists A U Q. (" + _conjunction(
        _state("h", "e", "0", "A", "R", "U", "T", "0", "audit_terminal"),
        _state("h", "e", "l", "a", "r", "u", "t", "Q", "audit_initial"),
        "~(R=0)", "~(T=0)", "exists k. k+S(R*R)=p",
        "forall i. (exists k. k+S i=l) -> (" + candidate.cornacchia_transition_at("p", "h", "e", "i", tag="audit_transition") + ")",
    ) + ")"
    actual = candidate.cornacchia_euclidean_run("p", "a", "r", "u", "t", "R", "T", "h", "e", "l", tag="run_audit")
    assert _closed_formula(f"forall p a r u t R T h e l. {actual}") == _closed_formula(f"forall p a r u t R T h e l. {expected}")


def test_complete_trace_starts_at_the_same_root_and_fixed_initial_coefficients() -> None:
    expected = _conjunction(
        candidate.cornacchia_root("p", "z", tag="audit_root"),
        candidate._run("p", "p", "z", "0", "1", "R", "T", "h", "e", "l", tag="audit_rooted_run"),
    )
    actual = candidate.cornacchia_trace("p", "z", "R", "T", "h", "e", "l", tag="trace_audit")
    assert _closed_formula(f"forall p z R T h e l. {actual}") == _closed_formula(f"forall p z R T h e l. {expected}")


def test_full_endpoint_constructs_root_history_and_its_returned_coordinates_without_supplied_trace() -> None:
    expected = (
        f"forall p. ({prime('p', tag='audit_prime')}) -> (exists k. p=4*k+1) -> "
        "exists z R T h e l. ((" + candidate.cornacchia_trace("p", "z", "R", "T", "h", "e", "l", tag="audit_trace")
        + ") /\\ p=R*R+T*T)"
    )
    actual = _closed_formula(_all()["cornacchia_prime_two_squares_complete"].statement)
    assert actual == _closed_formula(expected)
    assert isinstance(actual, Forall)
    assert isinstance(actual.body, Imp) and isinstance(actual.body.right, Imp)
    output = actual.body.right.right
    for _ in range(6):
        assert isinstance(output, Exists)
        output = output.body
    assert isinstance(output, And)


def test_algorithm_works_from_every_bounded_root_not_a_preselected_successful_one() -> None:
    expected = (
        "forall p z. (" + candidate.cornacchia_root("p", "z", tag="audit_given_root")
        + ") -> exists R T h e l. (("
        + candidate.cornacchia_trace("p", "z", "R", "T", "h", "e", "l", tag="audit_produced_run")
        + ") /\\ p=R*R+T*T)"
    )
    assert _closed_formula(_all()["cornacchia_from_any_bounded_negative_one_root"].statement) == _closed_formula(expected)


def test_total_history_is_constructed_by_induction_and_real_beta_extension() -> None:
    induction = _all()["cornacchia_complete_from_invariant_up_to"]
    assert "induction B" in induction.script
    assert {"euclidean_division_step_exists", "cornacchia_invariant_euclidean_step", "cornacchia_trace_extend"} <= set(induction.dependencies)
    extension = _all()["cornacchia_trace_extend"]
    assert "beta_prefix_extend" in extension.dependencies
    assert any(command.startswith("specialize beta_prefix_extend ") for command in extension.script)
    assert "cornacchia_stopped_trace_exists" in induction.dependencies


def test_dependency_cone_has_no_supplied_two_square_representation_shortcut() -> None:
    reached: set[str] = set()

    def visit(name: str) -> None:
        if name in reached:
            return
        reached.add(name)
        for dependency in _all()[name].dependencies:
            visit(dependency)

    visit("cornacchia_prime_two_squares_complete")
    assert "prime_mod_four_one_bounded_divisible_two_square_norm_exists" in reached
    assert "cornacchia_alternating_congruences_norm_multiple" in reached
    assert "cornacchia_complete_from_invariant_up_to" in reached
    assert "prime_mod_four_one_is_sum_of_two_squares" not in reached
    assert "prime_is_two_squares_iff_two_or_one_mod_four" not in reached


def _pack_values(a: int, r: int, u: int, t: int, q: int) -> int:
    def pair(x: int, y: int) -> int:
        return (x + y) * (x + y + 1) + 2 * y

    return pair(pair(a, r), pair(pair(u, t), q))


def _actual_run(p: int, z: int) -> list[tuple[int, int, int, int, int]]:
    a, r, u, t = p, z, 0, 1
    states: list[tuple[int, int, int, int, int]] = []
    while r * r > p:
        q, s = divmod(a, r)
        states.append((a, r, u, t, q))
        a, r, u, t = r, s, t, q * t + u
    states.append((a, r, u, t, 0))
    return states


def _valid_run(p: int, z: int, R: int, T: int, states: list[tuple[int, int, int, int, int]]) -> bool:
    if not states or not (0 < z < p) or (z * z + 1) % p:
        return False
    if states[0][:4] != (p, z, 0, 1):
        return False
    a, r, u, t, q = states[-1]
    if (r, t, q) != (R, T, 0) or not (R > 0 and T > 0 and R * R < p):
        return False
    for before, after in zip(states, states[1:]):
        a, r, u, t, q = before
        A, s, U, V, _ = after
        if not (A == r and U == t and a == r * q + s and 0 <= s < r and V == q * t + u and p < r * r):
            return False
    return True


def _beta_code(values: list[int]) -> tuple[int, int]:
    scale = (max(values, default=0) + 1) * factorial(len(values))
    code, modulus = 0, 1
    for i, value in enumerate(values):
        next_modulus = 1 + (i + 1) * scale
        assert value < next_modulus and gcd(modulus, next_modulus) == 1
        code += modulus * (((value - code) * pow(modulus, -1, next_modulus)) % next_modulus)
        modulus *= next_modulus
    return code, scale


def test_small_prime_runs_use_every_actual_root_and_all_arithmetic_invariants() -> None:
    runs = 0
    for p in range(2, 201):
        if any(p % d == 0 for d in range(2, isqrt(p) + 1)):
            continue
        for z in range(1, p):
            if (z * z + 1) % p:
                continue
            states = _actual_run(p, z)
            _, R, _, T, _ = states[-1]
            assert _valid_run(p, z, R, T, states)
            assert R * R + T * T == p
            for a, r, u, t, _ in states:
                assert p == a * t + r * u
                assert gcd(a, r) == 1 and 0 < r < a and t > 0
                assert p < a * a and t * t < p
                assert ((a - z * u) % p == 0 and (r + z * t) % p == 0) or (
                    (a + z * u) % p == 0 and (r - z * t) % p == 0
                )
            values = [_pack_values(*state) for state in reversed(states)]
            h, e = _beta_code(values)
            assert [h % (1 + (i + 1) * e) for i in range(len(values))] == values
            runs += 1
    assert runs == 43  # Prime 2, plus both roots for each of 21 primes 1 mod 4.


@pytest.mark.parametrize(("p", "z", "expected"), (
    (2, 1, [(2, 1, 0, 1, 0)]),
    (5, 2, [(5, 2, 0, 1, 0)]),
    (5, 3, [(5, 3, 0, 1, 1), (3, 2, 1, 1, 0)]),
    (13, 8, [(13, 8, 0, 1, 1), (8, 5, 1, 1, 1), (5, 3, 1, 2, 0)]),
))
def test_zero_step_and_multistep_boundaries_have_exact_returned_states(p: int, z: int, expected) -> None:
    assert _actual_run(p, z) == expected
    _, R, _, T, _ = expected[-1]
    assert _valid_run(p, z, R, T, expected)


def test_example_checker_rejects_unrelated_outputs_bad_quotients_and_late_stopping() -> None:
    states = _actual_run(13, 8)
    assert _valid_run(13, 8, 3, 2, states)
    assert not _valid_run(13, 8, 2, 3, states)  # Also a representation, not this run's output.
    bad = list(states)
    a, r, u, t, q = bad[0]
    bad[0] = (a, r, u, t, q + 1)
    assert not _valid_run(13, 8, 3, 2, bad)
    late = [*states[:-1], (5, 3, 1, 2, 1), (3, 2, 2, 3, 0)]
    assert not _valid_run(13, 8, 2, 3, late)  # The extra transition starts below sqrt(13).
    assert not _valid_run(13, 5, 3, 2, states)  # Another root cannot relabel this history.


def test_doubled_cantor_state_encoding_preserves_all_five_components_in_examples() -> None:
    states = tuple(product(range(4), repeat=5))
    values = {_pack_values(*state) for state in states}
    assert len(values) == len(states)
