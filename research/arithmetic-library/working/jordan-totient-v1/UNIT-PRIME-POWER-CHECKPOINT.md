# Jordan unit and prime-power checkpoint — 2026-09-06

Ten additional theorems now have complete original-HA proofs and independent
compiled-Lean checks. They extend the previous 86 owned Jordan rows to 96;
historical prerequisites are not counted as new results. Alpha admission,
Stable changes and public deployment are separate, unperformed operations.

## Mathematics and definitions

The six unit-modulus lemmas construct the literal singleton beta enumeration
and prove `Jordan(k,1,1)` for positive `k`, then show any such count equals one.
The four prime-power lemmas prove that, for prime `p` and positive exponent
`h+1`, a beta tuple is primitive modulo `p^(h+1)` if and only if `p` does not
divide all its coordinates. Primitivity therefore survives a change between
positive exponents of the same prime. These are statements about actual tuple
coordinates, not their nonunique beta encodings.

The statements reuse the existing 493-definition registry. Exact compact /
expand tests preserve the original formula AST and free-variable list for
every new theorem, with no new notation identity or changed definition object.
`JordanTotient` retains its genuine enumeration definition, depending on
boundedness, coordinate equality and `JordanPrimitiveTuple`; prime powers use
the existing witnessed `Pow` relation. The existing `IntegerVectorZero`
identity is reused for the zero tuple. Proof dependencies remain distinct from
definition-expansion dependencies.

The actual dependency chains are:

- Bounded coordinates modulo one → equality of bounded tuples → explicit
  singleton enumeration → `jordan_totient_at_one` →
  `jordan_totient_at_one_unique` (also using existing count uniqueness).
- Prime divisors of actual prime powers and common-divisor descent →
  `jordan_prime_power_tuple_primitive_of_not_all_divisible`; together with
  exclusion of a prime common divisor and base divisibility at positive
  exponent, this proves the characterization and exponent-invariance roots.

The sources are [unit modulus](jordan_unit_modulus_candidate.py) and
[prime-power characterization](jordan_prime_power_characterization_candidate.py).
The three roots listed below collectively contain all ten new theorem names
in their actual dependency ancestry.

## Complete and standalone certificates

The complete artifact has **358 mathematical nodes and 949 proof-dependency
edges**. Its seven-root packaging node brings the checked artifact to 359
nodes, 956 edges and 22,165 body proof nodes. Its exact 1,620,004 bytes have
SHA256 `9164d35758d1fa15d18ec792a429cbb33fd4c511df5651b9f15d37bececf5ea7`.
The authoring process freshly checked the prior Jordan86 seed and actual
historical providers, then constructed all ten new bodies. A separate fresh
process checked the complete artifact in original HA and the independently
compiled Lean verifier on identical bytes.

Each principal root was also reconstructed in the empty context, rechecked
in the original kernel, serialized as one node with no dependencies, decoded
and rechecked, and verified by Lean on exactly that standalone payload.

| Principal root | Ordinary proof nodes | Standalone bytes | HA + Lean seconds |
|---|---:|---:|---:|
| `jordan_totient_at_one_unique` | 12,019 | 1,454,755 | 9.71 |
| `jordan_prime_power_tuple_primitive_characterization` | 14,666 | 2,290,422 | 9.96 |
| `jordan_prime_power_tuple_primitivity_invariant` | 14,666 | 2,324,851 | 10.06 |

Standalone SHA256 values, respectively:

1. `8d991ede43af2baf30ae54559a64170291c3db188a0c64c91fbbe7059e236dc8`
2. `e86e6db89ec8a7da3546fcb7c9aa3eb3785c123c9c00224a568abd0c5c2b14d5`
3. `9a5cb161f03098b148f758d9f37585a6ef79dfbbdfea48f84629a8ea121c0f38`

The exact source binding is
`42a633abc05b777fd4c882e6057ef4fef7a8b3c5b56a86505eef28dc1f06d787`.
All five fresh processes exited naturally with code zero, preserving CPU
170/175 seconds, wall 180 seconds, RSS 1,536 MiB and proof depth 256.
The largest observed RSS among these processes was 667,549,696 bytes.
No kernel, inference rule, proof limit or historical certificate was changed.

Evidence (observations, not proof inputs):

- [Authoring](observations/jordan96-author-v1.json), 25.69 seconds.
- [Fresh complete HA / same-byte Lean check](observations/jordan96-bundle-v1.json),
  5.38 seconds.
- [Unit-count ordinary root](observations/jordan96-root6-v1.json).
- [Prime-power characterization ordinary root](observations/jordan96-root9-v1.json).
- [Exponent-invariance ordinary root](observations/jordan96-root10-v1.json).
- [All 87 tests](observations/jordan96-tests-v2.json): 261 successful phases,
  13.64 seconds, peak RSS 270,123,008 bytes; SHA256
  `be25348da5a2b97274eaa47606469c0ccce48c9c75c2755255d34d2a40432b32`.

The tests include independent exact statement contracts, finite beta-tuple
models, positive native bodies, false conclusions, removed dependencies,
zero-rank exclusion and every new statement's definition-DAG roundtrip.
Earlier failed script/test attempts remain saved. In particular, verbose
rendering of a rejected recursive proof state exhausted the test process's
memory allowance; isolated command checking exposed ordinary script errors
at about 55 MB. Inferable applications and explicit negation introductions
fixed the scripts; concise failure reports keep those diagnostics bounded.
No failed observation has been relabeled as passed.

## Next mathematical target

The distinct-prime Jordan product formula is **not** proved by this batch.
Next construct the coordinate-scaling bijection for tuples all divisible by
`p`, prove the bounded-tuple and complement cardinalities, derive the
prime-power count, and combine it with the already checked coprime
multiplicativity through the actual finite prime-factor product.
