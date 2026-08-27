# Exact first-layer foundation endpoints

This additive five-row candidate reuses the immutable Alpha-v27 library.
It changes no Stable entry, historical proof body, kernel rule, or release.
Dependency-curried body checks are authoring evidence; a later complete
ordinary-proof closure and separate Alpha admission remain required.

## Exact scope

| Goal | New endpoint | Statement boundary |
| --- | --- | --- |
| G001 | `foundation_division_exists_unique` | Every nonzero divisor has an actual quotient and strict remainder; every other such pair equals the chosen pair. |
| G002 | `foundation_signed_bezout_canonical_gcd` | Every pair of naturals has an actual gcd, actual canonical signed-natural Bezout coefficient codes, and uniqueness of the gcd value. Coefficients are not asserted unique. The zero/zero case is included, so no positive-input premise is added. |
| G003 | `foundation_coprime_product_divisor` | Coprimality and divisibility of the product yield an actual quotient of the other factor. |
| G004 | `foundation_prime_factor_list_exists` | Every positive natural has an actual beta-coded finite list of prime factors with an actual product trace equal to that natural. |
| G021 | `foundation_primes_above_every_bound` | Every natural bound has a genuinely larger prime. |

The existing Stable proofs already provide division existence/uniqueness,
relational gcd uniqueness, coprime cancellation, actual sorted prime-list
existence, and prime unboundedness. Existing Alpha additionally supplies the
canonical signed-natural Bezout representation. These rows expose exact joint
interfaces; they do not describe these old mathematical results as novel.

## Factorization and permutation boundary

`prime_factor_list_relation(n,b,c,l)` expands conservatively to
`n!=0 /\ (Product(b,c,l,n) /\ AllPrime(b,c,l))`. It contains no sortedness,
permutation, supplied canonicalization, or unproved prime-factor oracle.
The established sorted-list existence theorem constructs the actual witnesses;
forgetting the extra sortedness proves this less restrictive list predicate.
The empty list represents one, and no prime factorization of zero is claimed.

G005 is **not** proved by these five rows. Its authoritative blueprint asks for
an actual coded bijection between arbitrary unordered prime-factor lists.
The existing sorted-list extensional uniqueness theorem alone does not meet
that contract. A separate `prime_factorization_permutation_candidate` module
must construct the matching index permutation and prove its boundedness,
injectivity, surjectivity, and entry alignment.

## Audited inventory

Five ordinary bodies, seven direct dependencies, 92 tactic commands,
168 structural proof nodes, maximum depth 33. Ordered-name SHA-256:

`3fb216ba4a46248e14444b3927af3c5534f930ca0fa2757d7310927ae41751cb`.

The focused tests authenticate the immutable 2,560-row parent catalogue,
pin every endpoint statement, check exact expanded formula shapes, reject
capture and unsafe fragments, and reject false conclusions, truncated bodies,
missing dependencies, and corrupted dependency formulas. Checks run one body
at a time in the unchanged original kernel, without editing replay limits.
