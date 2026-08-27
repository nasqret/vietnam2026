# Actual unrestricted-dimensional signed determinant recursion

Status: the 44 additive determinant candidate bodies are implemented and
checked individually by the unchanged original kernel, over immutable Alpha
v26. This document is not an Alpha admission or dependency-closure receipt.
No rank, lattice-basis, Smith/Hermite normal form, or LLL theorem is claimed
by these determinant proofs alone.

## Audited target boundary

T13's blueprint sentence asks for checked finite entries, products, and
determinants but still contains informal `IntMatrix` and certificate prose.
The accompanying plan additionally promises rank and lattice tools. Its 79
historical checked components include actual arbitrary signed minors and
alternating folds, but the supplied cofactor values in those folds are not
assumed to be determinants.

The new determinant interface has seven natural arguments:

`SignedRecursiveDeterminant(pb,pc,nb,nc,d,p,n)`.

The four input code parameters describe the positive and negative entry
components of an arbitrary `d × d` beta-coded matrix. The outputs are the
exact subtraction-free positive and negative cofactor components. The empty
matrix evaluates to `(1,0)`. No dimension bound occurs in this relation.

## Conservative definition DAG

Every node uses only zero, successor, addition, multiplication, equality, and
first-order intuitionistic logical operators. There is no recursive predicate
or evaluator installed in the kernel.

1. A seven-field node code uses the existing injective doubled-Cantor pairing.
   Five existentially quantified intermediate code values share the six
   pair-constructor equations; large nested pairing polynomials are not
   repeated in the history formula.
2. A node record decodes one actual beta entry and all seven fields: dimension,
   four signed-matrix code parameters, and two signed determinant components.
3. A cofactor-child prefix contains, for every selected column, an actual
   signed first-row minor and a strictly earlier record evaluating that minor
   in dimension one smaller. Two beta streams contain those actual results.
4. A local evaluation is either the exact empty determinant or the checked
   parity-correct alternating fold over the complete child prefix and the
   actual first-row matrix entries.
5. A history validates every record of its finite beta prefix against that
   local rule. A determinant is an actual root record in such a history.

Strict earlier-node bounds rule out cycles. The dimension equation and the
complete actual-minor relation rule out supplied, unrelated cofactor values.
Notation and definition dependencies do not constitute theorem evidence.

## Construction proof

The dimension induction is deliberately strengthened: any valid existing
history can be extended by evaluating any matrix of the given dimension.
The zero case appends `(1,0)`. In the successor case, a separate finite-prefix
induction constructs every genuine cofactor minor, applies the smaller
dimension induction hypothesis to append its evaluation to the shared
history, and appends its two actual output values to the cofactor streams.
The checked alternating fold then computes and appends the parent root.

The conditional recursion-step lemmas are intermediate induction statements,
not public unconditional determinant claims. The unrestricted root discharges
their hypotheses with ordinary object-level HA induction.

## Actual functionality and recursive equations

The second candidate factory proves equality of the positive and negative
outputs for any pointwise-equal finite input codes. It first proves that the
genuine cofactor-minor matrices agree entry by entry, and then uses dimension
induction to identify their actual determinant values. The final theorem
therefore has no supplied cofactor-functionality premise.

The successor cofactor equation is an equivalence, in both directions,
between an actual determinant history and a parity-correct fold of genuinely
evaluated minors. The empty equation is exactly
`SignedRecursiveDeterminant(pb,pc,nb,nc,0,p,n) ↔ (p=1 ∧ n=0)`.
The third maximal root states that every matrix, in every natural dimension,
has exactly one pair of these subtraction-free cofactor components.

Exact component uniqueness concerns recodings with identical positive and
negative entries. It does not assert component equality for different
signed-pair representations of the same integer. In particular, these proofs
do not silently assert multilinearity, multiplicativity, or signed-quotient
representation invariance.

## Remaining rank and lattice boundaries

The agreed subsequent rank target is an actual rectangular rank witness
`r ≤ min(rows,cols)`, a nonzero `r`-minor (the empty determinant handles rank
zero), and vanishing of every `(r+1)`-minor, constructed by finite decidable
search. The lattice target is actual integer column-span witnesses with zero,
addition, and negation closure using decoded signed matrix-vector products.
Arbitrary generators are not called an independent lattice basis, and no
injectivity, index, Cramer, Smith/Hermite, or LLL consequence is inferred.

## Validation and resource policy

Authoring tests reconstruct exact historical `TheoremSpec` statements,
scripts, dependencies, and summaries from the immutable Alpha-v26 catalog to
avoid the approximately 700 MiB overhead of importing all historical edition
registries. They still execute every new tactic body through the unchanged
kernel. This bounded dependency-curried pass is explicitly not full closure;
final admission must reconstruct and independently check every dependency
body and every exact endpoint in a separate immutable bundle.

The two factories contain 24 construction and 20 extensionality/equation
rows, 104 direct declared dependencies, 2,611 tactic commands, and 5,732
candidate proof-body node occurrences (5,711 distinct proof objects). The
successor-decomposition body shares 21 objects. The largest body has 707 nodes; the largest
actual body depth is 90. Tests pin these structural metrics per body, exact
endpoint statements, the ordered name inventory, and reject false-conclusion
and missing-dependency mutations. These counts exclude every historical
dependency body and are not release-bundle counts.

The ordered candidate-name SHA-256 is
`06dd3bc157a99bd9a7aafac8208ea5daf82682d346160be137dc68878cb44aa9`.
The maximal roots are `signed_recursive_determinant_exists_unique`,
`signed_recursive_determinant_cofactor_equation`, and
`signed_recursive_determinant_empty_equation`; together their actual
dependency cones include all 44 new rows.

No frozen v26 sources, kernel rules, checker, edition, UI, website, deployment
recipe, or externally owned Hydra work is modified by this candidate layer.
