# Constructive Möbius values and finite signed-sum foundations

Status: completed, non-admitting foundation tranche for G007. **The full
Möbius divisor-cancellation and inversion statements remain open.**

This local tranche adds 51 ordinary HA theorem bodies. It neither changes
the immutable Alpha-v30 library nor introduces an axiom, trusted tactic,
choice principle, kernel change, resource-limit increase, or deployment.

## 1. Parent and scope

The parent is the published v30 catalogue at
`artifacts/peano-library/alpha/catalog-v30.json`, SHA-256
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`:
3,222 checked Alpha entries and the unchanged 432-entry Stable library.

The original G007 target concerns positive divisors and actual finite
signed arithmetic tables:

```
ArithTable(N,f) ∧ ArithTable(N,g) ∧
(∀m. 0<m≤N → g(m)=∑_{d|m} f(d))
  → ∃h. ∀n. 0<n≤N →
      h(n)=∑_{d|n} μ(d)g(n/d) ∧ h(n)=f(n).
```

The sum notation in that target is a specification of the remaining work,
not a definition or an admitted theorem in this tranche. In particular,
neither cancellation nor inversion has been put into the Möbius graph or
the table-validity predicate.

Completed here:

- independently defined, total and unique Möbius values on positive inputs;
- the unit boundary and the actual fresh-prime sign-change theorem;
- actual packed beta-coded signed tables, lookup and canonical-value
  functionality;
- genuine signed prefix sums, including the empty prefix, successor
  introduction/decomposition and representation-independent values;
- construction of actual beta-coded pullbacks and signed-sum invariance
  under an actual bounded injective beta map.

Not completed here: a Möbius divisor-indicator table, its prime-divisor
involution, the divisor-sum cancellation identity, finite weighted
convolution/Fubini, or the all-positive-input inversion endpoint.

## 2. Independent Möbius definition

Signed values use the existing canonical natural coding: `0` represents
zero, `2` represents positive one, and `1` represents negative one.

```
AlternatingUnit(l,z) :=
    (Even(l) ∧ z=2) ∨ (Odd(l) ∧ z=1).

HasPrimeSquareDivisor(n) :=
    ∃p. Prime(p) ∧ p*p | n.

FactorParitySign(n,z) :=
    ∃b c l. PrimeFactorList(n,b,c,l) ∧ AlternatingUnit(l,z).

Mobius(n,z) := n≠0 ∧
    ((HasPrimeSquareDivisor(n) ∧ z=0) ∨
     (Squarefree(n) ∧ FactorParitySign(n,z))).
```

Every divisibility statement has an actual natural quotient witness.
`PrimeFactorList` is the existing unsorted beta-coded list of actual prime
entries and its genuine finite product trace; it does not contain a
factorization or uniqueness oracle. `Squarefree` is the existing positive
prime-square-free predicate, with its previously proved unbounded
prime-square exclusion theorem.

The proof of literal uniqueness uses real prime-factor-list matching to
show that all such lists have the same length. The value at one is proved
using the actual empty-factor-list boundary, not inserted into the graph.
The zero input has no Möbius value under this positive-domain convention.

The fresh-prime theorem is exactly

```
Prime(p) → ¬(p|n) → Mobius(n,a) → Mobius(p*n,b)
  → SignedNegate(a,b).
```

Its squarefree branch constructs a longer beta-coded prime-factor list.
Its nonsquarefree branch transports an actual prime-square divisor and
proves both canonical values are zero. Primality and nondivisibility are
necessary hypotheses, tested both arithmetically and by body corruption.

## 3. Actual finite signed tables

Write the existing natural-pair constructor as

```
Pair(a,b) = (a+b)*S(a+b) + (b+b).
Pack(pb,pc,nb,nc) = Pair(Pair(pb,pc),Pair(nb,nc)).
```

The representation equation
`F=Pack(pb,pc,nb,nc)` is exactly the old `MatrixMinorFourCode` relation.
The existing `matrix_minor_four_code_components_injective` theorem is
reused directly. An initially drafted duplicate was removed before this
tranche was frozen; no new theorem or definition is counted for that alias.

With the unchanged `BetaAt` and canonical `SignedBalance` graphs:

```
ArithTable(N,F) := ∃pb pc nb nc.
  F=Pack(pb,pc,nb,nc) ∧
  ∀i. i≤N → ∃p n z.
    BetaAt(pb,pc,i,p) ∧ BetaAt(nb,nc,i,n) ∧ SignedBalance(z,p,n).

ArithAt(F,i,z) := ∃pb pc nb nc p n.
  F=Pack(pb,pc,nb,nc) ∧
  BetaAt(pb,pc,i,p) ∧ BetaAt(nb,nc,i,n) ∧ SignedBalance(z,p,n).

SignedPrefixSum(F,l,z) := ∃pb pc nb nc p n.
  F=Pack(pb,pc,nb,nc) ∧
  BetaSum(pb,pc,l,p) ∧ BetaSum(nb,nc,l,n) ∧ SignedBalance(z,p,n).

ArithTableEqual(F,G,l) :=
  ∀i a b. i<l → ArithAt(F,i,a) → ArithAt(G,i,b) → a=b.

ArithTableReindex(F,G,r,s,l) :=
  ∀i j a. i<l → BetaAt(r,s,i,j) →
    ArithAt(F,j,a) → ArithAt(G,i,a).
```

Table validity explicitly covers `0≤i≤N`, including `N=0`. Prefix sums
cover exactly `0≤i<l`; the empty prefix is the actual canonical zero sum.
The later number-theoretic application will separately exclude zero
divisors and use only positive arguments. These two bounds are not
interchanged.

Different component streams can represent the same signed function.
Nothing here equates those streams: `(1,0)` and `(19,18)` both represent
positive one. The equality and sum-extensionality proofs establish
balanced integer equality and then equality of canonical signed codes.
Only a fixed literal packed code has uniquely determined packing fields.

The principal permutation theorem requires both genuine input/output sum
traces, the actual lookup-pullback graph, and an actual bounded injective
beta map. It first constructs component compositions, uses the existing
natural finite-sum permutation theorem, then proves independence of the
chosen signed representatives. No sum-rearrangement premise is hidden in
`ArithTableReindex`.

All public builders take keyword-only `tag` and an explicit nonempty tuple
`variables`. They parse compound terms, including large double-and-add
numerals, and reject collisions between the entire supplied context and
every generated binder, including deeply nested inherited binders.

## 4. Factory order and complete new inventory

All paths below are relative to `peano-lab/py/peano_lab/library/`.

| Module/factory stem | Rows | Declared edges | Commands | Body nodes |
| --- | ---: | ---: | ---: | ---: |
| `mobius_value_candidate` | 13 | 22 | 296 | 462 |
| `mobius_prime_step_candidate` | 8 | 42 | 364 | 652 |
| `divisor_sum_table_candidate` | 14 | 21 | 484 | 805 |
| `divisor_sum_algebra_candidate` | 9 | 30 | 487 | 762 |
| `divisor_sum_reindex_candidate` | 7 | 22 | 439 | 571 |
| Total | 51 | 137 | 2,070 | 3,252 |

Each factory is `make_<module stem>_theorems`. The last three are general
finite signed-sum foundations; their theorem dependencies do not use the
Möbius value or fresh-prime theorems.

The complete ordered names are:

```
alternating_signed_unit_exists
alternating_signed_unit_functional
alternating_signed_unit_zero
mobius_prime_factor_count_unique
mobius_input_positive
mobius_zero_has_no_value
mobius_from_prime_square
mobius_from_squarefree_factor_count
mobius_value_exists
mobius_squarefree_evaluation
mobius_value_functional
mobius_value_exists_unique
mobius_one
mobius_squarefree_divisor
mobius_prime_squarefree
mobius_squarefree_fresh_prime_product
mobius_prime_factor_list_append
mobius_positive_unit_negates_to_negative_unit
alternating_signed_unit_successor_negates
mobius_prime_square_value_zero
mobius_fresh_prime_negates
divisor_signed_table_at_from_components
divisor_signed_table_at_to_components
divisor_signed_table_from_components
divisor_signed_table_construct
divisor_signed_table_components
divisor_signed_table_lookup
divisor_signed_table_at_functional
divisor_signed_table_restrict
divisor_signed_sum_from_components
divisor_signed_sum_to_components
divisor_signed_sum_exists_from_components
divisor_signed_sum_functional
divisor_signed_sum_empty_value
divisor_signed_sum_empty_exists
divisor_signed_balance_negate
divisor_signed_balance_negate_intro
divisor_signed_negate_fixed_zero
divisor_natural_sum_successor_intro
divisor_signed_table_equality_component_balance
divisor_signed_sum_extensional
divisor_signed_sum_negation_transport
divisor_signed_sum_successor_intro
divisor_signed_sum_successor_decompose
divisor_signed_table_lookup_from_components
divisor_signed_table_reindex_data_exists
divisor_signed_table_reindex_from_components
divisor_signed_table_reindex_exists
divisor_signed_table_reindex_functional
divisor_signed_sum_component_reindex
divisor_signed_sum_permutation_invariant
```

The SHA-256 of these names joined by a single newline, without a trailing
newline, is
`2a8c49a6cdce2af93e953386c0417489a70f0cb135e227fcc18600228962a3db`.

Selected literal statement SHA-256 values:

| Theorem | SHA-256 |
| --- | --- |
| `mobius_value_exists_unique` | `eb41094b2ceb2273e89e8966ced4cc921decf56dd6bc6dbcb5349c2087aa1135` |
| `mobius_fresh_prime_negates` | `2b0116e6d32e45fe7ae5e9a8bd7c11e5f95a88021cd42786276cff6e7ec303d2` |
| `divisor_signed_table_construct` | `065e6ef834a030b0d3d9118d538713cc0d459fb8a24f3b64b296d4f4c5ed6ca7` |
| `divisor_signed_table_at_functional` | `c47babd7207da358b0bfd877418fabee735ca070824b94fcbfdd81eb07957575` |
| `divisor_signed_sum_functional` | `857d741811328d1f67713764d25e883e6131f98b3645e3b41c2fde18d3991a9a` |
| `divisor_signed_sum_extensional` | `b5d76a97376567d4d2e34212f1172b134f14781a661d76925a3615f38065c348` |
| `divisor_signed_table_reindex_exists` | `f2cc667b787e62fe9e43a8689834b3edf048e4fe71b615639db1d2062d93f9f9` |
| `divisor_signed_sum_permutation_invariant` | `0e94ef4db7c6f73d73ae87525d29e24722764adabcd38a908ab3a844bfec57ac` |

## 5. Verification boundary

Every listed body is checked by the unchanged
`candidate_validation.replay_candidate_bodies`. That is a genuine original
kernel check of the body with its declared dependencies introduced as
ordinary hypotheses. It is **not** by itself a closed theorem or Alpha
admission receipt. Dependency ordering and declared-use tests run
separately. Root-level reconstruction must still close the actual complete
dependency cone and check the resulting empty-context certificate.

Across the isolated bodies there are 3,252 proof-node occurrences and
3,252 distinct per-body proof objects. The largest body has 147 nodes;
the largest depth is 53. No proof, public-job, catalogue, or compiler limit
has been raised.

The five dedicated test files cover all 51 positive body checks, poisoned
conclusions, removed guards and sum witnesses, exact independent AST
contracts, full-context binder capture, empty domains, negative values,
distinct signed representatives, and actual CRT-encoded beta permutations.
Model tests are independent arithmetic diagnostics, not proof authority.
The large-numeral AST comparison uses an iterative structural comparison
in tests; it does not change Python recursion limits or any kernel code.

Each test module also has a `--body NAME` CLI. From `peano-lab/py`:

```
PYTHONPATH=. PYTHONMALLOC=malloc PYTHONDONTWRITEBYTECODE=1 \
  python3 -u tests/test_divisor_sum_reindex_candidate.py
```

The body CLI retains 170/175-second CPU limits, a 180-second wall alarm and
the 1,536-MiB peak-RSS assertion. The final combined run, under those same
limits, passed **460/460 tests in 38.32 seconds** (38.4496 seconds including
the runner), with exit status zero and peak RSS **461,357,056 bytes**.
That run includes all 51 actual original-kernel candidate-body checks.

The independently reconstructed 21-row Möbius-value/prime-step checkpoint
already has a separate original-kernel and compiled-Lean acceptance:
`artifacts/bottom-layer-mobius-values-proof-bundle-v1.json` relative to this
RFC directory, 237 bundle nodes, 675 edges, 15,134 body occurrences,
813,004 bytes, SHA-256
`041f1a3471002ff3cd5fc3da2a6cc751ad2f4a4458a497b3de2a26276fd314b8`.
That checkpoint does not assert cancellation or inversion. A later complete
51-row closure belongs in its own independently checked local receipt;
these candidate bodies and hashes are not a substitute for it.

## 6. Frozen source and test pins

| Stem | Candidate source SHA-256 | Dedicated test SHA-256 |
| --- | --- | --- |
| `mobius_value_candidate` | `18cc5aef4d4710a09bd8f2eac063ae2ccf54049a68eaab33d6b9ce7df87af9e0` | `a33c5d30284cae89b8c83d4fd12472ec2f948da9fe3e9753d569372d22b1ca5f` |
| `mobius_prime_step_candidate` | `f6fe75aa8e5c899baff761edea21dc82a3b76ea52ef165511d20f34a6d332af7` | `1e840973f90b2b357cf01e72823008584f57c666e531e127de0fd7e08a1fcb00` |
| `divisor_sum_table_candidate` | `011980a3d5857c123e97359e048bb7f5b9e35685fb9d1357d1d543c4ff9d7692` | `5601cf02666425a2ef591fb902b064a07d2e46ad2a63424e5663de033822710e` |
| `divisor_sum_algebra_candidate` | `38cdcf7229cb43001f658bded3434d53b54efee3b28067f634e1f39af61a6c92` | `f7aeddfb8623271114c55a3129ad8d62ccbf8ae75330657b5b722415f0c02d78` |
| `divisor_sum_reindex_candidate` | `e652ac90350d01c0ec6e4bbb7405950db316f35ff24fba3d019e1bc0c21d1ab4` | `e719df9bbc16e6f193464383b8ee4c0213a84189d06213bd4f54b2cbb24dc58f` |

## 7. Exact remaining G007 work

1. Construct a finite signed table whose value at positive `d|n` is the
   independently defined `Mobius(d)`, and whose other entries are zero.
   The table must be built by actual finite beta extension.
2. For `n>1`, construct a prime `p|n` and the actual bounded divisor map
   which toggles one occurrence of `p`. Divisors containing `p²`, zero,
   and nondivisors contribute zero and may be fixed. Prove map
   functionality, bounds and involution, including actual quotient
   witnesses for its division branch.
3. Combine that map with the proved fresh-prime negation and signed-sum
   permutation theorem to prove the cancellation identity. Separately
   prove the exact positive-unit result at `n=1`.
4. Construct finite weighted divisor tables and prove the required finite
   double-sum interchange/distributive convolution identity. No infinite
   sum or assumed ring/choice operation is available.
5. Apply the original hypothesis at every required positive quotient
   `m≤N`, proved from actual `n=d*m` witnesses. Only after this weighted
   identity is checked may the final witness be chosen as the existing
   table `h=f`.

Those stages are intentionally not marked completed by the present
foundation count or its independently checked prefix.
