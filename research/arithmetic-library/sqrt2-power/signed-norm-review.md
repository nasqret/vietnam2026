# SN001: signed quadratic-norm zero criterion

Source/mathematical review, 2026-09-19. This document is not a kernel receipt.
The exact execution evidence is in the
[fresh HA observation](observations/shared-wave-signed-norm-v1/report.json) and
[independent Lean report](observations/fresh-lean-signed-norm-v1/report.json).
Both checks passed on the same canonical certificate, SHA-256
`5685db9bdbe1ceb79e29a25dff767c519ccf424705a1e395dad5fcb3b01911de`:
206 bundle nodes and 40,402 ordinary body nodes. This does not close IR032
or irrationality.

## Exact statement

```text
forall ap an bp bn s t.
 ap*ap+an*an=s+(ap*an+an*ap) ->
 bp*bp+bn*bn=t+(bp*bn+bn*bp) ->
 s=(S(S 0))*t ->
 (ap=an /\ bp=bn)
```

Target AST SHA-256:
`c948aa0e7350e5c51c464721215573a489b0921c9d1a3263c9c5181f20164941`.
The first two premises are the existing ND0157 `SignedDifferenceSquare`.
Thus `s=(ap-an)^2`, `t=(bp-bn)^2`, with no assumption that the signed
representatives are normalized or nonnegative as integers.

## Constructive proof decomposition

1. Obtain natural absolute differences `x,y`. Their witnesses are the
   constructive disjunctions `ap=an+x or an=ap+x`, and similarly for `bp,bn,y`.
2. The absolute-square balance theorem gives
   `SignedDifferenceSquare(ap,an,x*x)` and its second-pair counterpart.
3. Functionality of signed squares gives `s=x*x` and `t=y*y`.
4. Substitute these equalities into `s=2*t`. Reassociate explicitly from
   `2*(y*y)` to `(2*y)*y`, the exact syntax expected by IR016.
5. Apply the checked natural twice-square theorem to obtain `x=y=0`.
6. In both orientations of each absolute-difference disjunction, substitution
   and `n+0=n` give equality of the two components.

The actual old proof bodies are nodes 655, 641 and 691, with their complete
22-node ancestor union, in `alpha-v28-lower-layer-proof-bundle-v1.json`.
Their artifact hash is
`e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1`.
They must be extracted, source-bound and replayed, not replaced by receipts.
The natural IR016 proof and its complete Fermat-four ancestry are also retained.

## Hostile mathematical checks

- Replacing coefficient 2 by 1 makes the claim false at
  `ap=bp=s=t=1, an=bn=0`.
- Removing either signed-square premise permits a nonzero corresponding
  represented integer with `s=t=0`.
- `ap=an=5, bp=bn=7, s=t=0` is a valid input. The conclusion must be component
  equality, never the stronger and false claim that all four parts vanish.

## What this does not establish

This is the signed-integer zero-norm criterion, not full IR030 or IR032.
Integer discreteness is still needed for a witnessed absolute norm at least 1.
Norm multiplicativity, conjugate-height bounds, the interpretation of quadratic
approximations, and positive-denominator transport remain distinct obligations.
Rational coefficients need explicit nonzero denominators and common-denominator
clearing. None of this alone proves irrationality of `(sqrt2)^(sqrt2)`.

Do not reuse Gaussian `GNorm`: its quadratic form is `A^2+B^2`, not
the `A^2-2*B^2` used here. IR017/IR018 concern logarithm bounds; the relevant
quadratic branch is IR016 -> IR029/IR030/IR031 -> IR032 -> IR046.
