"""Additive conservative notation for the next five-goal priority campaign.

Every historical definition object is reused unchanged. The totient count is
independent of its Euler product; natural squarefree kernels are not confused
with the blueprint's polynomial SquarefreeDecomposition homonym; convergents
are actual computations, not records containing approximation conclusions.
This registry grants notation only, never theorem or Alpha authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import sys
from types import MappingProxyType
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "peano-lab/py") not in sys.path:
    sys.path.insert(0, str(ROOT / "peano-lab/py"))

from constructive_lower_layer_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.library.ha_pair_cell_seed_candidate import pair_code
from peano_lab.library.matrix_lattice_data_candidate import _absolute
from peano_lab.library.prime_valuation_support_candidate import (
    prime_exponent_entries_relation, prime_divisor_support_relation,
    prime_valuation_support_relation,
)
from peano_lab.library.euler_totient_count_candidate import (
    unit_bit_prefix_relation, unit_count_relation, totient_relation,
)
from peano_lab.library.euler_totient_product_candidate import (
    totient_prime_power_factor_relation, totient_euler_factor_prefix_relation,
    totient_euler_product_relation,
)
from peano_lab.library.squarefree_decomposition_candidate import (
    squarefree_relation, squarefree_decomposition_relation,
)
from peano_lab.library.perfect_power_profile_candidate import (
    prime_valuations_divisible_relation, prime_exponent_prefix_gcd_relation,
    perfect_power_root_table_relation, perfect_power_profile_code_relation,
    perfect_power_profile_data_relation, perfect_power_profile_relation,
)
from peano_lab.library.odd_prime_lte_candidate import (
    power_difference_quotient_relation, power_difference_second_order_relation,
    lifted_power_difference_relation,
)
from peano_lab.library.continued_fraction_approximation_candidate import (
    rational_approximation_error_relation, alternating_convergent_identity_relation,
    convergent_error_invariant_relation,
)
from peano_lab.library.continued_fraction_convergents_candidate import (
    convergent_matrix_state_code_relation, convergent_matrix_state_at_relation,
    convergent_matrix_trace_relation, convergent_relation,
    best_approximation_second_kind_relation,
)


def _contextual(builder: Callable[..., str]) -> Callable[..., str]:
    def expand(*values: str, tag: str) -> str:
        return builder(*values, tag=tag, variables=tuple(values))
    return expand


def _construct(identifier: int, name: str, parameters: tuple[str, ...],
               builder: Callable[..., str], summary: str,
               dependencies: tuple[str, ...] = ()) -> DefinitionSpec:
    return _definition(
        stable_id=f"ND{identifier:04d}", name=name, parameters=parameters,
        template_source=builder(*parameters, tag="prioritylayer"), summary=summary,
        category="constructive_priority_layer", priority="P2",
        conceptual_dependencies=dependencies,
    )


PRIORITY_LAYER_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(177, "NaturalPair", ("z", "a", "b"),
               lambda *values, tag: pair_code(*values),
               "The original injective doubled-Cantor code z=(a+b)(a+b+1)+2b. It does not claim every natural is a valid pair code."),
    _construct(178, "NaturalAbsDifference", ("p", "n", "D"),
               lambda *values, tag: _absolute(*values),
               "The actual nonnegative absolute difference |p−n|, witnessed by one of the two natural balance equations."),
    _construct(179, "PrimeExponentEntries", ("n", "pb", "pc", "eb", "ec", "vb", "vc", "l"),
               _contextual(prime_exponent_entries_relation),
               "Each bounded index simultaneously decodes an actual prime, its positive valuation in n, and the value of that prime power.",
               ("Lt", "BetaAt", "Prime", "PowerValuation", "Pow")),
    _construct(180, "PrimeDivisorSupport", ("n", "pb", "pc", "l"),
               _contextual(prime_divisor_support_relation),
               "Every actual prime divisor of n occurs at a witnessed index in this prime prefix; no prime divisor may be omitted.",
               ("Prime", "Dvd", "Lt", "BetaAt")),
    _construct(181, "PrimeValuationSupport", ("n", "pb", "pc", "eb", "ec", "vb", "vc", "l"),
               _contextual(prime_valuation_support_relation),
               "Positive n, distinct actual prime/exponent/power entries, complete coverage of prime divisors, and an actual finite product equal to n. One has the empty support.",
               ("InjectivePrefix", "PrimeExponentEntries", "PrimeDivisorSupport", "Product")),
    _construct(182, "UnitBitPrefix", ("n", "b", "c", "l"), unit_bit_prefix_relation,
               "The decoded bit at i<l is one exactly for Coprime(i,n), and zero otherwise. The interval starts at zero.",
               ("Lt", "BetaAt", "Coprime")),
    _construct(183, "UnitCount", ("n", "l", "t"), unit_count_relation,
               "An actual beta sum counts the coprime residues in 0≤i<l. This auxiliary count is total even at modulus zero.",
               ("UnitBitPrefix", "Sum")),
    _construct(184, "Phi", ("n", "t"), totient_relation,
               "Positive n and the actual count of canonical residues i<n coprime to n. Phi(1,1) counts residue zero; Phi excludes n=0.",
               ("UnitCount",)),
    _construct(185, "EulerPrimePowerFactor", ("p", "e", "c"), totient_prime_power_factor_relation,
               "For an actual prime and positive exponent, explicit predecessor and power witnesses compute c=p^(e−1)(p−1). No totient count is assumed.",
               ("Prime", "Pow")),
    _construct(186, "EulerFactorPrefix", ("pb", "pc", "eb", "ec", "fb", "fc", "l"), totient_euler_factor_prefix_relation,
               "At every bounded index, the same prime/exponent entries determine the actual Euler factor in the third beta prefix.",
               ("Lt", "BetaAt", "EulerPrimePowerFactor")),
    _construct(187, "EulerProduct", ("n", "t"), totient_euler_product_relation,
               "A complete distinct prime-valuation support, its independently computed Euler factors, and their actual product t. Equality with Phi is a theorem, not a definition.",
               ("PrimeValuationSupport", "EulerFactorPrefix", "Product")),
    _construct(188, "Squarefree", ("n",), _contextual(squarefree_relation),
               "Positive n with no squared prime divisor p² for any prime p≤n. The bounded condition is proved to exclude all squared prime divisors.",
               ("Prime", "Le", "Dvd")),
    _construct(189, "NaturalSquarefreeDecomposition", ("n", "r", "s"), _contextual(squarefree_decomposition_relation),
               "An actual squarefree natural r and the balance n=r·s². This is not the blueprint's unrelated polynomial SquarefreeDecomposition predicate.",
               ("Squarefree",)),
    _construct(190, "PrimeValuationsDivisible", ("n", "k"), _contextual(prime_valuations_divisible_relation),
               "Every actual prime valuation of n is divisible by k. Root theorems separately require positive n and positive k.",
               ("Prime", "PowerValuation", "Dvd")),
    _construct(191, "PrimeExponentPrefixGCD", ("b", "c", "l", "g"), _contextual(prime_exponent_prefix_gcd_relation),
               "g divides every actual decoded exponent, and every common divisor of these exponents divides g. The empty-prefix gcd is zero.",
               ("Lt", "BetaAt", "Dvd")),
    _construct(192, "PerfectPowerRootTable", ("n", "g", "b", "c"), _contextual(perfect_power_root_table_relation),
               "For each positive divisor k of g, the table actually decodes a root r with Pow(r,k,n). It is constructed after the root-existence proof.",
               ("Dvd", "BetaAt", "Pow")),
    _construct(193, "PerfectPowerProfileCode", ("w", "pb", "pc", "eb", "ec", "vb", "vc", "l", "g", "rb", "rc"),
               _contextual(perfect_power_profile_code_relation),
               "A real nested historical pair code stores the seven support fields, exponent gcd, and two root-table codes.",
               ("NaturalPair",)),
    _construct(194, "PerfectPowerProfileData", ("n", "w", "pb", "pc", "eb", "ec", "vb", "vc", "l", "g", "rb", "rc"),
               _contextual(perfect_power_profile_data_relation),
               "The nonunit positive input, its actual encoded complete prime support, positive exponent gcd, and all root-table witnesses.",
               ("PerfectPowerProfileCode", "PrimeValuationSupport", "PrimeExponentPrefixGCD", "PerfectPowerRootTable")),
    _construct(195, "PowerProfile", ("n", "w"), _contextual(perfect_power_profile_relation),
               "Either n=1 with code zero and a uniform proof of every positive unit power, or the actual finite nonunit prime-valuation and root profile. Zero is excluded.",
               ("Pow", "PerfectPowerProfileData")),
    _construct(196, "PowerDifferenceQuotient", ("a", "b", "n", "A", "B", "d", "q"),
               _contextual(power_difference_quotient_relation),
               "Actual powers A=a^n, B=b^n and balances a=b+d, A=B+dq. No prime, valuation, or LTE conclusion is assumed.",
               ("Pow",)),
    _construct(197, "PowerDifferenceSecondOrder", ("a", "b", "d", "k", "A", "B", "R", "T", "Q", "C", "H"),
               _contextual(power_difference_second_order_relation),
               "Four actual powers at exponents k+2,k+1,k and three subtraction-free difference/correction balances. Ordinary induction constructs all seven witnesses.",
               ("Pow",)),
    _construct(198, "LiftedPowerDifference", ("p", "a", "b", "n", "e", "A", "B", "D"),
               _contextual(lifted_power_difference_relation),
               "An output certificate: actual n-th powers, positive p-divisible difference D, a p-nondivisible second power, and actual valuation e. Its existence is proved, not assumed.",
               ("Pow", "Dvd", "PowerValuation")),
    _construct(199, "RationalApproximationError", ("a", "b", "rp", "rn", "t", "E"),
               _contextual(rational_approximation_error_relation),
               "The exact cross-product error |a·t−b·(rp−rn)| for an arbitrary signed numerator. This is not an approximation inequality.",
               ("NaturalAbsDifference",)),
    _construct(200, "AlternatingConvergentIdentity", ("a", "b", "u", "U", "v", "V", "E", "F"),
               _contextual(alternating_convergent_identity_relation),
               "Adjacent determinant ±1 with the two correctly alternating natural error balances. It is derived from the actual quotient computation."),
    _construct(201, "ConvergentErrorInvariant", ("a", "b", "u", "U", "v", "V"),
               _contextual(convergent_error_invariant_relation),
               "Actual adjacent determinant/error witnesses with strictly decreasing current error and previous error at most b. This proved invariant is not part of Convergent.",
               ("AlternatingConvergentIdentity", "Lt", "Le")),
    _construct(202, "ConvergentMatrixCode", ("s", "u", "U", "v", "V", "z"),
               _contextual(convergent_matrix_state_code_relation),
               "A nested original pair code stores the quotient suffix and two numerator/denominator matrix columns.",
               ("NaturalPair",)),
    _construct(203, "ConvergentMatrixAt", ("h", "e", "j", "s", "u", "U", "v", "V"),
               _contextual(convergent_matrix_state_at_relation),
               "A real beta history entry at j contains the actual coded quotient suffix and matrix state.",
               ("ConvergentMatrixCode", "BetaAt")),
    _construct(204, "ConvergentMatrixTrace", ("s", "h", "e", "k", "u", "U", "v", "V"),
               _contextual(convergent_matrix_trace_relation),
               "An actual length-k quotient-matrix computation begins at the identity and prepends genuine quotient cells. No determinant or error conclusion is hidden in the trace.",
               ("ConvergentMatrixAt", "Lt", "ListCell")),
    _construct(205, "Convergent", ("s", "i", "u", "v"), _contextual(convergent_relation),
               "The actual (i+1)-step quotient-matrix output with v>0 and natural u, including u=0. The old planning-only restriction u>0 was incorrect for initial 0/1.",
               ("ConvergentMatrixTrace",)),
    _construct(206, "BestApproximationSecondKind", ("a", "b", "u", "v"),
               lambda *values, tag: best_approximation_second_kind_relation(*values, tag=tag, variables=tuple(values)),
               "Every natural numerator and strictly smaller positive denominator has cross-product error at least that of u/v. Both absolute errors are actual witnesses.",
               ("NaturalAbsDifference", "Lt", "Le")),
    _construct(207, "SignedBestApproximationSecondKind", ("a", "b", "u", "v"),
               lambda *values, tag: best_approximation_second_kind_relation(*values, tag=tag, variables=tuple(values), signed=True),
               "The same second-kind comparison for every signed numerator rp−rn and every 0<t<v; it includes the natural comparison as a corollary.",
               ("NaturalAbsDifference", "Lt", "Le")),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 233 or len(_identifiers) != 233:
    raise ValueError("the immutable Alpha-v28 definition registry changed")
if tuple(item.stable_id for item in PRIORITY_LAYER_DEFINITIONS) != tuple(f"ND{index:04d}" for index in range(177, 208)):
    raise ValueError("priority-layer definition identifiers changed")
for item in PRIORITY_LAYER_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("a priority-layer definition overwrites a historical identity")
    if len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies)) or not set(item.conceptual_dependencies) <= _known.keys():
        raise ValueError("priority-layer definitions have repeated, forward, or missing dependency edges")
    _known[item.name] = item
    _identifiers.add(item.stable_id)

PRIORITY_LAYER_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType({item.name: item for item in PRIORITY_LAYER_DEFINITIONS})
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_known)
PRIORITY_LAYER_REGISTRIES = (
    ("prime-valuation-support", PRIORITY_LAYER_DEFINITIONS[:5]),
    ("totient-products", PRIORITY_LAYER_DEFINITIONS[5:11]),
    ("squarefree-kernels", PRIORITY_LAYER_DEFINITIONS[11:19]),
    ("exponent-lifting", PRIORITY_LAYER_DEFINITIONS[19:22]),
    ("best-approximation", PRIORITY_LAYER_DEFINITIONS[22:]),
)


def definition_closure(names: tuple[str, ...]) -> tuple[DefinitionSpec, ...]:
    """Only relevant notation and its exact, acyclic prerequisite objects."""
    ordered: list[DefinitionSpec] = []
    visited: set[str] = set()
    active: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError(f"unknown or cyclic priority-layer notation {name!r}")
        active.add(name)
        definition = ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]
        for dependency in definition.conceptual_dependencies:
            visit(dependency)
        active.remove(name)
        visited.add(name)
        ordered.append(definition)

    for name in names:
        visit(name)
    return tuple(ordered)


__all__ = (
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME", "PRIORITY_LAYER_DEFINITIONS",
    "PRIORITY_LAYER_DEFINITIONS_BY_NAME", "PRIORITY_LAYER_REGISTRIES", "definition_closure",
)
