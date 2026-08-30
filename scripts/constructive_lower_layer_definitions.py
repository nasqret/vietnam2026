"""Additive, hygienic notation for the lower-layer constructive campaign.

Historical reviewed objects and IDs are reused unchanged. The canonical
integer decoder is the original parity encoding, shared by the two quadratic
integer rings. This registry supplies notation only, never proof authority.
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

from constructive_second_wave_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.library.finite_permutation_theorems import permutation_prefix
from peano_lab.library.foundation_saturation_candidate import prime_factor_list_relation
from peano_lab.library.ha_signed_add_candidate import signed_add
from peano_lab.library.ha_signed_balance_candidate import signed_balance
from peano_lab.library.ha_signed_bezout_candidate import signed_bezout
from peano_lab.library.ha_signed_decode_candidate import signed_decode
from peano_lab.library.ha_signed_mul_candidate import signed_mul
from peano_lab.library.ha_signed_negate_candidate import signed_negate
from peano_lab.library.prime_factorization_permutation_candidate import (
    factor_list_matching_relation, prime_factor_list_permutation_relation,
)
from peano_lab.library.prime_enumeration_candidate import (
    initial_prime_chain_relation, next_prime_relation, prime_list_relation,
)
from peano_lab.library.signed_integer_division_candidate import (
    signed_code_floor_relation, signed_integer_floor_relation,
)
from peano_lab.library.gaussian_euclidean_candidate import (
    gaussian_add_relation, gaussian_division_remainder_relation,
    gaussian_euclidean_division_relation, gaussian_multiply_relation,
    gaussian_norm_relation,
    gaussian_decode_relation, gaussian_integer_relation,
    gaussian_representation_relation, gaussian_rounded_signed_division_relation,
    gaussian_signed_division_remainder_relation, gaussian_signed_norm_relation,
    signed_difference_square_relation,
)
from peano_lab.library.eisenstein_euclidean_candidate import (
    eisenstein_coordinate_norm_relation, eisenstein_coordinate_product_relation,
    eisenstein_division_remainder_relation, eisenstein_euclidean_division_relation,
    eisenstein_multiply_relation, eisenstein_norm_relation,
    eisenstein_signed_division_remainder_relation, _weighted as _weighted_norm_three,
)


def _construct(identifier: int, name: str, parameters: tuple[str, ...], builder: Callable[..., str], summary: str, dependencies: tuple[str, ...] = ()) -> DefinitionSpec:
    return _definition(
        stable_id=f"ND{identifier:04d}", name=name, parameters=parameters,
        template_source=builder(*parameters, tag="lowerlayer"), summary=summary,
        category="constructive_lower_layer", priority="P2", conceptual_dependencies=dependencies,
    )


LOWER_LAYER_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(142, "SignedDecode", ("z", "p", "n"), signed_decode,
               "The original canonical integer code: even 2p denotes p, and odd 2k+1 denotes −(k+1). The decoded positive and negative parts are normalized."),
    _construct(143, "SignedBalance", ("z", "p", "n"), signed_balance,
               "The original canonical code z represents the integer difference p−n; these supplied components need not be normalized.", ("SignedDecode",)),
    _construct(144, "SignedAdd", ("a", "b", "c"), signed_add,
               "Actual addition of original canonical signed codes, witnessed by their decoders and balanced equality.", ("SignedDecode",)),
    _construct(145, "SignedMul", ("a", "b", "c"), signed_mul,
               "Actual multiplication of original canonical signed codes; opposite-sign products remain on the negative side of the balance.", ("SignedDecode",)),
    _construct(146, "SignedNegate", ("a", "b"), signed_negate,
               "Canonical signed negation swaps the positive and negative decoded parts.", ("SignedDecode",)),
    _construct(147, "SignedBezout", ("g", "a", "b", "u", "v"), signed_bezout,
               "The original signed coefficient codes u and v witness a·u+b·v=g by actual decoded balanced arithmetic.", ("SignedDecode",)),
    _construct(148, "PermutationPrefix", ("b", "c", "l"), permutation_prefix,
               "An actual beta-coded bijection of the finite index interval [0,l), including all bounds, injectivity, and surjectivity.", ("BoundedPrefix", "InjectivePrefix", "SurjectivePrefix")),
    _construct(149, "PrimeFactorList", ("n", "b", "c", "l"), prime_factor_list_relation,
               "A positive number n, an actual length-l beta product equal to n, and prime entries. No sortedness or supplied canonicalization is required.", ("Product", "AllPrime")),
    _construct(150, "FactorListMatching", ("b", "c", "d", "e", "u", "v", "l"), factor_list_matching_relation,
               "Each actual source factor equals the factor at the index decoded from its image under the witnessed map.", ("Lt", "BetaAt")),
    _construct(151, "PrimeFactorListPermutation", ("b", "c", "l", "d", "e", "m", "u", "v"), prime_factor_list_permutation_relation,
               "Equal list lengths and an actual bounded, injective, surjective beta index map matching all source and target prime occurrences, including repetitions.", ("PermutationPrefix", "FactorListMatching")),
    _construct(152, "NextPrime", ("a", "p"), next_prime_relation,
               "The actual least prime strictly above a. Global minimality excludes a sparse subsequence of primes.", ("Prime", "Lt", "Le")),
    _construct(153, "InitialPrimeChain", ("b", "c", "k"), initial_prime_chain_relation,
               "A beta code starting at two and containing k actual least-prime transitions, hence k+1 consecutive primes.", ("BetaAt", "Lt", "NextPrime")),
    _construct(154, "InitialPrimeList", ("b", "c", "k"), prime_list_relation,
               "Exactly the first k primes in increasing order, omitting no smaller prime; k=0 is the genuine empty list.", ("InitialPrimeChain",)),
    _construct(155, "SignedFloor", ("p", "n", "m", "q", "t", "r"),
               lambda *values, tag: signed_integer_floor_relation(*values, tag=tag, variables=tuple(values)),
               "The genuine signed floor equation (p−n)=m·(q−t)+r and strict natural remainder bound r<m.", ("Lt",)),
    _construct(156, "SignedCodeFloor", ("a", "m", "q", "r"), signed_code_floor_relation,
               "Actual canonical signed input and quotient codes satisfy the very same floor equation with remainder r<m.", ("SignedDecode", "SignedFloor")),
    _construct(157, "SignedDifferenceSquare", ("p", "n", "s"),
               lambda *values, tag: signed_difference_square_relation(*values),
               "The natural value s of the integer square (p−n)², expressed as a subtraction-free balanced equality."),
    _construct(158, "GaussianSignedNorm", ("ap", "an", "bp", "bn", "N"), gaussian_signed_norm_relation,
               "The actual sum (ap−an)²+(bp−bn)² of two witnessed signed-coordinate squares.", ("SignedDifferenceSquare",)),
    _construct(159, "ZPairDecode", ("z", "ap", "an", "bp", "bn"), gaussian_decode_relation,
               "The shared injective code of two original canonical signed integers, with their normalized coordinate decoders. Both quadratic integer rings use this same carrier.", ("SignedDecode",)),
    _construct(160, "ZPairValid", ("z",), gaussian_integer_relation,
               "The natural z actually encodes a pair of signed integers; not every natural is assumed to be a valid pair code.", ("ZPairDecode",)),
    _construct(161, "ZPairRep", ("z", "ap", "an", "bp", "bn"), gaussian_representation_relation,
               "The shared pair code represents the two supplied signed differences, with arbitrary nonnormalized representatives allowed.", ("SignedBalance",)),
    _construct(162, "RoundedSignedDivision", ("p", "n", "N", "qp", "qn", "ep", "en", "t"), gaussian_rounded_signed_division_relation,
               "A genuine signed quotient and signed error represent p−n=N·(qp−qn)+(ep−en), with absolute error t and 2t≤N.", ("SignedDifferenceSquare", "Le")),
    _construct(163, "GaussianSignedDivisionRemainder", ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn", "qp", "qn", "up", "un", "rp", "rn", "sp", "sn", "U", "V"), gaussian_signed_division_remainder_relation,
               "The actual Gaussian coordinate equation A=B·Q+R, the two genuine squared norms U=N(R), V=N(B), and strict decrease U<V.", ("GaussianSignedNorm", "Lt")),
    _construct(164, "GNorm", ("z", "n"), gaussian_norm_relation,
               "The actual norm a²+b² of the shared canonical pair code representing the Gaussian integer a+bi.", ("ZPairRep", "GaussianSignedNorm")),
    _construct(165, "ZPairAdd", ("a", "b", "c"), gaussian_add_relation,
               "Actual coordinatewise integer addition in the shared signed-pair carrier. Both quadratic integer rings use this identical additive relation.", ("ZPairRep",)),
    _construct(166, "GMul", ("a", "b", "c"), gaussian_multiply_relation,
               "Actual Gaussian multiplication: (a+bi)(c+di)=(ac−bd)+(ad+bc)i, with canonical pair-code outputs.", ("ZPairRep",)),
    _construct(167, "GDivRem", ("a", "b", "q", "r"), gaussian_division_remainder_relation,
               "The exact canonical-code equation a=bq+r, using an actual Gaussian product code and the shared addition graph. No norm bound is included here.", ("GMul", "ZPairAdd")),
    _construct(168, "GEuclideanDivision", ("a", "b", "q", "r", "U", "V"), gaussian_euclidean_division_relation,
               "Valid quotient and remainder codes satisfy the genuine Gaussian equation a=bq+r and have actual norms U=N(r), V=N(b) with U<V.", ("ZPairValid", "GDivRem", "GNorm", "Lt")),
    _construct(169, "EisensteinCoordinateNorm", ("ap", "an", "bp", "bn", "n"),
               lambda *values, tag: eisenstein_coordinate_norm_relation(*values, tag=tag, variables=tuple(values)),
               "The genuine Eisenstein coordinate norm (ap−an)²−(ap−an)(bp−bn)+(bp−bn)², as a balanced natural equation."),
    _construct(170, "EisensteinCoordinateProduct", ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn", "rp", "rn", "sp", "sn"),
               lambda *values, tag: eisenstein_coordinate_product_relation(*values, tag=tag, variables=tuple(values)),
               "The actual signed-coordinate product (a+bω)(c+dω)=(ac−bd)+(ad+bc−bd)ω, where ω²+ω+1=0; this is not Gaussian multiplication."),
    _construct(171, "ENorm", ("z", "n"),
               lambda *values, tag: eisenstein_norm_relation(*values, tag=tag, variables=tuple(values)),
               "The actual norm a²−ab+b² of the shared canonical pair code representing the Eisenstein integer a+bω.", ("ZPairRep", "EisensteinCoordinateNorm")),
    _construct(172, "EMul", ("a", "b", "c"),
               lambda *values, tag: eisenstein_multiply_relation(*values, tag=tag, variables=tuple(values)),
               "Actual multiplication in the Eisenstein ring, using the shared signed-pair carrier and the law ω²+ω+1=0.", ("ZPairRep",)),
    _construct(173, "EDivRem", ("a", "b", "q", "r"),
               lambda *values, tag: eisenstein_division_remainder_relation(*values, tag=tag, variables=tuple(values)),
               "The genuine canonical Eisenstein equation a=bq+r, witnessed by the Eisenstein multiplication graph and the very same shared pair addition as for Gaussian integers.", ("EMul", "ZPairAdd")),
    _construct(174, "EEuclideanDivision", ("a", "b", "q", "r", "U", "V"),
               lambda *values, tag: eisenstein_euclidean_division_relation(*values, tag=tag, variables=tuple(values)),
               "Actual Eisenstein quotient and remainder codes satisfy a=bq+r and have genuine norms U=N(r), V=N(b) with strict decrease U<V. The norm and operation witnesses imply valid pair codes.", ("EDivRem", "ENorm", "Lt")),
    _construct(175, "WeightedSignedNormThree", ("ap", "an", "bp", "bn", "n"),
               lambda *values, tag: _weighted_norm_three(*values, tag),
               "The witnessed sum (ap−an)²+3(bp−bn)². It supports the proved identity 4N(a+bω)=(2a−b)²+3b², not a new norm axiom.", ("SignedDifferenceSquare",)),
    _construct(176, "EisensteinSignedDivisionRemainder", ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn", "qp", "qn", "up", "un", "rp", "rn", "sp", "sn", "U", "V"),
               lambda *values, tag: eisenstein_signed_division_remainder_relation(*values, tag=tag, variables=tuple(values)),
               "The genuine signed-coordinate Eisenstein equation A=B·Q+R, actual coordinate norms U=N(R), V=N(B), and strict decrease U<V.", ("EisensteinCoordinateNorm", "Lt")),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 198 or len(_identifiers) != 198:
    raise ValueError("the immutable Alpha-v27 definition registry changed")
if tuple(item.stable_id for item in LOWER_LAYER_DEFINITIONS) != tuple(f"ND{index:04d}" for index in range(142, 177)):
    raise ValueError("lower-layer definition identifiers changed")
for item in LOWER_LAYER_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("a lower-layer definition overwrites a historical identity")
    if len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies)) or not set(item.conceptual_dependencies) <= _known.keys():
        raise ValueError("lower-layer definitions have repeated, forward, or missing dependency edges")
    _known[item.name] = item
    _identifiers.add(item.stable_id)

LOWER_LAYER_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType({item.name: item for item in LOWER_LAYER_DEFINITIONS})
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_known)
LOWER_LAYER_REGISTRIES = (
    ("arithmetic-foundations", LOWER_LAYER_DEFINITIONS[:10]),
    ("prime-enumeration", LOWER_LAYER_DEFINITIONS[10:13]),
    ("gaussian-integers", LOWER_LAYER_DEFINITIONS[13:27]),
    ("eisenstein-integers", LOWER_LAYER_DEFINITIONS[27:]),
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
            raise ValueError(f"unknown or cyclic lower-layer notation {name!r}")
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
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME", "LOWER_LAYER_DEFINITIONS",
    "LOWER_LAYER_DEFINITIONS_BY_NAME", "LOWER_LAYER_REGISTRIES", "definition_closure",
)
