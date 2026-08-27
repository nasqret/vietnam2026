# G006: the actual Euler totient and its complete prime-support product

Date: 2026-08-27.

This additive development supplies ordinary constructive HA proof bodies for
the full G006 statement. It does not change the kernel, tactics, admission
limits, any frozen provider, or Alpha/Stable metadata. Its authoring parent is
the immutable Alpha-v28 catalogue: 2,764 checked theorems, Stable 432,
catalogue SHA-256
`897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`.

## Exact endpoint and boundary

The principal theorem is `totient_euler_product_formula`:

```text
∀ n. n≠0 → ∃ f g l t.
  PrimeFactorList(n,f,g,l) ∧ Phi(n,t) ∧ EulerProduct(n,t).
```

`PrimeFactorList` is the frozen G004 relation: positive `n`, an actual
beta-coded list of prime factors, and an actual product trace equal to `n`.
The list need not be sorted. `EulerProduct` independently constructs complete
distinct positive prime-valuation support for the same `n`, a beta-coded list
of `p^(Val(p,n)-1)*(p-1)`, and its actual product `t`. In particular:

- No factorization, valuation support, preceding power, count, CRT trace,
  Euler-factor code, or product witness is supplied as an endpoint premise.
- The product ranges over every distinct prime divisor of `n`; it is not a
  product over a supplied incomplete or repeated list.
- `Phi(1,1)` is proved using the canonical interval containing just residue
  zero. `totient_euler_product_one` explicitly chooses nine zero codes,
  including the empty support length, and proves its empty product is one.
- Both `Phi(0,t)` and `EulerProduct(0,t)` are excluded by proved theorems.
- Finite lists use their actual code, scale, and length witnesses. This does
  not pretend that the planning notation `Factorization(n,s)` has the same
  raw arity as the reviewed list relation.

The stronger graph-equivalence theorem `totient_euler_product_iff` proves,
for arbitrary natural `n,t`, both `Phi(n,t) → EulerProduct(n,t)` and the
reverse implication. Neither graph is defined in terms of this equivalence.

## Independent conservative definitions

The public builders accept identifier arguments and a keyword-only `tag`.
They expand only ordinary HA formulas and existing beta, finite-sum,
finite-product, primality, coprimality, power and valuation relations.

| Public builder | Arguments | Meaning |
| --- | --- | --- |
| `unit_bit_prefix_relation` | `n,b,c,L` | At every `i<L`, the decoded bit is one precisely for `Coprime(i,n)`, and zero otherwise. |
| `unit_count_relation` | `n,L,t` | There are actual unit-bit codes and an actual beta sum of their first `L` entries equal to `t`. |
| `totient_relation` | `n,t` | `n≠0 ∧ UnitCount(n,n,t)`. |
| `totient_prime_power_factor_relation` | `p,e,c` | `Prime(p)`, `e≠0`, and actual `h,d,Q` with `p=S h`, `e=S d`, `Pow(p,d,Q)`, `c=Q*h`. |
| `totient_euler_factor_prefix_relation` | `pb,pc,eb,ec,fb,fc,L` | Every bounded index decodes its prime, exponent and computed Euler factor from these same three lists. |
| `totient_euler_product_relation` | `n,t` | Actual complete distinct valuation support, the associated Euler-factor list, and its finite product `t`. |

The first three builders are in `euler_totient_count_candidate.py`; the
last three are in `euler_totient_product_candidate.py`. The auxiliary
`UnitCount` is total even for modulus zero, but this does not extend the
domain of `Phi`. The indicator uses **`i`, not `S i`**, so the interval is
exactly `0≤i<n`; this is material at `n=1`.

The definition dependencies are acyclic:

```text
Beta + Lt + Coprime ──> UnitBitPrefix
UnitBitPrefix + Sum ──> UnitCount ──> Phi (also n≠0)

Prime + positive exponent + predecessors + Pow ──> EulerFactor
Beta + Lt + EulerFactor ──> EulerFactorPrefix
PrimeValuationSupport + EulerFactorPrefix + Product ──> EulerProduct
```

There is no definition edge from `Phi` to `EulerFactor` or `EulerProduct`.
Equality is proved later. The product definitions retain the frozen support
relation rather than introducing a competing meaning of valuation or prime
factorization. All six new builders have AST-equivalence, free-parameter,
alpha-renaming, malformed-input and capture checks; the compound Euler
definitions are independently compared with their actual primitive graphs.

## Constructive proof route

1. The actual canonical gcd decides `Coprime(i,n)`. HA induction and
   `beta_prefix_extend` construct the characteristic bits. Existing finite
   summation then constructs the count. Its value is unique independently of
   encoding, and cannot exceed its interval length.
2. Induction proves subtraction-free interval balance. If the actual unit
   predicates agree on two intervals of length `L`, their count increments
   agree. Euclidean gcd transport proves periodicity, hence `k` complete
   periods contain `k` times the canonical unit count.
3. Adjoining a prime `p` has two genuinely counted cases. If `p|n`, the unit
   predicate is unchanged, giving `phi(n*p)=p*phi(n)`. If `Coprime(p,n)`, in
   the block `[p*j,p*(j+1))` the sole possible newly excluded index is `p*j`.
   Its old unit indicator equals that of `j`, and every positive offset is
   prime to `p`. Induction over the blocks gives
   `phi(n*p)+phi(n)=p*phi(n)`, so for `p=S h` cancellation gives
   `phi(n*p)=h*phi(n)`.
4. These recurrences prove positive prime-power values. A separate induction
   over a real prime-factor list proves coprime multiplicativity; frozen
   G004 constructs that list, so the final multiplicativity theorem has no
   list or CRT-witness premise.
5. Frozen `prime_valuation_support_exists` constructs distinct positive
   prime exponents, their actual power factors and product `n`, and complete
   coverage of prime divisors. The new proofs construct every preceding
   power and Euler-factor beta entry. Injectivity of the prime list and
   `coprime_powers` prove the power factors pairwise coprime. Induction over
   the two actual product traces then proves their Euler-factor product is
   precisely the independently defined `Phi` value.

This route does not need a new rectangular CRT-counting oracle or an
unproved assertion about a finite set's cardinality. Existing shuffle lemmas
whose historical names contain `four_square` are ordinary addition identities;
using them does not assume the four-square theorem.

## Inventory and integration order

The five new providers expose factories named
`make_<module stem>_theorems`. Within each factory the order is topological.

| Module stem | Rows | Direct dependencies | Tactic commands | Body nodes | Maximum depth |
| --- | ---: | ---: | ---: | ---: | ---: |
| `euler_totient_count_candidate` | 25 | 48 | 617 | 1,072 | 42 |
| `euler_totient_interval_candidate` | 12 | 32 | 458 | 796 | 48 |
| `euler_totient_prime_step_candidate` | 17 | 59 | 622 | 1,161 | 46 |
| `euler_totient_algebra_candidate` | 9 | 65 | 570 | 928 | 50 |
| `euler_totient_product_candidate` | 21 | 62 | 939 | 1,546 | 73 |
| Total | 84 | 266 | 3,206 | 5,503 | 73 |

There are 5,485 body proof objects; the largest single body has 239 nodes.
The all-84 ordered-name SHA-256, joining names with newline and **no trailing
newline**, is
`b5fc4d93d3c19c97026a89f5dac586cee74c154a16604da8b9dfef8d5c4d7a2f`.

The first four providers require only Alpha v28 and earlier providers in
this table. Before the fifth provider, include the separately frozen
`prime_valuation_support_candidate` (20 rows, factory
`make_prime_valuation_support_candidate_theorems`). That common source's
SHA-256 is
`bbd6e661a575f6a39f7a71424611da36a16d34cb6704cbae2b918387cc0f66d2`;
its RFC is `prime-valuation-support-rfc-v1.md`. G006 does not depend on the
squarefree or perfect-power-profile providers that also consume this support.

Principal theorem statement SHA-256 pins:

| Theorem | SHA-256 |
| --- | --- |
| `totient_exists_unique` | `949c4af14495d74cb45019f5e068fbb45580968e2abf1527f27b80146db77013` |
| `totient_one_value` | `c25486aebde25c7405e66abd7d4018c19e607f1c9400ae0b5b15123a6e7b2b17` |
| `totient_prime_power_value` | `5a77436d23c80965981715a3196f5669122f4184a3201c19955d7fdfcdfb10f0` |
| `totient_coprime_multiplicative` | `13319c5d902961834ee8b29318cc2bee30c5e5c77bee7443756e7fe40a832e11` |
| `totient_euler_product_exists` | `825e79f251c91fc4664ef8f304b143c67aa4c6dae03a2c029ac5be3082efc128` |
| `totient_euler_product_iff` | `1d37df29457d21f2f36c8fc9a652a0dfcde15bde5a730c8a3ae789fcf98eb176` |
| `totient_euler_product_one` | `5650edfce8b3712b3658545e921b60eeabc9f895078d4f2a756be5d19a698d45` |
| `totient_euler_product_zero_excluded` | `4f75707ef4318b5d242df321a53288e3f0d62bbd69acd9b487bfbe4d9a0484a4` |
| `totient_euler_product_formula` | `30f159a663418d13fe52b39acca9de20a67d44219cc28eb965c36f352ddcf2a2` |

## Verification boundary

Every one of the 84 bodies has passed the **unchanged original kernel** as
a dependency-curried theorem. Each replay uses a fresh subprocess, the exact
hash-pinned v28 catalogue specification table, the ordinary candidate-body
checker, unchanged live proof limits, an additional 45/50-second CPU guard,
and a 60-second subprocess timeout. Per-body node, depth and object metrics
are pinned in the five focused test files.

The regressions reject false strengthened conclusions, truncated scripts,
removed dependencies and false dependency statements. Additional tests reject
removing G006's positive-domain premise or substituting modulus zero into the
empty-product construction. Independent AST checks pin the actual residue
interval, arithmetic factor, complete support, same-index correspondence and
full G006 endpoint; numerical checks are explanatory regression tests only,
never proof authority.

Focused test command:

```sh
PYTHONPATH=peano-lab/py:scripts python3 -m pytest -q \
  peano-lab/py/tests/test_euler_totient_count_candidate.py \
  peano-lab/py/tests/test_euler_totient_interval_candidate.py \
  peano-lab/py/tests/test_euler_totient_prime_step_candidate.py \
  peano-lab/py/tests/test_euler_totient_algebra_candidate.py \
  peano-lab/py/tests/test_euler_totient_product_candidate.py
```

Final combined focused run: **1,084 tests passed in 276.14 seconds**. This
includes all 84 fresh-process positive body replays, exact per-body resource
profiles, proof/dependency mutations, complete public-definition and endpoint
AST contracts, positive-domain mutations, and independent numeric references.
No peak-RSS figure is asserted: the optional macOS timing utility could not
read its sandbox-restricted `kern.clockrate` metric after pytest completed.

**Admission is separate.** These tests do not constitute Alpha admission or
a closed dependency receipt. The integrating release must assemble the real
transitive proof cone, authenticate the exact statements and dependency
edges, replay it in the unchanged HA kernel, and obtain acceptance from the
independently compiled Lean checker. No such closed-bundle or deployment
claim is made by this candidate RFC.
