# Alpha v30: constructive Gaussian unique factorization

This is an additive admission contract over the immutable Alpha v29 release.
The separately recorded complete original-kernel and compiled-Lean checks are
required release gates, not consequences of this document or its hashes.
Stable remains the same 432-theorem default edition.

## Exact milestone and mathematical boundary

The principal theorem is `gaussian_unique_prime_factorization`, completing
the exact G082 contract. In conservative named notation its content is

```text
forall z. ZPairValid(z) -> z != 0 ->
  exists epsilon b c l.
    GPrimeFactorization(z,epsilon,b,c,l) and
    forall eta d e m.
      GPrimeFactorization(z,eta,d,e,m) ->
      l = m and exists u v. GMatchedFactors(b,c,d,e,u,v,l).
```

The exact expanded HA statement has SHA-256
`57abdbebab6835ebe1fecb15f4229f2eee579b7d67c22638345cc0deb6e20219`.
This is a theorem about actual canonical signed-pair Gaussian codes, not all
natural numbers. Gaussian zero is code `0`; Gaussian one is code `6`.

`GPrimeFactorization` requires an actual unit coefficient, actual beta-coded
prime entries, and an actual Gaussian multiplication history beginning at
code `6`. Gaussian primality is the genuine product-divisor property; its
equivalence to irreducibility is proved by the Euclidean gcd/Bezout chapter.
It is not a renamed irreducibility predicate or a factorization oracle.

`GMatchedFactors` requires a bounded, injective, surjective beta-coded index
map. Every matched pair is related by an actual multiplicative unit witness.
Repeated factors and repeated associates are allowed. Literal factor codes
and the leading unit need not be unique. The theorem does not select sorted
primary representatives, classify Gaussian primes by rational congruence
classes, or assert Eisenstein unique factorization.

All four units have empty factorizations; every prime factorization of a unit
has length zero. Zero has no such factorization. The nonzero and carrier
hypotheses are necessary and are independently regression-tested.

## Frozen mathematical factories and actual proof direction

All seven factories have campaign `gaussian_factorization`, in this order:

| Module under `peano-lab/py/peano_lab/library/` | Rows | Edges | Commands |
| --- | ---: | ---: | ---: |
| `gaussian_ring_candidate.py` | 65 | 204 | 2162 |
| `gaussian_divisibility_candidate.py` | 29 | 92 | 787 |
| `gaussian_gcd_candidate.py` | 14 | 76 | 777 |
| `gaussian_factor_search_candidate.py` | 23 | 107 | 1140 |
| `gaussian_factorization_candidate.py` | 28 | 91 | 1125 |
| `gaussian_product_reindex_candidate.py` | 3 | 22 | 431 |
| `gaussian_factor_permutation_candidate.py` | 18 | 81 | 1437 |
| Total | 180 | 673 | 7859 |

Every factory is named `make_<module-stem>_theorems`. Exact factory order,
all specification fields, source pins, source/test/RFC provenance maps, and
22 principal statement hashes are checked by `alpha_enrollment_v30.py`.
The mathematical RFCs are `gaussian-gcd-prime-rfc-v1.md`,
`gaussian-factorization-rfc-v1.md`, and `gaussian-product-reindex-rfc-v1.md`.

The actual dependency direction is:

```text
frozen Gaussian Euclidean division
  -> actual ring, units, cancellation and quotient-witness divisibility
  -> norm-recursive gcd and Bezout -> irreducible iff prime

actual norm -> bounded canonical coordinates -> finite divisor search
  -> a genuine irreducible divisor and a strictly smaller actual quotient
  -> norm induction and beta-product extension -> actual prime factorization

actual products -> replacement balance and swap invariance
  -> prime-divisor occurrence, associate cancellation and beta bijections
  -> uniqueness up to witnessed units and permutation
```

No inference rule, axiom, classical tactic, trusted arithmetic oracle or
resource limit is added. Finite example models are tests, never proof
authority. Candidate-body replay and complete dependency closure remain
distinct evidence levels.

## Exact additive parent and inventory

The unmodified parent is `artifacts/peano-library/alpha/catalog-v29.json`:

```text
parent theorem / checked-use count: 3042
parent catalogue SHA-256:
2db42c10aa3196dda6a2fff73db02a86906091826a880abf4b38227f5f34f0b0
parent edition identity:
57da70c3718579cb8eb81c59a4c2898a5071140fa944e31bca312fe53432574c
parent ordered enrollment:
feac02afbfe516116accd30a6a117060f5d5cd99d608971a7f62bd1f3787104d
parent complete specification digest:
70c8d552afdf9ce499942ad263d5145e703c9dab834e9d4b66d753b5364582c1

new theorem / actual dependency-edge count: 180 / 673
new ordered-name digest (LF-separated, no final LF):
0894c4ef5f36b631a424c74d4119bd538f790245fd5e9dfb25c682e0c05e16fa
new complete specification digest:
c2072a3d9e07b3e64813e8234522e5f2c606a7be79efe03c22b730ae1ca0cd46
exact factory/provenance metadata digest:
e31f0c584cac4c227232bd2b59062395f7b6dc64e5d2764aa2d0da0d6a72bd48

Alpha v30 theorem / checked-use count: 3222
Alpha v30 actual theorem edges / layers: 10588 / 53
Alpha v30 edition identity:
8986ab8b8d8493ab7c8f01e2080b0ac590fd3c7289ac811b6606710ca453e1e9
Alpha v30 ordered enrollment:
04b73a38d04d1bd8038c1712b7f4f6cc77156f97a890515524761bb1cdf71393
```

Every parent entry is reused as the same immutable object, in the same
order, with unchanged membership, provenance and first-admission history.
The Stable entries, specifications, release order and edition object are
reused literally. Every new theorem is Alpha-only and has no Stable lookup.

## Complete proof artifact and fail-closed runtime

`campaign_gaussian_factorization_closure.py` constructs the exact actual
dependency cone: 180 new and 272 inherited theorem bodies, 1430 ordinary
dependency edges, and 18 maximal endpoints. A separate conjunction packaging
node gives 453 bundle nodes and 1448 bundle edges; it is not a library theorem.

The canonical file is exactly, including lowercase spelling:

```text
research/arithmetic-library/artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json
```

All 19 historical proof-provider byte pins are checked, including unused
providers. A reused body must match its exact target and every ordered
prerequisite target. Every body in an explicit authoring checkpoint is freshly
kernel-checked before reuse, and every final node is checked again. Hashes
detect changed evidence; they do not replace a derivation. Exports use
exclusive creation and never overwrite historical or existing artifacts.

The largest induction body can be authored separately as an ordinary closed
implication with its exact 24 prerequisites as ordered antecedents. This is
not the unconditional G082 theorem. A fresh process checks that implication,
matches its target exactly, and installs its body into the untrusted full
graph whose prerequisite nodes are actual proved theorems. The complete
original-kernel check then discharges every edge. This decomposition changes
neither proof rules nor limits; it prevents a long authoring pass from sharing
one time window with all graph reconstruction and verification work.

The edition's `require_gaussian_factorization_seal()` is a cheap metadata
eligibility guard, not a proof checker. It rejects zero, missing, malformed
or internally inconsistent proof seals before an Alpha lookup or export can
advertise the new entries. It opens no proof files; Stable does not call it.
Actual checked use reads the canonical bytes, checks exact targets and ordered
edges, and sends every body to the unchanged kernel. Missing or forged bytes
fail closed even if an attacker also rewrites their digest and byte count.

Named replay selects the genuine dependency cone, conservatively interns
ordinary syntax, checks every interned body, materializes an ordinary
empty-context certificate, and checks that certificate again. The immutable
v29 runtime still handles inherited theorems. Browser replay can supply the
exact parent specification tuple without requiring a repository catalogue.

The new provider's untrusted `compile_gaussian_factorization_replay` keeps the
original dependency graph and its validation domain unchanged. It groups the
already closed dependency-curried bodies into ordinary conjunction arguments,
then builds binder-free implication/conjunction/cut wiring from those
arguments. Every argument is supplied by its genuine closed body, outside
the temporary large layer context. Ordinary implication elimination discharges
all temporary assumptions before the final empty-context check. This avoids
repeatedly shifting irrelevant layer formulas through term binders; it does
not optimize, memoize, modify or bypass the original checker.

Resource accounting remains explicit in two domains. The original theorem
targets, edges, bodies and dependency-layer packages retain all existing graph
limits. Additional conditional argument formulas are not disguised as graph
targets or exempted from accounting: each is separately formula/depth-bounded,
and every occurrence of every added cut, argument, formula and body is charged
under the unchanged complete candidate proof/object/depth/annotation/envelope
limits. Their sum need not be a valid *expanded graph*; no expanded graph is
created or claimed. Only the actual complete ordinary certificate is accepted.
Independent regression tests reject an omitted argument, a free hypothesis,
changed conclusion, reversed premise order, swapped body premises and miswired
projections, and check every graph and transformed-candidate resource gate.

## Definitions and publication separation

Twenty additive reviewed definitions `ND0208` through `ND0227` distinguish
actual divisibility, units, association, irreducibility, primality, Bezout,
gcd, finite search bounds, product traces and witnessed permutations. All
264 parent definition objects remain unchanged. The resulting registry has
284 definitions and 560 actual reviewed dependency edges.

Definition arrows are not theorem-proof premises. Exact AST round trips and
complete binder-hygiene checks preserve the expanded HA statement. The
Quadratic Reciprocity presentation, global atlas, browser application,
channel export, deployment and Git operations are separate release work.
This RFC authorizes none of those by itself.

The observed complete proof, independent Lean provenance, ordinary root
replays, resource bounds and final regression results are recorded in
`alpha-v30-gaussian-factorization-receipt.md`.
