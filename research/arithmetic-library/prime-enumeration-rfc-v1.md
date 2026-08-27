# Actual initial-prime lists and an effective nth-prime bound

Date: 2026-08-27. Blueprint target: G022. Parent: immutable Alpha v27,
catalogue SHA-256
`481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6`.

## Exact mathematical contract

For every positive natural k, construct beta parameters b,c, a final index j,
the kth prime p, and both exponentiation witnesses e,B such that

```text
k = S j
InitialPrimeList(b,c,k)
BetaAt(b,c,j,p)
PowTwo(k,e)
PowTwo(e,B)
p < B
```

The sole premise of `first_primes_double_exponential_bound` is `k != 0`.
No prime list, search termination, power value, prime-count bound, or omitted
minimality hypothesis is supplied. Its exact statement SHA-256 is
`b69363aca6a0a887d3baba0ca6ddd13a550496075f15ec2cb4199e7c73054676`.
The stronger construction `initial_prime_chain_bounded_exists` provides the
actual first k+1 primes with terminal prime strictly below `2^(k+2)`.

`first_primes_list_exists` also constructs the empty list when k=0. The
positive-index bound does not pretend that a zeroth prime exists.

## Conservative definitions and their semantics

- `NextPrime(a,p)` means that p is prime, a<p, and p<=q for every prime q>a.
  Finite decidable scanning, followed by Euclid unboundedness, constructs it;
  its minimality proves uniqueness. It is not merely an arbitrary prime above a.
- `InitialPrimeChain(b,c,k)` begins with two at index zero and contains k
  actual `NextPrime` transitions. Thus it has k+1 prime entries.
- `InitialPrimeList(b,c,k)` is empty at k=0; otherwise k=S j and the same code
  is an `InitialPrimeChain(b,c,j)`. The two beta parameters refine the
  blueprint's schematic single list variable. This is not an arity-compatible
  alias for the planning notation `PrimeList(s,k)`.

Separate ordinary proofs establish that every list entry is prime, every
earlier entry is strictly smaller, and every prime below any entry occurs at
an explicitly bounded index. The list therefore really is the first k primes;
a sparse Bertrand chain, a repeated prime, or an omitted smaller prime cannot
satisfy this interface.

All relations expand hygienically into the unchanged first-order arithmetic
language. Existing `Prime`, `BetaAt`, `Le`, `Lt`, `Pow`, and `PowTwo` definitions
are reused without changing their identities. No sequence or exponentiation
primitive is added to the trusted kernel.

## Proof DAG and verification boundary

The 18 dependency-ordered rows have 74 direct edges, 802 tactic commands,
1,446 structural body-proof nodes, and maximum body depth 57. Their ordered
name digest is
`e825e8c48261a136f77575ec7505919456ec3badd0796dbbadb59f64e56eeec9`.
The largest body has 193 nodes. The arithmetic root uses the actual checked
strict Bertrand theorem to bound the least prime, not an oracle about prime gaps.

Every dependency-curried body is independently accepted by the original HA
kernel; negative tests remove every direct prerequisite, truncate every body,
and strengthen every target by false. Definition tests check exact free
parameters, alpha-renaming, syntax injection, and binder capture. Finite
examples illustrate the first 128 primes and deliberately avoid constructing
huge double-exponential host numerals. They are not mathematical evidence.

Candidate-body checks do not grant edition membership. Alpha admission
requires the separate exact dependency-closed artifact, original-kernel
checking of every actual body, compiled Lean verification, and an additive
sealed release. Stable remains the unchanged 432-theorem default. No new
axiom, classical rule, or resource-limit increase is used.
