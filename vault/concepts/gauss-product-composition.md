---
title: Gauss product composition
tags: [peano-arithmetic, quadratic-reciprocity, gauss-lemma, finite-products]
---

# Gauss product composition

The native [[quadratic-reciprocity-moc|quadratic-reciprocity campaign]] now
has an isolated, dependency-curried proof of the algebraic center of Gauss's
lemma. A signed half-range prefix supplies:

- a magnitude code whose product is the canonical half-range product `P`;
- a zero/one reflection code with relational count `e`;
- a sign-factor code whose product is the relational power `(p-1)^e`; and
- a pointwise-product code congruent to the scaled canonical entries.

The finite folds compose to

\[
  a^h P\equiv P(p-1)^e\pmod p.
\]

Every canonical half-range factor is positive and strictly below the prime.
The generic finite-product coprimality theorem and
[[mod_eq_cancel_coprime]] therefore cancel `P` constructively, giving

\[
  a^h\equiv(p-1)^e\pmod p.
\]

This uses balanced natural Bézout witnesses; it does not add integers, a
field inverse, finite lists, or a classical axiom. The candidates remain
outside the public registry. Their current evidence checks the bodies with
dependencies as hypotheses; recursive WMI closure, mutation testing, and
admission are still required.

## Complete body-green Gauss interfaces

Witness packaging and the connection to actual quadratic-residue status are
now authored. For a canonical half-range code, the bounded endpoint assumes

\[
 p=2h+1,\quad \operatorname{Prime}(p),\quad 0<a<p
\]

and constructs a reflection count `e` together with hidden signed-prefix and
`BitCount(e)` witnesses. It proves

\[
 \operatorname{QRes}(p,a)\leftrightarrow\operatorname{Even}(e),\qquad
 \neg\operatorname{QRes}(p,a)\leftrightarrow\operatorname{Odd}(e).
\]

`bounded_gauss_lemma_complete` composes the witness-packaged power endpoint,
the predecessor-power parity bridge, and complete bounded Euler. Its pinned
direct-body receipt is 11 dependencies, 204 commands, 597 nodes, depth 53,
559 objects, 596 edges, and 38 reused objects. Its focused audit is `5/5` in
7.24 seconds.

`arbitrary_gauss_lemma_complete` replaces `0<a<p` by `p` not dividing `a`
and invokes arbitrary-representative Euler. Its independently checked receipt
is 9 dependencies, 188 commands, 547 nodes, depth 49, 513 objects, 546 edges,
and 34 reused objects. The two focused modules pass together at `9/9` in
13.64 seconds. The arbitrary tactic tail is source-shared fail-closed from the
bounded one, but no certificate or theorem authority is inherited by that
Python reuse.

Both interfaces are dependency-curried, unregistered, and unadmitted. They
are body-green endpoints, not recursive WMI replay results.

## Related

[[quadratic-reciprocity-moc]] · [[parity-transport]] · [[arithmetic-congruence]] ·
[[gcd-and-coprimality]] · [[self-contained-proof-sharing]]

## Source views

- [Research derivation](../../research/arithmetic-library/gauss-magnitude-permutation.md)
- [Jupyter Book chapter](../../book/arithmetic-library/quadratic-reciprocity.md)
- [Candidate composition](../../peano-lab/py/peano_lab/library/gauss_product_composition_candidate.py)
- [Bounded Gauss endpoint](../../peano-lab/py/peano_lab/library/gauss_lemma_bounded_candidate.py) · [test](../../peano-lab/py/tests/test_gauss_lemma_bounded_candidate.py)
- [Arbitrary Gauss endpoint](../../peano-lab/py/peano_lab/library/gauss_lemma_arbitrary_candidate.py) · [test](../../peano-lab/py/tests/test_gauss_lemma_arbitrary_candidate.py)
