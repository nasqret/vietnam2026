# Alpha v26: complete the first execution wave

This additive release closes blueprint goals G077 and G078. “First wave” means
the remaining mathematical obligations in section 7.1 of the grand campaign,
not all 120 research goals. The literal foundational DAG layers 0–1 were
already available. Later determinant, Hensel, generalized-CRT, and other
research obligations are not promoted by this release.

## Exact mathematical surface

The immutable Alpha-v25 parent has 2,080 checked-use theorems. Append exactly
58 first-order intuitionistic arithmetic theorems, in this dependency order:

| Campaign | New theorems | Direct proof dependencies |
| --- | ---: | ---: |
| Coprime square-factor extraction | 9 | 48 |
| Positive primitive Pythagorean inverse/classification | 23 | 77 |
| Fermat-four strict descent and zero-boundary classification | 26 | 93 |
| Total | 58 | 218 |

The new edition has 2,138 checked-use theorems and 6,851 direct proof edges.
Stable remains the identical 432-theorem object and the default release
channel. No historical theorem, certificate, source binding, or definition
identity is rewritten.

The principal exact statements are:

```
Coprime(a,b) -> a*b=z*z -> exists u v. a=u*u /\ b=v*v

(exists q. b*b=(a*a)*q) -> exists k. b=a*k

PrimitiveTriple(a,b,c) <-> EuclidParametrization(a,b,c)

forall x y z. FermatFourCounterexample(x,y,z) ->
  exists a b c. SmallerFermatFourCounterexample(a,b,c,z)

forall x y z. ~(x=0) -> ~(y=0) ->
  ~(x*x*x*x + y*y*y*y = z*z)

forall x y z. x*x*x*x + y*y*y*y = z*z*z*z <->
  TrivialFermatFourSolution(x,y,z)
```

The displayed `forall` is implicit in the first three lines; `<->` abbreviates
the conjunction of both implications. The checked sources always contain the
fully expanded ordinary language, not these display macros.

`PrimitiveTriple` explicitly requires all three coordinates to be nonzero.
The historical `PrimitivePythagorean` predicate deliberately retains its
zero-leg cases. `EuclidParametrization` constructs coprime opposite-parity
parameters m>n>0 and c=m²+n² with either ordered orientation of the two legs.
Natural subtraction is expressed by m²=n²+a or m²=n²+b, not a new operation.
The G078 endpoint quantifies over every z, including zero.

## Proof architecture

Square-factor extraction uses reduced gcd cofactors and checked Gauss
cancellation. It requires neither prime factorization nor a choice principle.
The inverse constructs coprime half-factors of the odd hypotenuse and odd leg,
extracts their square roots, and derives the exact parameter order and parity.

For Fermat four, gcd normalization supplies coprime positive bases without
increasing the height. Two actual oriented Pythagorean inversions, coprime
square splitting, and the odd doubled-product split construct a positive
counterexample with strictly smaller height. Only then is the historical
checked bounded-induction bridge instantiated. No descent implication is
silently treated as an unconditional theorem.

## Definition and display contract

The reviewed registry grows from 120 to 131 definitions with 231 separate
definition-dependency edges. The five existing `CF0011`, `CF0013`, `CF0014`,
`CF0015`, and `CF0016` explorer identities retain their exact expansions.
New `ND0069`–`ND0074` introduce positive triples, oriented Euclid witnesses,
primitive and smaller counterexamples, trivial Fermat solutions, and the full
two-orientation parametrization. The closed descent alias keeps its genuine
nullary signature rather than acquiring a dummy argument.

Definition dependencies, theorem proof dependencies, and theorem notation
usage have different edge kinds. Every displayed abbreviation is expanded
with capture-avoiding substitution and compared to the original de Bruijn
formula. A failed or over-budget compaction retains exact text and gains no
equivalence receipt. Large tactic-local propositions use explicit per-source,
distinct-source-count, and aggregate-character limits; repeated sources share
the budget while keeping their own command hashes and line-number receipts.

The current explorer follows the unchanged Quadratic Reciprocity design,
keeps historical proof tags, exposes definitions as navigable DAG vertices,
and retains the exact-source edition alongside the compact reading edition.

## Admission gates

Admission requires the complete self-contained proof bundle, not body-only
tests, source hashes, numerical examples, or a claim that Lean agreed.
Every real dependency body is checked by the unchanged original kernel.
The independent compiled Lean verifier must also accept the exact artifact
before the release builder issues a catalog. All new checked-use roots must
fail closed when their proof artifact is missing, altered, or misindexed.

The expected artifact is
`alpha-v26-first-wave-proof-bundle-v1.json`; its exact bytes, nodes, edges,
and independent-verifier result are recorded in the separate source-bound
`alpha-v26-first-wave-receipt.md`. The complete cone contains 215 real theorem
bodies and one synthetic conjunction root covering the four maximal endpoints.

Tests reject false/truncated proofs, missing actual dependencies, reordered or
forged release rows, altered source/certificate bindings, conflicting
definition identities, cyclic definition graphs, binder capture, fabricated
equivalence receipts, and accidental Stable promotion. Reconstruction is
microbatched and counts actual proof identities against its memory limits.

This RFC authorizes neither a remote deployment nor a Git-history rewrite.
