# Complementary-divisor reindexing for actual convolution

This additive mathematical module proves commutativity and finite support for
the genuinely constructed Dirichlet-convolution tables. It introduces no new
kernel symbols or axioms and changes no inherited theorem or definition.
The immutable basis contains 3,643 prior statements: Alpha v30 (3,222), two
published research generations (170 and 126) and one local generation (125).
New convolution constructors and signed zero-window lemmas are explicit
cross-track prerequisites, never silently counted as older Alpha facts.

## Exact proof route

For a positive input `n`, the existing divisor-complement construction gives
an actual beta-coded permutation of `0,…,n`. At a positive divisor `d`, its
image is the witnessed quotient `q`, with `n=d*q`; zero and nondivisors are
fixed. The new summand lemma cancels a genuine nonzero factor to identify the
other quotient and uses actual signed multiplication commutativity. Thus
the complement map genuinely pulls one convolution summand table into the
factor-swapped table. Existing signed permutation invariance proves equality
of their actual finite sums. No quotient or permutation oracle is an input.

```text
∀F G n a b. DirichletSum(F,G,n,a) → DirichletSum(G,F,n,b) → a=b.

∀N F G H. DirichletTable(N,F,G,H) → DirichletTable(N,G,F,H).
```

The scalar graph already includes `n≠0`. Table graphs constrain positive
entries only: neither input nor output zeroth values are forced to agree.
Whole-table commutativity includes `N=0` with actual table witnesses.

The finite-support argument proves that a divisor of a positive natural
cannot lie beyond it. Consequently every actual summand at `d>n` is zero,
and a longer constructed summand prefix yields precisely the original sum:

```text
∀F G n L M z. n≠0 → Le(n,L) → DirichletPrefix(F,G,n,L,M) →
  (SignedPrefixSum(M,S L,z) → DirichletSum(F,G,n,z)) ∧
  (DirichletSum(F,G,n,z) → SignedPrefixSum(M,S L,z)).
```

Both implications retain genuine fold witnesses. The reverse direction
constructs the padded fold before using convolution functionality; it does
not insert a desired sum into the prefix definition. The inclusive summand
endpoint `n` is essential because it contributes `F(n)*G(1)`.

## Tests and status

All ten dependency-curried bodies pass the unchanged original HA checker:
34 direct prerequisite edges, 481 tactic commands, maximum 239 body-node
occurrences, 236 distinct body objects, and maximum depth 48. The first body's
three reused proof objects are counted honestly; object and occurrence counts
are not interchanged.

All 114 distinct focused tests pass in two bounded windows. They independently
expand all ten statements, check every original body and false target, and
drop and poison all 34 declared prerequisites. Numerical diagnostics construct
actual beta-coded complement permutations, positive/negative input streams,
masked products and cumulative sum traces. They cover arbitrary zero values,
different representations, prime and composite inputs, unused endpoints,
zero tails and the essential final divisor. Such examples are not proof
authority. The maximum observed test RSS was 424,099,840 bytes; the longer
window took 63.28 seconds, within the unchanged 170/175 CPU, 180 wall-second
and 1,536 MiB ceilings.

Complete original-HA bundles, independent compiled-Lean checks, ordinary root
replay and exact novelty are separate mandatory gates before verified explorer
labels. Commutativity alone does not close Möbius inversion (G007), the general
inverse criterion or the multiplicative-function requirements of G009.
No Alpha/Stable promotion, commit, push or deployment is performed here.
