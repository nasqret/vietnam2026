# Recursive normalized polynomial gcd and Bézout

Continue from the verified 95-row working checkpoint without modifying it.
Its complete artifact is `454f23a30acfb9188d7458a9dc206ce9fc14a61510d0c3b548a611a9d682af56`;
its final verification binding is
`005eeadb5fe1798f531940bac31c9ae60d9346619459814b998500cb958b2449`.
This turn implements proofs locally; it does not commit, promote, push, deploy,
change catalogue capacity, or change the kernel or resource limits.

## Contracts

All statements use actual natural-number triples `(code, scale, length)`, a
prime modulus, canonical coefficient prefixes, and all-power formal polynomial
equivalence. Right divisibility is the existing actual left-quotient relation.

- `Normal(p,G)` is `Glen=0` or the existing `FpMonic(p,G)`.
- `RightGcd(p,G,A,B)` is `CommonRightDivisor(p,G,A,B)` together with
  `forall D. CommonRightDivisor(p,D,A,B) -> RightDivides(p,D,G)`.
- `NormalizedGcd(p,G,A,B)` is `Normal(p,G)` and `RightGcd(p,G,A,B)`.

The public existence theorem must construct actual `G,U,V` with
`Normal(G)`, `RightGcd(G,A,B)`, and the existing witnessed
`Bezout(A,B,G,U,V)`. Uniqueness concerns formal equivalence of the normalized
gcd; neither beta encodings nor Bézout coefficients are asserted unique.

## Construction

For fixed prime `p`, induct on a bound `n`, quantifying **both** polynomial
triples inside the induction predicate. The predicate constructs `G,U,V`
with `Normal(G)`, `CommonRightDivisor(G,A,B)`, and `Bezout(A,B,G,U,V)` whenever
both inputs are canonical and `Blen <= n`.

Normalize the first input at the terminal step and keep that same `G` while
transporting witnesses backward. This is equivalent to normalizing after
recursion, but avoids changing the result during back-substitution.

1. With empty second input, construct a zero-or-monic mutual right associate
   of `A`. Its actual right-multiple witness gives the first Bézout coefficient;
   an empty second coefficient gives a genuine zero product. This includes
   `(0,0)` and all-zero first inputs.
2. Trim the second input to a formally equivalent canonical `T`. If its
   retained length is zero, use the terminal constructor and transport back
   to the original second representation, including stored leading zeros.
3. Otherwise obtain `Tlen=S d`, divide `A` by `T`, and construct an actual
   remainder of length at most `d`. From `Tlen<=Blen<=S n`, derive `d<=n`.
4. Apply the quantified induction hypothesis to `(T,R)`. The already-proved
   common-divisor and Bézout backward maps give the witnesses for `(A,T)`;
   formal-equivalence transport replaces `T` by the original `B`.
5. A separate linear-combination lemma proves greatestness: every common
   right divisor divides each actual product and their aligned sum.
6. Prove that zero-or-monic mutually dividing polynomials are formally
   equivalent. For nonzero inputs, trim the actual quotient, use genuine
   product-degree and leading-coefficient laws, and force its degree to zero
   and coefficient to one. Handle zero branches without assigning degree zero
   to the zero polynomial.

## Work and verification

New sources are separate from the frozen checkpoints: gcd Bézout laws,
recursive existence, uniqueness, conservative notation, and final integration.
Focused tests target mathematical contracts, real coefficient/beta models,
counterexamples, binder hygiene, and corrupted proofs. Existing verification
infrastructure is reused; configuration repetition is not additional coverage.

Only one heavy proof/Alpha/Lean worker runs at a time. Original bounds remain
CPU 170/175 seconds, wall 180 seconds, RSS 1,536 MiB, and live depth 256.
Conditional native checks do not establish closed proof or admission. Final
acceptance requires actual dependency-complete original HA, the same
authenticated bytes in the independent compiled Lean checker, ordinary
empty-context principal proofs, and current-Alpha exact-AST novelty.

The new vocabulary is ND0348 `FpPolynomialZeroOrMonic`, ND0349
`FpPolynomialRightGcd`, and ND0350 `FpPolynomialNormalizedGcd`. All 404
predecessor definitions and their 879 expansion arrows are preserved; the
new conservative registry has 407 definitions and 884 expansion arrows.
The final existence conclusion groups `NormalizedGcd` and `Bezout` literally,
so both abbreviations can appear directly in its readable statement.

This work does not close grand-campaign G091. Its actual contract is
`Prime(p) /\ k>0 -> exists F. FiniteFieldCode(F,p^k)`; polynomial gcd and
Bézout are prerequisites, not an arbitrary-degree irreducibility construction
or an encoded extension field with the proved carrier size.

Status: complete as a verified local working checkpoint. All 24 new theorems
(four Bézout laws, nine recursion/greatestness rows, eleven uniqueness rows)
are included in the actual 119-row dependency-complete bundle. Its 493 proof
nodes, 1,578 edges and 47,545 body nodes passed original HA and the independent
compiled Lean checker on identical authenticated bytes. All 14 ordinary
empty-context principal proofs passed, including 56,067 nodes for normalized
existence, 24,581 for normalized uniqueness and 36,635 for greatestness.

All ten authoring stages and all 16 final gates passed on their first actual
runs, with original kernel, compiler, codec, fuel and resource limits intact.
The 938 distinct focused cases comprise 320 Bézout-law, 86 existence, 415
uniqueness and 117 notation/control cases; the final repeat of the 117 guards
is not counted twice. Earlier rejected development attempts remain preserved.
The full source map has 492 theorem nodes, 407 conservative definitions and
no unresolved dependencies.

Final bundle SHA-256:
`3fe18ad2899cff7db5fbe19df8570ef70b1bfb902171d5212e9b036dda660a46`.
All final gates share the source binding
`ea10c4b28b0a0ebaf55616bfa291f93011322764349c6ad8eccbc11ad2582c1d`.
The prior 95-row checkpoint and its authority remain unchanged. See the
[completed checkpoint](../research/arithmetic-library/working/prime-field-gcd-closure-v1/README.md)
for exact artifacts, commands and evidence. No commit, admission, push or
deployment was performed; full G091 remains open.
