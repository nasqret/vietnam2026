"""Conservative notation for actual signed Dirichlet arithmetic.

All 356 inherited identities are unchanged. New graphs describe represented
values, real finite tables and folds, not the algebraic laws proved about
them. Definitions and their expansion arrows grant no theorem authority,
Alpha membership, publication status, or broader G009/G091 milestone claim.
"""

from collections.abc import Mapping
from types import MappingProxyType

from constructive_lower_continuation_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from constructive_bottom_layer_definitions import _contextual
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.library import signed_finite_support_candidate as finite
from peano_lab.library import dirichlet_convolution_candidate as convolution
from peano_lab.library import dirichlet_fubini_candidate as fubini
from peano_lab.library import dirichlet_units_candidate as units
from peano_lab.library import mobius_inversion_candidate as inversion


def _construct(identifier, name, parameters, builder, summary, dependencies):
    return _definition(
        stable_id=f"ND{identifier:04d}", name=name, parameters=parameters,
        template_source=_contextual(builder)(*parameters,tag="dirichlet"),
        summary=summary, category="constructive_dirichlet", priority="P2",
        conceptual_dependencies=dependencies,
    )


DIRICHLET_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(300,"SignedZeroWindow",("F","k","l"),finite.signed_arithmetic_zero_window_relation,
        "Every actual signed lookup on the half-open interval k<=i<l has value zero. Table validity, existence of folds, and equality after padding are separate hypotheses or theorems, not part of this graph.",
        ("Le","Lt","ArithAt")),
    _construct(301,"DirichletEntry",("F","G","n","d","z"),convolution.dirichlet_convolution_entry_relation,
        "At a positive divisor d, witness n=d*q, read the actual signed values F(d) and G(q), and multiply them. Zero and nondivisors contribute canonical zero without reading either input at zero. Source-table validity is separate.",
        ("Dvd","ArithAt","SignedMul")),
    _construct(302,"DirichletPrefix",("F","G","n","l","M"),convolution.dirichlet_convolution_prefix_relation,
        "An actual signed table M records the independently defined convolution entry at every inclusive index 0<=d<=l. The endpoint l is included and can differ from n; no sum or convolution identity is assumed.",
        ("ArithTable","Le","ArithAt","DirichletEntry")),
    _construct(303,"DirichletSum",("F","G","n","z"),convolution.dirichlet_convolution_sum_relation,
        "Require n>0, construct a real convolution-summand prefix through n, and take its actual signed fold over exactly S n entries. Zero is outside this sum's input domain; no value is assigned by a unit or inversion formula.",
        ("DirichletPrefix","SignedPrefixSum")),
    _construct(304,"DirichletTable",("N","F","G","H"),convolution.dirichlet_convolution_table_relation,
        "Three actual finite signed tables whose output H(n), at every 0<n<=N, is the independently defined convolution sum of F and G. All zero entries are unrestricted; only represented positive values, not table codes, are subsequently proved unique.",
        ("ArithTable","Le","ArithAt","DirichletSum")),
    _construct(305,"DirichletGridEntry",("F","G","H","n","a","e","z"),fubini.signed_dirichlet_grid_entry_relation,
        "A retained cell has a!=0, e!=0, an actual middle factor n=(a*e)*c, and the two signed products F(a)*(H(e)*G(c)). Cells with a=0, e=0 or a*e not dividing n are zero. Positivity of n and source-table validity are separate guards.",
        ("Dvd","ArithAt","SignedMul")),
    _construct(306,"DirichletFlatEntry",("F","G","H","n","i","z"),fubini.signed_dirichlet_flat_entry_relation,
        "Witness genuine row-major quotient/remainder coordinates i=(S n)*a+e with e<S n, then require the corresponding actual factor-grid entry. This graph does not itself bound a by n or assume a rearrangement law.",
        ("Lt","DirichletGridEntry")),
    _construct(307,"DirichletFlatPrefix",("F","G","H","n","l","T"),fubini.signed_dirichlet_flat_prefix_relation,
        "An actual signed table stores each independently defined flat grid entry at every inclusive index i<=l. Its construction uses finite division and beta recoding; no supplied grid, sum, or Fubini conclusion is built into the graph.",
        ("ArithTable","Le","ArithAt","DirichletFlatEntry")),
    _construct(308,"DirichletGrid",("F","G","H","n","T"),fubini.signed_dirichlet_grid_table_relation,
        "The actual row-major (S n)-by-(S n) factor grid specifies cells a,e<=n at index (S n)*a+e. The underlying table separately certifies its unused endpoint (S n)*(S n). Construction from a flat prefix is a proof dependency, not an extra definition condition.",
        ("ArithTable","Le","ArithAt","DirichletGridEntry")),
    _construct(309,"DirichletFactorRow",("F","G","H","n","a","V"),fubini.signed_dirichlet_factor_row_relation,
        "An actual signed row V records the factor cells for fixed a at every e<=n. Its separately valid endpoint S n is unused. No bound a<=n, scalar-sum identity, or associativity law is included as an assumption.",
        ("ArithTable","Le","ArithAt","DirichletGridEntry")),
    _construct(310,"ConstantOneTable",("N","U"),units.dirichlet_constant_one_table_relation,
        "An actual signed table has canonical one, code 2, at every 0<n<=N. Its value at zero is unrestricted, including when N=0. Existence with any prescribed zero entry and the divisor-sum identity are separately proved.",
        ("ArithTable","Le","ArithAt")),
    _construct(311,"KroneckerDeltaTable",("N","E"),units.dirichlet_kronecker_delta_table_relation,
        "An actual signed table has code 2 at n=1 and code 0 at all other positive n<=N. Its zero entry is unrestricted and N=0 has an empty positive domain. Both convolution unit laws are theorems, not definition premises.",
        ("ArithTable","Le","ArithAt")),
    _construct(312,"DivisorTransform",("N","F","G"),inversion.signed_arithmetic_divisor_transform_relation,
        "Every actual positive output G(n), for n<=N, is the separately defined signed divisor sum of F. Table validity is a separate prerequisite and both zero entries are unrestricted. No Möbius values or inversion conclusion appear in the graph.",
        ("Le","ArithAt","DivisorSum")),
)


_known=dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers={item.stable_id for item in _known.values()}
if len(_known)!=356 or len(_identifiers)!=356:
    raise ValueError("the frozen 356-definition registry changed")
if tuple(item.stable_id for item in DIRICHLET_DEFINITIONS)!=tuple(f"ND{i:04d}" for i in range(300,313)):
    raise ValueError("Dirichlet definition identifier order changed")
for item in DIRICHLET_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("Dirichlet notation shadows an inherited identity")
    if (len(item.conceptual_dependencies)!=len(set(item.conceptual_dependencies))
            or not set(item.conceptual_dependencies)<=_known.keys()):
        raise ValueError("repeated, forward or missing Dirichlet definition dependency")
    _known[item.name]=item
    _identifiers.add(item.stable_id)

ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str,DefinitionSpec]=MappingProxyType(_known)
DIRICHLET_REGISTRIES=(
    ("finite-support",DIRICHLET_DEFINITIONS[:1]),
    ("dirichlet-convolution",DIRICHLET_DEFINITIONS[1:5]),
    ("dirichlet-fubini",DIRICHLET_DEFINITIONS[5:10]),
    ("dirichlet-units",DIRICHLET_DEFINITIONS[10:12]),
    ("mobius-inversion",DIRICHLET_DEFINITIONS[12:]),
)


def definition_closure(names: tuple[str,...]) -> tuple[DefinitionSpec,...]:
    """Return only actual transitive expansion prerequisites in stable order."""
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise ValueError("definition names must be an exact tuple of nonempty text")
    ordered,visited,active=[],set(),set()

    def visit(name):
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError("unknown or cyclic Dirichlet notation: "+name)
        active.add(name)
        item=ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]
        for dependency in item.conceptual_dependencies:
            visit(dependency)
        active.remove(name)
        visited.add(name)
        ordered.append(item)

    for name in names:
        visit(name)
    return tuple(ordered)


__all__=("DIRICHLET_DEFINITIONS","DIRICHLET_REGISTRIES",
         "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME","definition_closure")
