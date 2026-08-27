# G005: unordered prime factorization with a witnessed permutation

This additive candidate closes the mathematical gap between historical
sorted-factor-list equality and the stronger current blueprint contract:
two **arbitrary unordered** prime factorizations admit an actual coded
bijection matching their entries. Existing Alpha-v27, Stable, definitions,
proof bodies, and kernel rules remain unchanged.

## Exact native relations

The five-row foundation tranche already defines
`PrimeFactorList(n,b,c,l)` by `n!=0 /\ (Product(b,c,l,n) /\ AllPrime(b,c,l))`.
Both the factor list and its product trace are genuine finite beta codes.
Sortedness and distinctness are not part of this predicate.

`factor_list_matching_relation(b,c,d,e,u,v,l)` says that for every `i<l`,
every actual decoded image `BetaAt(u,v,i,j)`, and every actual source factor
`BetaAt(b,c,i,a)`, the target has `BetaAt(d,e,j,a)`.

`prime_factor_list_permutation_relation(b,c,l,d,e,m,u,v)` adds `l=m` and the
existing full `PermutationPrefix(u,v,l)` relation. In particular it contains
all three conditions: every image is in `[0,l)`, the map is injective, and
every target index has an actual bounded preimage. Equal repeated factors
do not allow a many-to-one map to masquerade as a permutation.

These are hygienic first-order abbreviations, not parser primitives, list
oracles, or additional axioms. The native list representation has two beta
parameters and a length; the map has two beta parameters. Literal equality
of raw beta codes is neither needed nor asserted.

## Main checked-body contracts

`prime_factor_lists_permutation_exists` states:

```text
forall n b c l d e m.
  (PrimeFactorList(n,b,c,l) /\ PrimeFactorList(n,d,e,m)) ->
  exists u v. PrimeFactorListPermutation(b,c,l,d,e,m,u,v).
```

Its statement SHA-256 is
`89df5c484cb30ab9c74dd04af9a5700c635ae402d01f8088ff934f75e0254518`.

`prime_factorization_exists_unique_up_to_permutation` additionally constructs
the first actual factor list for every `n!=0` and, for every competing
factorization, constructs an actual matching map. No successful factorization
or canonicalization is supplied as a premise of this existence endpoint.
Its statement SHA-256 is
`622f8362d88b818d10462b55bca228e06f0c517174001c7ea039b85bb054ab7c`.

The empty factor list represents one. The proof includes the empty/empty
matching case and rules out nonempty all-prime products equal to one.
Zero is excluded explicitly by the factorization definition. Duplicate
primes and different beta encodings of equal finite lists are allowed.

## Constructive induction

1. Decompose the source product at its actual last prime. Retain an actual
   nonzero shorter product and its actual all-prime prefix.
2. Find an actual occurrence of that prime in the target using the checked
   coprime-product/prime-divisor infrastructure.
3. If it is already last, cancel it and recurse. Otherwise construct a beta
   code swapping that occurrence with the target's last position; prove the
   recoded list still has the identical actual product and prime entries.
4. Apply ordinary induction on source length. It yields equality of the two
   shorter lengths and an actual bounded/injective/surjective matching map.
5. Construct the fresh-index extension of that map. In the interior-swap
   case, use its actual preimage and construct the matching map transposition
   that undoes the target swap. Prove entry alignment at the two changed
   positions and everywhere else by injectivity.

The uniqueness dependency cone contains neither sorted-list assumptions nor
the historical sorted canonical-factorization uniqueness theorem. The
separate first-list existence endpoint legitimately reuses the established
sorted construction solely to obtain actual witnesses, then forgets sorting.

## Inventory and verification boundary

23 new ordinary HA bodies, 79 direct dependency edges, 1,504 tactic commands,
3,051 structural proof occurrences, 3,033 proof objects, maximum body 713,
maximum depth 60. Ordered-name SHA-256:

`a2049a742e30b1939d5f13475bbccabbfbb6e87f67ff48ccd37eaf397e8caff1`.

All bodies pass the unchanged original kernel in one-row authoring batches.
Focused tests pin every statement and exact native root/definition shape,
verify capture rejection, inspect the genuine dependency cone, and reject
false conclusions, truncated scripts, removed dependencies, and corrupted
dependency statements. Independent small arithmetic examples cover empty,
unsorted, repeated-prime, many-to-one, and alternative-code boundaries; these
examples are diagnostics, never proof authority.

This RFC records candidate-body validation only. Complete dependency-closed
ordinary proof packaging, independent compiled-Lean acceptance, and a new
immutable Alpha admission remain separate mandatory integration gates. No
historical release, Stable membership, commit, or deployment is changed here.
