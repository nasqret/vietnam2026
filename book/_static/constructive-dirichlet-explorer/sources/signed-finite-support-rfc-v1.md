# Actual finite signed support and zero padding

This additive, non-admitting checkpoint supplies the finite-support bridge
needed by actual Dirichlet convolution. Its immutable basis is Alpha v30
(3,222 checked-use theorems, Stable 432), 170 and 126 published research
theorems, and the preceding 125 local research theorems: 3,643 prior rows.
None of those sources, proof limits, kernel rules or membership records changes.

## Conservative definition

The sole new graph has exactly three arguments:

```text
SignedZeroWindow(F,k,l) :=
  ∀i z. Le(k,i) → Lt(i,l) → ArithAt(F,i,z) → z=0.
```

It states actual represented entry values on the half-open interval `k≤i<l`.
It contains no sum identity, table-code equality or finite-choice assumption.
The public builder is `signed_arithmetic_zero_window_relation(F,k,l,*,tag,variables)`.
It checks every generated binder against the entire explicit variable context,
including unused context variables; compound terms and double-and-add numerals
are permitted. All existing definition identities remain unchanged.

The genuine definition dependencies are `Le`, `Lt`, and `ArithAt`. Sum laws
are theorem dependencies, not expansion edges from this graph.

## Principal theorems

```text
∀F k l a b. Le(k,l) → SignedZeroWindow(F,k,l) →
  SignedPrefixSum(F,k,a) → SignedPrefixSum(F,l,b) → a=b.

∀F l a z. SignedZeroWindow(F,0,l) → ArithAt(F,l,a) →
  SignedPrefixSum(F,S l,z) → z=a.

∀F k l z. ArithTable(0,F) → Le(k,l) → SignedZeroWindow(F,k,l) →
  (SignedPrefixSum(F,k,z) → SignedPrefixSum(F,l,z)) ∧
  (SignedPrefixSum(F,l,z) → SignedPrefixSum(F,k,z)).
```

The first proof inducts on the longer fold. At each successor it decomposes
the actual sum, identifies its actual last entry with zero and uses the
previous signed-addition law. The last-entry theorem similarly retains the
real predecessor sum and table lookup. Both padding directions construct
the missing genuine fold before identifying its canonical signed value.
The zero-length and equal-endpoint cases are included. A reversed empty
window does not justify equal sums: the explicit order hypothesis is essential.

## Verification boundary

The factory `make_signed_finite_support_candidate_theorems` contains eight
new rows, 25 direct prerequisite edges and 312 tactic commands. All eight
dependency-curried bodies pass the unchanged original HA kernel. Their total
node count is 528; the maximum is 177 nodes and depth 39. This authoring result
is not, on its own, proof that inherited prerequisites are closed.

All 113 distinct focused tests pass in separate bounded windows. They check
all eight bodies and false targets, drop and poison every declared dependency,
independently expand all eight statements and the public graph, reject binder
capture and malformed contexts, and construct actual beta-coded signed tables
and both cumulative sum traces. Examples cover negative values, zero lengths,
arbitrary unused endpoints and genuinely different component encodings.
Observed maxima were 407,453,696 bytes RSS and 48.61 seconds per test window.
Numerical examples are diagnostics, never proof authority.

Complete dependency-bundle verification, unchanged compiled-Lean verification,
ordinary empty-context root checks and exact novelty against every prior row
are separate gates. They must all succeed before a proof explorer may display
this family as independently verified. No Alpha/Stable admission or remote
deployment is performed by this mathematical checkpoint.
