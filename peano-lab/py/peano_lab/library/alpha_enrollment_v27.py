"""Strict additive second-wave enrollment over the immutable Alpha-v26 edition.

Enrollment records reviewed specifications, not proof authority. Checked use
requires every actual body in the exact dependency-closed artifact to pass the
unchanged intuitionistic kernel; publication additionally runs the independent
compiled Lean verifier. Historical admission records and Stable stay intact.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from . import editions_v26 as v26
from .campaign_second_wave_closure import FACTORIES
from .theorems import TheoremSpec, _closed_formula


class AlphaV27EnrollmentError(ValueError):
    """The frozen parent, reviewed proof factory, or dependency DAG changed."""


class FrontierV27Campaign(str, Enum):
    MATRIX_DETERMINANTS = "matrix_determinants"
    HENSEL = "hensel"
    GENERALIZED_CRT = "generalized_crt"
    MULTINOMIAL_KUMMER = "multinomial_kummer"
    CHEBYSHEV = "chebyshev"
    CORNACCHIA = "cornacchia"
    CAUCHY_DAVENPORT = "cauchy_davenport"


@dataclass(frozen=True, slots=True)
class AlphaV27Enrollment:
    parent_entries: tuple[v26.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV27Campaign]


PARENT_ALPHA_V26_COUNT = 2_138
PARENT_ALPHA_V26_ENROLLMENT_SHA256 = (
    "cdf2cd0adfef8f1becd6f1f62d4d1d5d7a1891838e16b52a4d1cdaca98c496f2"
)
PARENT_ALPHA_V26_IDENTITY_SHA256 = (
    "8573945e4bdfe0a8d9414b499828ced67eff3b886e5adde50a0fcff81cfbdc19"
)

# Frozen after the complete seven-campaign artifact passed both verifiers.
FRONTIER_V27_EXPECTED_COUNT = 422
FRONTIER_V27_EXPECTED_EDGE_COUNT = 1_345
FRONTIER_V27_EXPECTED_NAMES_SHA256 = "e925d4355f63aad9874fac92a3ec05362162793ec1fc2eea909ac1e1ede8f01b"
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV27Campaign, int] = {
    FrontierV27Campaign.MATRIX_DETERMINANTS: 182,
    FrontierV27Campaign.HENSEL: 40,
    FrontierV27Campaign.GENERALIZED_CRT: 24,
    FrontierV27Campaign.MULTINOMIAL_KUMMER: 19,
    FrontierV27Campaign.CHEBYSHEV: 55,
    FrontierV27Campaign.CORNACCHIA: 30,
    FrontierV27Campaign.CAUCHY_DAVENPORT: 72,
}
EXPECTED_FACTORY_COUNTS: dict[str, int] = {
    "matrix_recursive_determinant_candidate": 24,
    "matrix_recursive_determinant_extensional_candidate": 20,
    "matrix_rank_finite_coding_candidate": 19,
    "matrix_rank_selected_minors_candidate": 21,
    "matrix_rank_certificate_candidate": 15,
    "integer_column_span_candidate": 33,
    "matrix_integer_invariance_candidate": 16,
    "matrix_rank_integer_invariance_candidate": 11,
    "matrix_lattice_data_candidate": 23,
    "hensel_prime_power_candidate": 19,
    "signed_hensel_lifting_candidate": 17,
    "hensel_simple_root_criterion_candidate": 4,
    "generalized_crt_full_candidate": 24,
    "multinomial_kummer_candidate": 19,
    "prime_count_chebyshev_candidate": 55,
    "cornacchia_candidate": 30,
    "finite_modular_set_candidate": 49,
    "cauchy_davenport_candidate": 23,
}
ROOT_STATEMENT_SHA256: dict[str, str] = {
    "signed_recursive_determinant_exists_unique": "bf78d0b39617ddaabf5e7b617a4e5474ee57d308c14d296de7a54e93d42d0dbc",
    "signed_recursive_determinant_cofactor_equation": "584c7cd696d0844f5748f21a45f4a408b3a321ad64097c2a5bebfc623194970d",
    "signed_recursive_determinant_empty_equation": "cd74d5fd1dda41357c2a9cbbbec952fe1d8bcd2c3d9c7b21f85b4125daba7cb0",
    "rectangular_matrix_rank_exists_unique": "677f945b5341792d5b2281cc8948922456c461c1aeeec880c452199df7d178f1",
    "rectangular_matrix_rank_successor_minors_zero": "3f79bf62134e5de89064d0a4181a1e00ff647b3b309498c1b127c30da468de9d",
    "integer_column_span_contains_zero": "1df52e34af59b05182acebe099349fc54eb8b6ca59ac55dccdc096bc8aaf0d01",
    "integer_column_span_add_exists": "4c3ef723161578a73747c914a683d2b50ad3a80d087ee222b56a14ef4a1e296a",
    "integer_column_span_negate_exists": "c6723d098ae92d7069c1ae12d5207fb1c133bd40ec63ad6bd596df954791736a",
    "integer_polynomial_prime_simple_root_lifts_all_positive_powers": "158b28822061f364d34a4badf84986d5f02301b58c555b1e67ec758c786709e8",
    "crt_pairwise_compatible_prefix_normalized_exists_unique": "f333d811cf04309d630382e2c049885d0de6e2cf4f26a218faf0e6039b002587",
    "crt_pairwise_compatible_prefix_canonical_exists_unique": "ac5e941743de53a1954904f99231acf74a38f59c15ed7887d3896cf3b8fe65b8",
    "crt_pairwise_compatible_prefix_solvable_iff": "bbaf5b097637ebfb6178b95ff37f6fed77776532c4058ece4f2f79a94e65ba64",
    "multinomial_exists": "ce01b5413f8c187fd18fafea53aa19619510ca975c179b88a5c732d3bf71299c",
    "multinomial_kummer_carry_valuation": "f69d92599b4eaa9e893e3a4c0e8ab998234bbce6223fbbde949433c1ee7c8266",
    "prime_count_chebyshev_bounds": "38a80957c2e9e9545cf57e1a036768d506a64edd891be2d0125ffd499fab7428",
    "prime_count_exists_unique": "c4255dbed70cfaf30b466653ecbb13f24ab98d362095fd6331fcce9263c85708",
    "cornacchia_prime_two_squares_complete": "becd01e6f073d37e512d385ffbc5e4e929ea3113f9d900fcc189718fc83eefc7",
    "cornacchia_from_any_bounded_negative_one_root": "b473b37393a7202423d12f928eacdeda26ce6c851793864e2431eab1fa713195",
    "prime_cauchy_davenport_sumset_exists": "7f2babcbea49f9ebe8e3a5d2339d0009d16d61afbe33341fcf7b951ede80b6e1",
    "prime_cauchy_davenport_sumset_bound": "634e3a5403ad025cef1e894dc2b9c3401691bb84bb57c2b70cb3aba185b806fb",
    "finite_modular_sumset_exists": "46420a141069c2696880ec30397f7cedaa2c8b7866ddc2791ec2aff0c799a9d9",
    "signed_recursive_determinant_integer_invariant": "a5587046845e712ff96b73c8fc4f54b9ecfeac5cfa224a1d537c6ce20f728dd6",
    "rectangular_matrix_rank_integer_invariant": "d6c74c06c5a55da7ec89d026a4658e49604b6f6b11521d1b453c8bfa16168151",
    "absolute_recursive_determinant_exists_unique": "1a01953c2267c95c0c92fb0b853dade02a33fbf1dbee71af3dfa3a97378bcad8",
    "positive_determinant_matrix_data_exists_unique": "2d8c3aec5c5751dc8325a28477c9b6c7b7ddd8d8cd20bcc719d7af518bcc2676",
    "positive_determinant_matrix_data_full_rank": "2d861924f0f0b78f626e57e1521a2fa6145abe7bf1eadae069ecd2a906b20b48",
    "square_matrix_full_rank_from_nonzero_determinant": "4c54da0a9e91e210d5a9f1d93711e28706532e435a889f22a8beb470abe4bb1a",
}


def _validate_parent() -> None:
    if (
        len(v26.ALPHA_ENTRIES) != PARENT_ALPHA_V26_COUNT
        or len(v26.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V26_COUNT
        or v26.ALPHA_V26_ENROLLMENT_SHA256 != PARENT_ALPHA_V26_ENROLLMENT_SHA256
        or v26.ALPHA_V26_IDENTITY_SHA256 != PARENT_ALPHA_V26_IDENTITY_SHA256
        or len(v26.STABLE_SPECS) != 432
    ):
        raise AlphaV27EnrollmentError("immutable completely checked Alpha-v26 parent changed")


@lru_cache(maxsize=1)
def alpha_v27_enrollment() -> AlphaV27Enrollment:
    _validate_parent()
    if tuple(owner.module for owner in FACTORIES) != tuple(EXPECTED_FACTORY_COUNTS):
        raise AlphaV27EnrollmentError("reviewed Alpha-v27 factory inventory or order changed")
    available = {entry.spec.name for entry in v26.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV27Campaign] = {}

    for owner in FACTORIES:
        if (
            owner.factory != f"make_{owner.module}_theorems"
            or not owner.rfc.endswith("-rfc-v1.md")
            or "/" in owner.rfc or "\\" in owner.rfc or ".." in owner.rfc
        ):
            raise AlphaV27EnrollmentError("reviewed Alpha-v27 factory metadata changed")
        try:
            campaign = FrontierV27Campaign(owner.campaign)
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV27EnrollmentError(
                f"unavailable reviewed Alpha-v27 factory {owner.module}.{owner.factory}"
            ) from error
        if len(candidates) != EXPECTED_FACTORY_COUNTS[owner.module]:
            raise AlphaV27EnrollmentError(
                f"exact Alpha-v27 factory cardinality changed: {owner.module}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec or item.name in available:
                raise AlphaV27EnrollmentError("invalid or duplicate additive Alpha-v27 theorem")
            missing = set(item.dependencies).difference(available)
            if missing or len(set(item.dependencies)) != len(item.dependencies):
                raise AlphaV27EnrollmentError(
                    f"invalid Alpha-v27 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith("use ") for command in item.script
            ):
                raise AlphaV27EnrollmentError(
                    f"Alpha-v27 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            sources[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            tests[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfcs[item.name] = f"research/arithmetic-library/{owner.rfc}"
            campaigns[item.name] = campaign
            rows.append(item)
            available.add(item.name)

    if Counter(campaigns.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise AlphaV27EnrollmentError("exact Alpha-v27 aggregate campaign cardinalities changed")
    if FRONTIER_V27_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V27_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V27_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V27_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV27EnrollmentError("exact additive Alpha-v27 second-wave frontier changed")
    by_name = {item.name: item for item in rows}
    for name, expected in ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV27EnrollmentError(f"exact Alpha-v27 campaign root changed: {name}")

    return AlphaV27Enrollment(
        parent_entries=v26.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(sources),
        test_by_name=MappingProxyType(tests),
        rfc_by_name=MappingProxyType(rfcs),
        campaign_by_name=MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV27Enrollment", "AlphaV27EnrollmentError", "EXPECTED_CAMPAIGN_COUNTS",
    "EXPECTED_FACTORY_COUNTS", "FRONTIER_V27_EXPECTED_COUNT",
    "FRONTIER_V27_EXPECTED_EDGE_COUNT", "FRONTIER_V27_EXPECTED_NAMES_SHA256",
    "FrontierV27Campaign", "PARENT_ALPHA_V26_COUNT",
    "PARENT_ALPHA_V26_ENROLLMENT_SHA256", "PARENT_ALPHA_V26_IDENTITY_SHA256",
    "ROOT_STATEMENT_SHA256", "alpha_v27_enrollment",
)
