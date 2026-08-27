# Arithmetic foundations, the first primes, and quadratic integer division

Alpha v28 adds **204 independently checked theorems** and closes nine exact
blueprint targets: **G001–G005, G021–G022, G081, and G084**. These results
strengthen the lower layers needed by many later campaigns. Every theorem
has an actual first-order proof; none is admitted from a numerical experiment,
a definition graph, or an assumed quotient or factorization algorithm.

The complete library now has **2,764 checked-use theorems** and **8,984 genuine
proof-dependency edges**. Stable remains the unchanged, default **432-theorem**
edition. The **2,332 Alpha-only** theorems require explicit Alpha selection.

## Four linked proof explorers

| Explorer | New theorem pages | Exact completed scope |
|---|---:|---|
| [Arithmetic and unique prime factorization](../_static/constructive-lower-layer-explorer/arithmetic-foundations/index.html) | 27 | Unique natural division, canonical signed Bézout, coprime divisibility, prime factor lists, and their uniqueness up to a witnessed permutation |
| [The first primes and explicit bounds](../_static/constructive-lower-layer-explorer/prime-enumeration/index.html) | 19 | Unbounded primes, the least prime above an input, complete initial prime lists, and a witnessed double-exponential bound |
| [Gaussian integers](../_static/constructive-lower-layer-explorer/gaussian-integers/index.html) | 93 | Signed floor and rounding, actual coded ring arithmetic, multiplicative norm, and Euclidean division |
| [Eisenstein integers](../_static/constructive-lower-layer-explorer/eisenstein-integers/index.html) | 65 | Actual coded ring arithmetic, the Eisenstein norm, and Euclidean division by an explicit floor construction |

Each explorer preserves the original Quadratic Reciprocity reading interface:
exact native statements and scripts, a definition-aware edition, permanent
theorem tags, printable dependency maps, and links back to the large research
atlas. The presentation moves the prime-unboundedness interface from its
foundation source package to the prime explorer. Thus the authoring counts
are 28 foundations and 18 prime-enumeration results, while the page counts
are 27 and 19. No theorem is duplicated or omitted.

## What was proved

### Arbitrary unordered factorizations

G004 constructs an actual beta-coded list of primes whose product is a
given positive natural number. Its empty list represents one.
G005 starts from **any two** such lists, including repeated prime factors,
and constructs an index map which is bounded, injective, surjective, and
matches corresponding factors. Neither list is required to be sorted.
The combined endpoint is
`prime_factorization_exists_unique_up_to_permutation`.

The earlier arithmetic interfaces are also made explicit: quotient and
remainder are unique, the signed Bézout coefficients produce the canonical
gcd even at `(0,0)`, and a divisor coprime to one factor can be cancelled
from a product. These are the exact G001–G003 contracts, not strengthened
axioms or replacements for their historical proofs.

### The actual first primes

`NextPrime(a,p)` says that `p` is the globally least prime above `a`.
`InitialPrimeList(b,c,k)` encodes the first `k` primes, not just a convenient
increasing subsequence. The library proves existence, strict increase,
primality of every entry, and no omission of any smaller prime.

For every `k != 0`, `first_primes_double_exponential_bound` constructs the
list, its final prime, and both powers witnessing

```text
p_k < 2^(2^k).
```

The theorem does not assume a supplied list or power table. The separate
total-list theorem includes `k = 0`. Its proof uses the already checked
Bertrand theorem, so G022 is placed after that actual prerequisite in the
atlas; historical planned dependencies are retained separately.

### Quotients and remainders in two quadratic rings

The main endpoints are `gaussian_euclidean_division_exists` and
`eisenstein_euclidean_division_exists`. Each constructs actual canonical
quotient and remainder codes, together with genuine norm witnesses, from
valid input codes `a,b` and `b != 0` alone:

```text
a = b*q + r  and  N(r) < N(b).
```

In the Gaussian ring, the norm is `x*x + y*y`; the quotient uses signed
rounding in the square lattice. In the Eisenstein ring, the norm is
`x*x - x*y + y*y`, with `omega*omega + omega + 1 = 0`; an explicit floor
quotient in the fundamental parallelogram suffices for strict decrease.
The Eisenstein proof does **not** assert globally nearest-point optimality.

The input carrier is not all natural numbers: its validity predicate
recognizes genuine canonical signed-pair codes. The constructive proofs
produce output codes satisfying the same representation relations.
They do not assume division, a remainder bound, norm multiplicativity, or
an external integer implementation as an oracle.

## One conservative definition DAG

The 35 new shared identities **ND0142–ND0176** extend, without replacing,
the historical registry. The atlas now contains **233 reviewed conservative
definitions** and **441 reviewed definition-dependency edges**. These are
distinct from the 323-term planning vocabulary and from actual theorem
dependencies.

The two rings share exactly the same `SignedDecode`, `ZPairDecode`,
`ZPairValid`, `ZPairRep`, and `ZPairAdd` objects. Their multiplication and
norm objects are intentionally different: `GMul`/`GNorm` and `EMul`/`ENorm`.
`GDivRem` and `EDivRem` express the actual arithmetic equation; the respective
`GEuclideanDivision` and `EEuclideanDivision` relations also require genuine
norm witnesses and strict decrease. Every abbreviation expands hygienically
to the original arithmetic AST, including under nested binders.

`PrimeFactorList`, `FactorListMatching`, and `PrimeFactorListPermutation`
likewise describe actual finite witnesses. Their arities are not silently
identified with older, incompatible planning placeholders. The earlier
Gaussian/Eisenstein norm plans remain archived as planning history.

## Evidence and the next research boundary

The new complete certificate has **862 proof nodes**: 861 real theorem
bodies and one conjunction packaging node. It contains **3,090 dependency
edges** and **230,464 structural body-proof occurrences**, and occupies
**18,977,050 bytes**. It is independently accepted by the unchanged original
HA checker and the separately compiled Lean verifier. Its SHA-256 is:

```text
e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1
```

The six mathematical source suites contain **1,412 passing tests**, including
negative cases, repeated factors, empty lists, zero and signed boundaries,
large integer examples, representation invariance, and source-proof checks.
Tests supplement the complete proof certificates; they do not replace them.

The next lower-layer targets include totient and Möbius identities, Gaussian
and Eisenstein gcd/factorization, and prime-power finite fields. **G082, G083,
G085, and G086 remain open**: Euclidean division is a prerequisite, not an
already completed unique-factorization or prime-classification theorem.
Higher reciprocity laws, representation counts, and stronger lattice results
also remain separate research goals.

Use the {doc}`multiscale atlas <grand-campaign-atlas>` to inspect these actual
prerequisite cones, and {doc}`Alpha and Stable editions <library-editions>`
for the opt-in checked-use API. The immutable v27 mathematical and explorer
snapshots remain independently reproducible; their current v28 presentation
preserves every original theorem and first-admission record.
