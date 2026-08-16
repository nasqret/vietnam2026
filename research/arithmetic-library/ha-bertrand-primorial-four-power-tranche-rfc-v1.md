# RFC HA-R6-BERTRAND-PRIMORIAL-5: the four-power Primorial bound

**Status:** binding subordinate statement, dependency, evidence, trust,
capacity, and release contract; this document grants no theorem authority

**Parent campaign:**
[`RFC HA-R6-BERTRAND-1`](ha-bertrand-postulate-campaign-rfc-v1.md), SHA-256
`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`

**Representation amendment:**
[`RFC HA-R6-BERTRAND-2`](ha-bertrand-postulate-campaign-rfc-v2.md), SHA-256
`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`

**Immutable edition parent:** Alpha v10 at commit
`1888aef98eb8cb6e421122e165ed938f7d5e03ef`

**Candidate parent:** commit
`ccb8e167df7c0db4d9de6fee6de745da18aba719`

**Object language:** unchanged first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

This RFC freezes the seven-row B4 capstone proving the inclusive Primorial
bound `Primorial(n,z) -> Pow(4,n,q) -> Le(z,q)`. The words **must**,
**must not**, **should**, and **may** are normative.

## 1. Scope and non-claims

This tranche proves:

1. the exact one-row Primorial boundary;
2. two small half-index bounds used by the parity split;
3. a generic nonzero form of the strong central-binomial upper bound;
4. one package containing the large interval and coefficient laws;
5. a bounded-induction form of the Primorial estimate; and
6. the public `primorial_le_four_pow` theorem.

It completes the numeric upper-bound requirement of B4. It does not prove
the B5 five-range factorization, B7, B8, BP01, or BP02. It does not enroll a
row or grant checked use.

## 2. Exact source seals

Candidate support must be rebuilt from exact source bytes in dependency
order. Alpha membership and old closure receipts are never proof authority.

```text
bertrand_primorial_foundation_candidate.py
70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98
bertrand_primorial_membership_candidate.py
edf14adde5edbbc6b7836003a174ee9a4b84f708fdcd0f3c3af45fc5013ac817
bertrand_primorial_interval_candidate.py
02e59e0f7addcae3bb127271ddeaa6728c5dab1dee096a878fced278065c10a3
bertrand_primorial_choose_interval_candidate.py
5442a23447d87f3452b6fdb4fa44093063047592127707abcdc0defc29b4ac09
bertrand_central_binom_upper_candidate.py
5bfea8dc2427bf60be8115c6b8cfb8e6a81d4c1bfb0ce65b695cdb065281247a
bertrand_integer_envelope_candidate.py
8f0967c2680f4f2e9c8c693df6f405a60a61decd8dd1cb52c2ca1b611b4fdfc1
bertrand_power_order_candidate.py
50b07e3b40b81966a37bc07cbb44b93498a86efa76aabcbb4af94b17c1eb17e6
```

The new source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_primorial_four_power_candidate.py
86c0bfa4e5840c35d0ea6a0bf443dedd159c298b21ee6345d1cdc0d5c6ede2f3
```

The focused-test seal remains pending until all fail-closed receipts are
measured. Any source change invalidates the source seal and every receipt.

## 3. Exact relation spellings and tags

`Primorial`, `PrimorialInterval`, `CentralBinom`, `Choose`, `Pow`, and `Le`
are authoring-only abbreviations fully expanded before parsing. The public
occurrence tags are:

```text
primorial_one
  bpo_source
double_half_predecessor_data
  bdhpb_result
odd_positive_prefix_predecessor_bound
  boppb_result
central_binom_nonzero_strong_upper
  bcnzsu_central, bcnzsu_power, bcnzsu_result
primorial_four_power_support_package
  bpfpsp_central_exists, bpfpsp_choose_exists,
  bpfpsp_split_source, bpfpsp_split_prefix, bpfpsp_split_interval,
  bpfpsp_even_interval, bpfpsp_even_central, bpfpsp_even_result,
  bpfpsp_odd_interval, bpfpsp_odd_middle, bpfpsp_odd_result,
  bpfpsp_odd_upper_middle, bpfpsp_odd_upper_power,
  bpfpsp_odd_upper_result
primorial_le_four_pow_bounded
  bplfpb_index, bplfpb_primorial, bplfpb_power, bplfpb_result
primorial_le_four_pow
  bplfp_primorial, bplfp_power, bplfp_result
```

Private proof formulas use only subordinate collision-safe tags. The focused
test must rebuild public strings and parsed closed formulas independently.

## 4. Exact row order, surfaces, and dependencies

### 4.1 `primorial_one`

```text
forall z. Primorial(1,z) -> z=1
```

Dependencies: `primorial_zero`, `primorial_succ_decompose`.

The proof must decompose the successor Primorial and handle the two selector
arms directly. It must not eliminate a constructed existential.

### 4.2 `double_half_predecessor_data`

```text
forall n k. S n=2*k -> (~(k=0) /\ Le(k,n))
```

Dependencies: `two_mul_eq_add_self`, `add_succ_left`.

The proof structurally splits `k`; the zero case is impossible and the
successor case constructs the weak-bound witness directly.

### 4.3 `odd_positive_prefix_predecessor_bound`

```text
forall n k.
  S n=2*k+1 -> (exists h. k=S h) -> Le(S k,n)
```

Dependencies: `two_mul_eq_add_self`, `add_succ_left`.

The proof structurally splits `k`; the zero branch contradicts the supplied
successor witness and the successor branch constructs the bound.

### 4.4 `central_binom_nonzero_strong_upper`

```text
forall n c q.
  ~(n=0) -> CentralBinom(n,c) -> Pow(4,n,q) -> Le(2*c,q)
```

Dependency: `central_binom_strong_upper`.

The proof inducts on `n` before introducing the remaining binders. This is
the only permitted carrier alignment; no whole expanded Central or Pow
relation rewrite is allowed.

### 4.5 `primorial_four_power_support_package`

The package is the exact right-associated conjunction of:

```text
forall n. exists c. CentralBinom(n,c)
forall n k. exists c. Choose(n,k,c)
forall a l z.
  Primorial(a+l,z) ->
  exists x y. Primorial(a,x) /\
    (PrimorialInterval(a,l,y) /\ z=x*y)
forall n z c.
  PrimorialInterval(n,n,z) -> CentralBinom(n,c) -> Le(z,c)
forall n z c.
  PrimorialInterval(S n,n,z) ->
  Choose(S(n+n),n,c) -> Le(z,c)
forall n c q.
  Choose(S(n+n),n,c) -> Pow(4,n,q) -> Le(c,q)
```

Dependencies, in exact order:

```text
central_binom_exists, choose_exists,
primorial_prefix_interval_split,
primorial_even_interval_le_central,
primorial_odd_interval_le_middle,
central_binom_odd_middle_le_four_pow
```

### 4.6 `primorial_le_four_pow_bounded`

```text
SupportPackage ->
forall N n z q.
  Le(n,N) -> Primorial(n,z) -> Pow(4,n,q) -> Le(z,q)
```

Dependencies, in exact order:

```text
le_zero, le_eq_or_lt, le_of_succ_le_succ, zero_or_succ,
le_refl, le_add_right, le_trans, mul_le_mul,
two_mul_eq_add_self, add_succ_left, parity_cases,
pow_exists, pow_zero, pow_one, pow_add,
primorial_index_eq_transport, primorial_zero, primorial_one,
double_half_predecessor_data,
odd_positive_prefix_predecessor_bound,
central_binom_nonzero_strong_upper
```

The induction is on `N`, generalized in `n,z,q`. In the successor boundary:

1. `parity_cases` writes `n=2*k` or `n=2*k+1`;
2. the even branch splits `Primorial(k+k)`, applies the induction hypothesis
   to the prefix, bounds the interval by the central coefficient, applies the
   nonzero strong bound, and recombines with `mul_le_mul` and `pow_add`;
3. the odd zero-half branch uses `primorial_one` and `pow_one`; and
4. the positive odd branch splits `Primorial(S k+k)`, bounds its prefix by
   induction and its interval by the checked odd-middle estimate, then
   recombines with `mul_le_mul` and `pow_add`.

Only `primorial_index_eq_transport` may transport a whole expanded relation.
No Central, Choose, interval, or Pow relation is rewritten wholesale.

### 4.7 `primorial_le_four_pow`

```text
forall n z q. Primorial(n,z) -> Pow(4,n,q) -> Le(z,q)
```

Dependencies, in exact order:

```text
le_refl, primorial_four_power_support_package,
primorial_le_four_pow_bounded
```

The wrapper must first build the universal bounded law from the conditional
row, then specialize it at the reflexive bound.

The direct-Cut vector is exactly `(2,2,2,1,6,21,3)`, for 37 live edges.

## 5. Capacity architecture

The support package imports multiple large candidate lineages, while the
public theorem also consumes the 303-command bounded induction. Naive
recursive Cut expansion duplicates those lineages and is not an acceptable
certificate architecture.

The focused empty-context evidence must use root-pruned `LayeredReplay` over
exact candidate bodies and checked Stable leaves. Candidate bodies must be
kernel-checked before interning, and the final layered proof must be checked
again by the unchanged kernel. No previous body or closure receipt is theorem
authority. The unchanged limits remain:

```text
proof occurrences       500000
proof objects            100000
proof/envelope depth     256
annotation occurrences  5000000
```

Run each expensive root in a fresh process. Parallel closure workers and cap
raises are forbidden.

## 6. Fail-closed evidence gates

The focused test must:

1. pin every executed candidate source and this RFC;
2. rebuild support from Stable plus exact dependency prefixes only;
3. exclude Alpha membership, registry mutation, and prior receipts;
4. freeze exact statement, script, dependency, body, envelope, and layered
   closure receipts for all seven rows;
5. reject every one of the 37 dependency removals;
6. reject `(statement) /\ false` for every row;
7. reject one genuine semantic mutation per row;
8. kernel-check bodies and closures before receipt comparison;
9. reject DNE and enforce the unchanged resource limits; and
10. assert the direct root-dependency vector `(2,2,2,1,6,21,3)` and corrupt
    every direct root dependency edge before accepting a layered closure
    receipt.

Receipt values are fail-closed: an absent value must fail, never skip.

## 7. Genuine mutations and counterfixtures

The required semantic mutations are:

1. `primorial_one` changes `z=1` to `z=0`; `Primorial(1)=1` refutes it;
2. row 2 changes `Le(k,n)` to `Le(S k,n)`; `n=1,k=1` satisfies
   `S n=2*k` but not the stronger bound;
3. row 3 changes `Le(S k,n)` to `Le(S(S k),n)`; `n=2,k=1` refutes it;
4. row 4 strengthens the result to `Le(S(2*c),q)` at `n=1,c=2,q=4`;
5. row 5 strengthens its odd-upper result by one at `n=0,c=q=1`;
6. row 6 changes the final result to `Le(S z,q)` at
   `N=n=0,z=q=1`; and
7. row 7 makes the same successor strengthening at `n=0,z=q=1`.

Equivalent reassociations, commuted products, tag changes, and reversed
equalities are not genuine mutations.

## 8. Release disposition

After evidence is frozen, these rows remain candidate evidence. They may be
added to a later Alpha microbatch as `body_checked` while preserving the
Alpha-v10 prefix exactly. Empty-context checked use and Stable promotion are
separate dependency-closed decisions.

The next mathematical front is B5: connect the central coefficient to the
five explicit prime ranges under the no-Bertrand-prime hypothesis.
