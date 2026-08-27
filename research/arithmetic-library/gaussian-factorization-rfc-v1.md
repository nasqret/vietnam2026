# Actual finite Gaussian prime factorization and witnessed uniqueness

Status: additive proof candidates for the exact G082 contract. All 69 bodies
in the three modules below have passed the unchanged original HA kernel.
An independently reconstructed, closed dependency bundle and its Lean receipt
remain separate release gates; this document does not grant Alpha admission.

## Exact scope and the planning boundary

For every **valid canonical Gaussian code** `z` with `z != 0`, construct an
actual unit `epsilon` and a finite beta-coded list of Gaussian prime elements
whose actual Gaussian product, multiplied by `epsilon`, equals `z`.
For every other such factorization, prove equal lengths and construct a real
beta-coded bijection matching the factors by witnessed multiplicative units.

This is the exact G082 atlas statement. The planning prose's word
“canonical” must not be read as a stronger theorem selecting sorted primary
representatives or a unique leading unit. Those normalizations are not part
of the atlas contract and are not claimed here. In particular, replacing
`1+i` by `i*(1+i)` while adjusting the leading unit gives a different, equally
valid literal factor list. The conclusion proves association, not literal
equality of the factor codes or leading units.

The source remains constructive first-order Heyting arithmetic. There is no
classical extraction from `not forall`, no assumed primality or factorization
decision oracle, no extra function symbol, and no new kernel rule or axiom.

## Conservative definitions

The signed-pair carrier, multiplication and norm are exactly the frozen G081
graphs. `ZPairValid(z)` is not true for every natural code. The Gaussian zero
has code `0`; Gaussian one has code `6`. The four usual unit codes are
`2,4,6,10`. In particular, natural code `1` is not the multiplicative identity
and is not a valid Gaussian code.

The preceding ring/gcd chapter supplies these actual graphs:

```
GDvd(d,z)       := exists q. GMul(d,q,z)
GUnit(u)        := exists v. GMul(u,v,6)
GAssociate(a,b) := exists u. GUnit(u) and GMul(u,a,b)
GIrreducible(p) := ZPairValid(p) and p != 0 and not GUnit(p)
                  and forall a b. GMul(a,b,p) -> GUnit(a) or GUnit(b)
GPrime(p)       := ZPairValid(p) and p != 0 and not GUnit(p)
                  and forall a b c. GMul(a,b,c) -> GDvd(p,c)
                       -> GDvd(p,a) or GDvd(p,b)
```

`GIrreducible` and `GPrime` are proved equivalent by the actual Euclidean gcd
and Bezout proofs. The factorization endpoint really uses `GPrime`; it does
not quietly rename an irreducible predicate “prime.”

The new product and factor predicates are ordinary conservative expansions:

```
GProduct(b,c,l,P) :=
  exists h e.
    Beta(h,e,0,6) and Beta(h,e,l,P) and
    forall i < l. exists a R T.
      Beta(b,c,i,a) and Beta(h,e,i,R) and Beta(h,e,i+1,T)
      and GMul(R,a,T)

AllGPrime(b,c,l) :=
  forall i p. i < l -> Beta(b,c,i,p) -> GPrime(p)

GPrimeFactorization(z,epsilon,b,c,l) :=
  GUnit(epsilon) and AllGPrime(b,c,l) and
  exists P. GProduct(b,c,l,P) and GMul(epsilon,P,z)
```

`AllGIrreducible` and the corresponding irreducible-factorization predicate
are used as internal induction interfaces, with checked conversion in both
directions. Beta entries are genuine bounded remainders, so the universal
entry predicate cannot make a nonempty list vacuous by omitting its values.

For a map encoded by `(u,v)`, the matching predicate is

```
forall i j p q.
  i < l -> Beta(u,v,i,j) -> Beta(b,c,i,p) -> Beta(d,e,j,q)
  -> GAssociate(p,q).
```

The permutation predicate separately includes boundedness, injectivity and
surjectivity of this actual decoded map, as well as equality of the source
and target lengths. Every association contains an actual unit witness.
Equality of norms alone is not a substitute for association.

Public relation builders accept trusted term ASTs in an explicit variable
context. They reject formula/code injection and every generated binder
collision, including unused caller names and the nested historical beta
binders. Definition sharing is presentation-only: the ordinary expanded HA
formula remains the proposition checked by the original kernel.

## Proof layers and dependency direction

```
frozen G081 signed carrier, norm and Euclidean division
  -> actual Gaussian ring, units and cancellation
  -> quotient-witness divisibility and its decision procedure
  -> norm-recursive gcd/Bezout -> irreducible iff prime

actual norm -> bounded canonical coordinates -> finite divisor search
  -> irreducible or actual smaller nonunit factors
  -> irreducible divisor -> actual strictly smaller quotient
  -> beta Gaussian product construction -> finite prime factorization

actual ring + beta products -> replacement balance and swap invariance
  -> finite irreducible-divisor occurrence
  -> associate cancellation + recursive bijections
  -> full witnessed prime-factorization uniqueness
```

There is no dependency cycle from gcd/Bezout back to prime factorization.

### 1. Finite, constructive search

Normalize the actual signed coordinates of a value of norm `N`. For a
canonical signed integer code whose coordinate square is at most `N`, prove
that its code is at most `2*N`. Consequently

```
GNorm(z,N) -> exists rc ic.
  z = Pair(rc,ic) and rc <= 2*N and ic <= 2*N.
```

These bounds concern canonical signed codes, never the possibly unbounded
positive and negative components of an arbitrary overlapping representative.
Every pair of signed-coordinate codes constructs a valid Gaussian code.

A proper-norm divisor is an actual nonunit divisor `d` with an actual norm
`D < N`. Unit status, actual divisibility, the norm and natural order are
constructively decidable. Two ordinary finite inductions exhaust the
`(2*N+1)` by `(2*N+1)` coordinate rectangle. They return either an actual
proper-norm divisor or a proof that no such divisor exists anywhere.

Any factorization into two nonunits has both factor norms at least two.
Multiplicativity of the actual norm then proves both strict decreases, so
the finite search cannot miss a reducible nonzero Gaussian value. This
produces the actual factor witnesses needed by HA; it is not an appeal to
classical De Morgan equivalence.

### 2. Actual finite factorization

Bounded norm induction first constructs an irreducible divisor. If `p` is a
nonunit divisor of a nonzero `z`, an actual quotient `q` is constructed from
divisibility and satisfies `N(q) < N(z)` and `q != 0`. The strict decrease
also holds when `q` is a unit.

A second bounded norm induction factorizes the quotient and appends `p` to
its actual beta factor array. A separate beta extension appends the actual
Gaussian multiplication step to the product history. The trace begins at
code `6`, and association of actual products reconstructs the original
value with its actual leading unit.

Every unit is handled by a genuine empty factor list. No nonempty product
of irreducibles can be a unit, and no such factorization can reconstruct
zero. Product values are functional canonical codes, not merely equivalent
representatives or abstract sums of code values.

### 3. Actual units and permutations

The main induction proves the stronger intermediate result that two actual
finite irreducible products which are associated have equal lengths and a
constructed unit-matching bijection.

Choose the last factor `p` of the first list. The actual prime-divisor
product theorem finds an actual occurrence in the second list associated
to `p`. When that occurrence is internal, construct a beta swap moving it
to the end. An independently proved Gaussian product replacement balance
and swap law show that the newly constructed product has exactly the same
canonical value.

Cancel the two associated nonzero last factors from the associated actual
products. This constructs a unit witnessing association of the shorter
products. Apply the induction hypothesis, extend the actual permutation by
its fresh last index, and undo the target swap by transposing the two actual
map entries. Boundedness, injectivity, surjectivity and the per-factor unit
witnesses are all proved. Repeated equal or associated factors require no
distinctness assumption.

Finally, the actual leading units show that two factorizations of the same
value have associated raw products. Converting prime factors to
irreducibles and back gives the complete G082 statement.

## Files, factories and principal endpoints

All paths in this section are relative to the repository root. The three
mathematical modules are under `peano-lab/py/peano_lab/library/`.

| Module | Factory | Rows | Dependency edges | Tactic commands |
| --- | --- | ---: | ---: | ---: |
| `gaussian_factor_search_candidate.py` | `make_gaussian_factor_search_candidate_theorems` | 23 | 107 | 1140 |
| `gaussian_factorization_candidate.py` | `make_gaussian_factorization_candidate_theorems` | 28 | 91 | 1125 |
| `gaussian_factor_permutation_candidate.py` | `make_gaussian_factor_permutation_candidate_theorems` | 18 | 81 | 1437 |
| Total | | 69 | 279 | 3702 |

The release order is: ring `65`, divisibility `29`, gcd/prime `14`, search
`23`, finite factorization `28`, product reindexing `3`, factor permutation
`18`: **180 additive theorem bodies in seven factories**. The ring/gcd and
reindexing sources have their own RFCs and independent tests.

Principal checked interfaces include:

- `gaussian_factor_search_complete`
- `gaussian_irreducible_decidable`
- `gaussian_irreducible_or_strict_nonunit_factorization`
- `gaussian_irreducible_divisor_exists`
- `gaussian_irreducible_factor_reduction`
- `gaussian_product_functional`
- `gaussian_prime_factorization_exists`
- `gaussian_irreducible_products_associate_unique`
- `gaussian_prime_factorizations_unique`
- `gaussian_unique_prime_factorization`
- `gaussian_zero_has_no_prime_factorization`
- `gaussian_unit_prime_factorization_length_zero`

The 69 dependency-curried body certificates contain 6853 proof-node
occurrences and 6828 actual proof objects. The largest individual body has
827 nodes; maximum body depth is 74. These are body metrics, not a claim
about the size or depth of an independently materialized closed release
root. The full conservative G082 source statement is 311956 UTF-8 bytes;
the reviewed definition DAG is necessary for readable presentation, not for
additional logical authority.

## Reproducibility and independent evidence

The authoring tests use the exact immutable v28 catalogue as a low-memory
source of dependency statements and scripts:

```
artifacts/peano-library/alpha/catalog-v28.json
897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9
```

It has 2764 checked entries and the unchanged 432-entry Stable prefix.
The additive preceding Gaussian candidates are explicit dependencies.
Catalogue bytes and theorem hashes identify the inputs; they are not proof
authority. Every body is replayed with the original tactic engine and
kernel. Release verification must also reconstruct and check every actual
dependency body and the closed bundle, including independent Lean checking.

Run the three new focused suites from the repository root:

```
PYTHONPATH=peano-lab/py python3 -m pytest -q \
  peano-lab/py/tests/test_gaussian_factor_search_candidate.py \
  peano-lab/py/tests/test_gaussian_factorization_candidate.py \
  peano-lab/py/tests/test_gaussian_factor_permutation_candidate.py
```

Fresh subprocesses use explicit CPU, wall-time and memory bounds. No proof
limits, Python recursion limits, integer-conversion guards or job timeouts
are relaxed. Large-term structural comparisons in tests use an exact
iterative AST walk instead of recursive Python dataclass equality; no hash
is used as structural equality.

The suites distinguish finite numerical explanations from formal evidence.
They check independent first-order contracts, all generated binders,
compound and large numeric terms, zero and the four unit boundaries,
strict unit-quotient descent, actual product seed `6`, repeated associates,
non-bijective fake maps, same-norm nonassociates, and the failure of literal
unit/factor uniqueness. False conclusions, incomplete proof scripts,
missing or forged dependencies, and removed domain/nonzero guards must be
rejected by the unchanged original checker. The full endpoint also has
checked concrete carrier instances at Gaussian one and the real integer
two; numerical sampling alone is not used to establish nonvacuity.

Final focused regression receipts:

| Suite | Accepted tests | Recorded execution |
| --- | ---: | --- |
| Finite factor search | 442 | 199.29 s; 116 fresh body/negative/guard probes plus 326 independent contract and model checks |
| Actual finite products/factorization | 1197 | 260.80 s; 129 fresh body/negative probes plus 1068 independent contract and model checks |
| Unit/permutation uniqueness | 1085 | Three bounded groups: 88 fresh body/negative/guard probes in 649.74 s, 995 independent contract/model checks in 8.26 s, and two checked concrete root instances in 3.62 s |
| Total | 2724 | All accepted; no skipped proof obligation or weakened proof limit |

The long uniqueness suite checks the actual 348-command inductive body and
its corrupted/incomplete variants in fresh processes. Its existing
170-second CPU and 180-second wall limits are per process, not a claim that
all 88 independent probes run within a single such interval.

### Immutable mathematical source pins

```
gaussian_factor_search_candidate.py
039bb7e5d7bb3c3fe1acd3177904c99c62ecfd78424685e78c8c5dc28cd1b6ce

gaussian_factorization_candidate.py
cb95534689e6155fdbb1a7e80be843bdd91153504f9b5df99bf6ee59e77e8d1e

gaussian_factor_permutation_candidate.py
13d404c9870cf2ef2fb089749f60224b858d2954ec581bb37b09320c23055f1f
```

The exact full G082 principal statement SHA-256 is
`57abdbebab6835ebe1fecb15f4229f2eee579b7d67c22638345cc0deb6e20219`.
Further principal statement pins and exact per-body metrics are independently
recorded in the focused tests. Full publication/admission receipts belong to
the separately verified release, not to this source-level RFC.

## Explicitly not claimed

This closes the mathematical finite-factorization and witnessed uniqueness
content of G082 when the independent closed release gates pass. It does not
claim a sorted or primary-normalized factor list, unique literal leading
unit, a classification of all Gaussian prime elements, an efficient integer
factoring complexity bound, Eisenstein factorization, ideal factorization,
class groups, principal ideal normal forms, or automatic Stable promotion.
All previously sealed releases, the kernel, arithmetic language and proof
resource limits remain unchanged.
