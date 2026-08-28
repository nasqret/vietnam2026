"""Additive conservative notation for the post-v30 bottom-layer proofs.

All 284 existing definition objects are retained literally.  In particular,
canonical prime-field reduction reuses ND0023 CanonicalModularResidue: it is
not a new mathematical concept or a second definition identity.

This registry supplies notation only, never proof or library membership.
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

from constructive_gaussian_factorization_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.library import euler_units_product_candidate as euler_product
from peano_lab.library import euler_units_residue_candidate as euler_residue
from peano_lab.library import mobius_value_candidate as mobius
from peano_lab.library import prime_field_arithmetic_candidate as field
from peano_lab.library import prime_field_tables_candidate as field_tables
from peano_lab.library import prime_field_finiteness_candidate as field_finiteness
from peano_lab.library import divisor_sum_table_candidate as signed_tables
from peano_lab.library import divisor_sum_reindex_candidate as signed_reindex


def _contextual(builder: Callable[..., str]) -> Callable[..., str]:
    def expand(*values: str, tag: str) -> str:
        return builder(*values, tag=tag, variables=tuple(values))
    return expand


def _construct(identifier: int, name: str, parameters: tuple[str, ...],
               builder: Callable[..., str], summary: str,
               dependencies: tuple[str, ...]) -> DefinitionSpec:
    return _definition(
        stable_id=f"ND{identifier:04d}", name=name, parameters=parameters,
        template_source=builder(*parameters, tag="bottomlayer"),
        summary=summary, category="constructive_bottom_layer", priority="P2",
        conceptual_dependencies=dependencies,
    )


BOTTOM_LAYER_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(228, "FpElement", ("p", "a"), _contextual(field.prime_field_carrier_relation),
               "A prime modulus and an actual canonical natural representative a<p. Field laws are proved separately.",
               ("Prime", "Lt")),
    _construct(229, "FpAdd", ("p", "a", "b", "c"), _contextual(field.prime_field_add_relation),
               "Bounded operands and the actual canonical residue of their natural sum. The old ND0023 residue graph is reused exactly.",
               ("Lt", "CanonicalModularResidue")),
    _construct(230, "FpMul", ("p", "a", "b", "c"), _contextual(field.prime_field_multiply_relation),
               "Bounded operands and the actual canonical residue of their natural product; no multiplication law is assumed.",
               ("Lt", "CanonicalModularResidue")),
    _construct(231, "FpNeg", ("p", "a", "b"), _contextual(field.prime_field_negate_relation),
               "An actual bounded additive inverse: FpAdd(p,a,b,0). Its existence and uniqueness are theorems.",
               ("FpAdd",)),
    _construct(232, "FpInv", ("p", "a", "b"), _contextual(field.prime_field_inverse_relation),
               "An explicitly nonzero input and an actual product equal to canonical one. This relation never declares zero invertible.",
               ("FpMul",)),
    _construct(233, "AlternatingSignedUnit", ("n", "z"), _contextual(mobius.alternating_signed_unit_relation),
               "The actual signed code of (-1)^n from parity: even exponents give code 2 (+1), odd exponents code 1 (-1).",
               ("Even", "Odd")),
    _construct(234, "HasPrimeSquareDivisor", ("n",), _contextual(mobius.has_prime_square_divisor_relation),
               "A genuine prime p and an actual quotient witness p*p dividing n. This is not an asserted factorization oracle.",
               ("Prime", "Dvd")),
    _construct(235, "FactorParitySign", ("n", "z"), _contextual(mobius.prime_factor_parity_sign_relation),
               "A genuine finite prime-factor list for n has a length whose alternating signed unit is z. Independence of the factor list is proved.",
               ("PrimeFactorList", "AlternatingSignedUnit")),
    _construct(236, "Mobius", ("n", "z"), _contextual(mobius.mobius_value_relation),
               "For positive n, an actual prime-square divisor gives signed zero; otherwise squarefreeness and real factor-count parity give the signed unit. No divisor-sum or inversion identity occurs here.",
               ("HasPrimeSquareDivisor", "Squarefree", "FactorParitySign")),
    _construct(237, "Unit", ("a", "m"), _contextual(euler_residue.modular_unit_relation),
               "Exactly m>1 with a witnessed inverse b<m and a*b congruent to one. Unlike the old UnitResidue range, this expresses genuine invertibility at composite moduli.",
               ("Lt", "ModEq")),
    _construct(238, "UnitMultiplierPrefix", ("a", "m", "b", "c", "l"), _contextual(euler_residue.unit_multiplier_prefix_relation),
               "At every index i<l, the actual beta entry is the canonical residue of a*i. A bijection is constructed by theorem, not assumed in this graph.",
               ("Lt", "BetaAt", "CanonicalModularResidue")),
    _construct(239, "UnitProductFactor", ("m", "i", "v"), _contextual(euler_product.unit_product_factor_relation),
               "The independently decided weighted factor is i when Coprime(i,m), and one otherwise. It contains neither Phi nor Euler's conclusion.",
               ("Coprime",)),
    _construct(240, "UnitProductPrefix", ("m", "b", "c", "l"), _contextual(euler_product.unit_product_prefix_relation),
               "Every actual beta entry in 0<=i<l satisfies UnitProductFactor at the same index. Product values are computed by the existing finite-product graph.",
               ("Lt", "BetaAt", "UnitProductFactor")),
    _construct(241, "UnitScaledPrefix", ("a", "m", "b", "c", "d", "e", "l"), _contextual(euler_product.unit_scaled_prefix_relation),
               "Two genuine beta prefixes are related by modular multiplication by a precisely at coprime indices, with the other factors unchanged.",
               ("Lt", "BetaAt", "Coprime", "ModEq")),
    _construct(242, "FpFieldLaws", ("p",), _contextual(field.prime_field_laws_relation),
               "The explicit conjunction of the actual canonical operations' field laws, including distinct zero/one and nonzero inverses. This is a proved conclusion, never an unproved constructor premise.",
               ("Lt", "FpAdd", "FpMul", "FpNeg", "FpInv")),
    _construct(243, "FpZeroExtendedInv", ("p", "a", "b"), _contextual(field_tables.prime_field_zero_extended_inverse_relation),
               "The bounded nonzero inverse graph with an explicit zero-to-zero table convention. Zero is not asserted to be invertible.",
               ("Lt", "FpInv")),
    _construct(244, "FpAddGridValue", ("p", "i", "v"), _contextual(field_tables.prime_field_add_grid_value_relation),
               "An actual addition value at the row-major index i=a*p+b, with bounded coordinates supplied by FpAdd.",
               ("FpAdd",)),
    _construct(245, "FpMulGridValue", ("p", "i", "v"), _contextual(field_tables.prime_field_multiply_grid_value_relation),
               "An actual multiplication value at the row-major index i=a*p+b; coordinate and value uniqueness are proved.",
               ("FpMul",)),
    _construct(246, "FpAddPrefix", ("p", "b", "c", "l"), _contextual(field_tables.prime_field_add_prefix_relation),
               "Every genuine beta entry below l gives the addition grid value at its actual index.",
               ("Lt", "BetaAt", "FpAddGridValue")),
    _construct(247, "FpMulPrefix", ("p", "b", "c", "l"), _contextual(field_tables.prime_field_multiply_prefix_relation),
               "Every genuine beta entry below l gives the multiplication grid value at its actual index.",
               ("Lt", "BetaAt", "FpMulGridValue")),
    _construct(248, "FpNegPrefix", ("p", "b", "c", "l"), _contextual(field_tables.prime_field_negate_prefix_relation),
               "The actual beta prefix records an additive inverse for each index below l.",
               ("Lt", "BetaAt", "FpNeg")),
    _construct(249, "FpInvPrefix", ("p", "b", "c", "l"), _contextual(field_tables.prime_field_inverse_prefix_relation),
               "The actual beta prefix records the zero-extended inverse function. The nonzero inverse laws are separate theorems.",
               ("Lt", "BetaAt", "FpZeroExtendedInv")),
    _construct(250, "FpOperationTables", ("p", "ab", "ac", "mb", "mc", "nb", "nc", "ib", "ic"),
               _contextual(field_tables.prime_field_operation_tables_relation),
               "Four constructed beta tables: p*p entries for addition and multiplication, and p entries for negation and zero-extended inversion. No field-law premise occurs in this graph.",
               ("FpAddPrefix", "FpMulPrefix", "FpNegPrefix", "FpInvPrefix")),
    _construct(251, "ArithTable", ("N", "F"), _contextual(signed_tables.signed_arithmetic_table_relation),
               "An actual packed signed table with canonical signed entries through index N, including index zero. It contains no divisor transform or inversion hypothesis.",
               ("MatrixMinorFourCode", "Le", "BetaAt", "SignedBalance")),
    _construct(252, "ArithAt", ("F", "i", "z"), _contextual(signed_tables.signed_arithmetic_table_entry_relation),
               "Two genuine beta entries of the packed table represent the unique canonical signed value z. Distinct component representations need not be equal.",
               ("MatrixMinorFourCode", "BetaAt", "SignedBalance")),
    _construct(253, "SignedPrefixSum", ("F", "l", "z"), _contextual(signed_tables.signed_arithmetic_prefix_sum_relation),
               "The signed balance of two actual natural finite sums, at exactly the indices 0<=i<l. Existence, uniqueness and representation independence are proved separately.",
               ("MatrixMinorFourCode", "Sum", "SignedBalance")),
    _construct(254, "ArithTableEqual", ("F", "G", "l"), _contextual(signed_tables.signed_arithmetic_table_equality_relation),
               "Pointwise equality of actual canonical signed lookups below l, not equality of table codes or their positive/negative components.",
               ("Lt", "ArithAt")),
    _construct(255, "FpCardinality", ("p", "b", "c"), _contextual(field_finiteness.prime_field_cardinality_relation),
               "The existing identity-selector beta graph together with explicit boundedness, injectivity and surjectivity onto all p canonical representatives. ND0141 is reused, not cloned.",
               ("IdentityMatrixSelector", "Lt", "BetaAt")),
    _construct(256, "FpUnitSteps", ("p", "b", "c", "n"), _contextual(field_finiteness.prime_field_unit_steps_relation),
               "Each consecutive pair of actual history entries is related by addition of the canonical one. No modular-residue invariant is assumed.",
               ("Lt", "BetaAt", "FpAdd")),
    _construct(257, "FpUnitTrace", ("p", "b", "c", "n", "r"), _contextual(field_finiteness.prime_field_unit_trace_relation),
               "An actual beta history starts at zero, performs n additions of one and terminates at r. The residue invariant is established by induction.",
               ("BetaAt", "FpUnitSteps")),
    _construct(258, "FpUnitMultiple", ("p", "n", "r"), _contextual(field_finiteness.prime_field_unit_multiple_relation),
               "Existence of a genuine n-step addition-of-one history with endpoint r; this is not a restatement of divisibility or characteristic.",
               ("FpUnitTrace",)),
    _construct(259, "FpCharacteristic", ("p",), _contextual(field_finiteness.prime_field_characteristic_relation),
               "An actual p-step sum of one returns to zero, and no positive shorter such sum does. Its validity at every prime is proved from the trace invariant.",
               ("FpUnitMultiple", "Lt")),
    _construct(260, "FpFiniteStructure", ("p", "ab", "ac", "mb", "mc", "nb", "nc", "ib", "ic", "eb", "ec"),
               _contextual(field_finiteness.prime_field_finite_structure_relation),
               "The constructed prime-order structure combines actual operation tables, a p-element bijection, proved field laws and exact characteristic. Its existence is a theorem; extension fields of order p^k remain a separate open goal.",
               ("FpOperationTables", "FpCardinality", "FpFieldLaws", "FpCharacteristic")),
    _construct(261, "ArithReindex", ("F", "G", "r", "s", "l"),
               _contextual(signed_reindex.signed_arithmetic_table_reindex_relation),
               "Actual beta-map lookup pulls each source signed value into the target table below l. Neither permutation bijectivity nor any sum identity is assumed in this graph.",
               ("Lt", "BetaAt", "ArithAt")),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 284 or len(_identifiers) != 284:
    raise ValueError("the immutable v30 reviewed definition registry changed")
if tuple(item.stable_id for item in BOTTOM_LAYER_DEFINITIONS) != tuple(f"ND{i:04d}" for i in range(228, 262)):
    raise ValueError("bottom-layer definition identifiers changed")
for item in BOTTOM_LAYER_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("a bottom-layer definition overwrites a historical identity")
    if (len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies))
            or not set(item.conceptual_dependencies) <= _known.keys()):
        raise ValueError("a bottom-layer definition has repeated, forward, or missing dependencies")
    _known[item.name] = item
    _identifiers.add(item.stable_id)


BOTTOM_LAYER_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(
    {item.name: item for item in BOTTOM_LAYER_DEFINITIONS}
)
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_known)
BOTTOM_LAYER_REGISTRIES = (
    ("prime-fields", tuple(item for item in BOTTOM_LAYER_DEFINITIONS if item.name.startswith("Fp"))),
    ("mobius-inversion", tuple(item for item in BOTTOM_LAYER_DEFINITIONS
                               if item.name in {"AlternatingSignedUnit", "HasPrimeSquareDivisor", "FactorParitySign", "Mobius"})),
    ("euler-units", tuple(item for item in BOTTOM_LAYER_DEFINITIONS if item.name.startswith("Unit"))),
    ("signed-arithmetic", tuple(item for item in BOTTOM_LAYER_DEFINITIONS
                                if item.name.startswith("Arith") or item.name == "SignedPrefixSum")),
)


def definition_closure(names: tuple[str, ...]) -> tuple[DefinitionSpec, ...]:
    """Only the exact requested notation and its actual acyclic ancestors."""
    ordered: list[DefinitionSpec] = []
    visited: set[str] = set()
    active: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError(f"unknown or cyclic bottom-layer notation {name!r}")
        active.add(name)
        item = ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]
        for dependency in item.conceptual_dependencies:
            visit(dependency)
        active.remove(name)
        visited.add(name)
        ordered.append(item)

    for name in names:
        visit(name)
    return tuple(ordered)


__all__ = (
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME", "BOTTOM_LAYER_DEFINITIONS",
    "BOTTOM_LAYER_DEFINITIONS_BY_NAME", "BOTTOM_LAYER_REGISTRIES", "definition_closure",
)
