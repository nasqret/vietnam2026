# RFC HA-R6-BERTRAND-CENTRAL-2: cap-safe central upper bounds

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
`97745559f57958c4c0c9cc966e73758d58d71731`

**Object language:** unchanged first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

This RFC freezes the six-row, capacity-safe proof of the elementary central
coefficient bounds needed by the Primorial argument. The words **must**,
**must not**, **should**, and **may** are normative.

## 1. Scope and non-claims

This tranche proves:

1. a pure arithmetic step preserving the strong factor-two bound;
2. one shared package containing the central recurrence and functional
   double-middle law;
3. the conditional and public bounds
   `2 * CentralBinom(S n) <= 4^(S n)`; and
4. the odd-middle estimate `Choose(2n+1,n) <= 4^n`.

It does not prove `primorial_le_four_pow`, the B5 five-range upper bound,
B7, B8, BP01, or BP02. It does not enroll a row or grant checked use.

## 2. Exact provider and source seals

Stable arithmetic is the only public authority. Candidate support must be
rebuilt from the exact source bytes below, in dependency order. Alpha
membership and old receipts are not authority.

```text
bertrand_choose_foundation_candidate.py
97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d
bertrand_choose_row_functional_candidate.py
dc1e9262e80090c304011728eb651690400b26b535cbf77d42b77c2a2e0f0edf
bertrand_choose_table_row_functional_candidate.py
379319daec74ad2e6b89b0808f885b87f6cc1a3fab4908559511d26f51be35f5
bertrand_choose_laws_candidate.py
1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d
bertrand_choose_diagonal_candidate.py
96044d1bf4e10dfffba3f9f7482c4fd9ff1f94fffbccac9fe45af32a32a691bc
bertrand_choose_recurrence_candidate.py
8b4a65b18e6a97a89c3f714686f2c690afb49f82ab56ed9575e3f673f50093c5
bertrand_choose_pascal_candidate.py
e96ee1d140beece2666b901dc7d671743b01386f110628b0957aeff01b9c26c3
bertrand_choose_symmetry_candidate.py
9958068fc364ca4bd171e965283a7683d167dcd6650e7a8df13f0b27c1edb78a
bertrand_choose_weighted_vertical_candidate.py
e8629d085ccb2d69acb179ce2bcede5612edf290a39dac175476574f9ce76bd1
bertrand_central_binom_candidate.py
c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e
bertrand_central_binom_zero_candidate.py
978dbdbdfe2fa68a5e0db91bbf895517028c66ec5956571fd7c15d0993c52e04
bertrand_central_binom_succ_candidate.py
c0faea72fbe7c21ada1f15adc91dec324e0fa643bde464c9b10f9a75df4f2b27
bertrand_integer_envelope_candidate.py
8f0967c2680f4f2e9c8c693df6f405a60a61decd8dd1cb52c2ca1b611b4fdfc1
bertrand_quotient_budget_candidate.py
78dbb7c472eb10861bbe39ec150f1499198a43c5f3687781c2e104e96516f225
bertrand_power_bridge_candidate.py
a5f9a60e680adab7cb290835a62a0359550dd773861e152ebb2615b2dcc637ab
```

The new source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_central_binom_upper_candidate.py
5bfea8dc2427bf60be8115c6b8cfb8e6a81d4c1bfb0ce65b695cdb065281247a
```

The focused-test seal remains pending until all fail-closed receipts are
measured. Any source change invalidates this seal and every receipt.

## 3. Exact relation spellings and tags

`Central(n,c)` abbreviates the already frozen raw
`Choose(n+n,n,c)` expansion. `Choose`, `Pow`, and `Le` are likewise fully
expanded before parsing. The public occurrence tags are:

```text
central_binom_strong_upper_step
  bcbsus_source, bcbsus_result
central_binom_recurrence_double_bundle
  bcbrdb_predecessor, bcbrdb_successor, bcbrdb_middle
central_binom_strong_upper_of_laws
  bcbrdb_predecessor, bcbrdb_successor, bcbsuo_exists,
  bcbsuo_central, bcbsuo_power, bcbsuo_result
central_binom_upper_support_package
  the exact bundle and existence occurrences above
central_binom_strong_upper
  bcbsuo_central, bcbsuo_power, bcbsuo_result
central_binom_odd_middle_le_four_pow
  bcomlfp_middle, bcomlfp_power, bcomlfp_result
```

Tags affect generated binder names only; the focused test must independently
rebuild and compare both source strings and parsed closed formulas.

## 4. Exact row order, surfaces, and dependencies

### 4.1 `central_binom_strong_upper_step`

```text
forall n c d q r.
  Le(2*c,q) ->
  S n*d = (2*S(n+n))*c ->
  r = q*4 ->
  Le(2*d,r)
```

Dependencies, in exact order:

```text
zero_add, add_succ_left, add_assoc, mul_comm, mul_assoc,
two_mul_eq_add_self, mul_le_mul_left, mul_le_mul_right, le_trans,
succ_ne_zero, mul_le_cancel_left_nonzero
```

The proof must scale the source bound, align the recurrence coefficients,
cancel only the nonzero factor `S n`, double the resulting inequality, and
align `2*(2*q)` with `q*4`. Large-context `congr` and `simp` are forbidden.

### 4.2 `central_binom_recurrence_double_bundle`

```text
(forall n c d.
   Central(n,c) -> Central(S n,d) ->
   S n*d = (2*S(n+n))*c)
/\
(forall n d m.
   Central(S n,d) -> Choose(S(n+n),n,m) -> d=m+m)
```

Dependencies, in exact order:

```text
mul_add, mul_assoc, two_mul_eq_add_self,
central_binom_succ_double_middle, choose_weighted_vertical,
choose_functional
```

The recurrence is rebuilt directly from double-middle plus weighted vertical.
The second conjunct uses the existing double-middle witness and functionality.

### 4.3 `central_binom_strong_upper_of_laws`

```text
Recurrence ->
(forall n. exists c. Central(n,c)) ->
forall n c q.
  Central(S n,c) -> Pow(4,S n,q) -> Le(2*c,q)
```

Dependencies, in exact order:

```text
one_mul, le_refl, pow_zero, pow_successor_decompose,
central_binom_zero, central_binom_strong_upper_step
```

The induction is generalized in `c,q`. Its base computes `C(2,1)=2` and
`4^1=4`; its step uses only predecessor existence, power decomposition,
the induction hypothesis, the supplied recurrence, and row 1.

### 4.4 `central_binom_upper_support_package`

```text
(Recurrence /\ DoubleMiddleFunctional)
/\
(forall n. exists c. Central(n,c))
```

Dependencies, in exact order:

```text
central_binom_recurrence_double_bundle, central_binom_exists
```

### 4.5 `central_binom_strong_upper`

```text
forall n c q.
  Central(S n,c) -> Pow(4,S n,q) -> Le(2*c,q)
```

Dependencies, in exact order:

```text
central_binom_upper_support_package,
central_binom_strong_upper_of_laws
```

This wrapper must apply the conditional theorem before introducing its public
quantifiers, avoiding a `forall`-after-implication inference ambiguity.

### 4.6 `central_binom_odd_middle_le_four_pow`

```text
forall n m q.
  Choose(S(n+n),n,m) -> Pow(4,n,q) -> Le(m,q)
```

Dependencies, in exact order:

```text
mul_add, mul_assoc, mul_comm, two_mul_eq_add_self,
mul_le_cancel_left_nonzero, pow_successor_compose,
central_binom_upper_support_package,
central_binom_strong_upper_of_laws
```

The proof obtains the successor central value from the package, uses the
functional double-middle law, composes the successor power, applies the
conditional strong bound, and cancels the literal nonzero factor `4`.

The direct-Cut vector is exactly `(11, 6, 6, 2, 2, 8)`, for 35 live edges.

## 5. Capacity architecture

The recurrence closure and double-middle closure are too large to import
independently into every client. Row 2 closes their shared graph once; row 4
adds central existence once; rows 5 and 6 consume the package plus the small
conditional induction.

Pre-freeze measurements are:

```text
central_binom_recurrence_double_bundle       307954 occurrences
central_binom_upper_support_package          397462 occurrences
central_binom_strong_upper                   405112 occurrences
central_binom_odd_middle_le_four_pow          471772 occurrences
```

Every final body and empty-context closure must pass the unchanged bounded
envelope, live node/object/depth limits, five-million annotation cap, and
no-DNE check. The 500000-occurrence limit must not be raised.

## 6. Fail-closed evidence gates

The focused test must:

1. pin every executed candidate source and this RFC;
2. rebuild support from Stable plus exact dependency prefixes only;
3. exclude Alpha membership, prior receipts, central recurrence candidates,
   positivity, factorial, Primorial, and B6 rows as authority;
4. freeze exact statement, script, dependency, body, envelope, and closure
   receipts for all six rows;
5. reject every one of the 35 dependency removals;
6. reject `(statement) /\ false` for every row;
7. reject one genuine semantic mutation per row;
8. kernel-check bodies and closures before receipt comparison;
9. reject DNE and enforce unchanged resource caps; and
10. assert direct Cuts `(11,6,6,2,2,8)` and corrupt every Cut before accepting
    a closure receipt.

Receipt values are fail-closed: an absent value must fail, never skip.

## 7. Genuine mutations

The required counterfixtures use standard binomial and power values:

1. row 1 strengthens the result to `Le(S(2*d),r)`; the all-zero fixture at
   `n=0` refutes it;
2. row 2 changes `d=m+m` to `d=S(m+m)`; `n=0,d=2,m=1` refutes it;
3. row 3 strengthens its strong-bound result by one; `n=0,c=2,q=4`
   refutes it;
4. row 4 applies the same false successor mutation inside the bundled
   double-middle conjunct;
5. row 5 strengthens `Le(2*c,q)` by one at `n=0,c=2,q=4`; and
6. row 6 strengthens `Le(m,q)` by one at `n=0,m=q=1`.

Commuted products, reassociated products, tag changes, and equivalent row
spellings are not genuine mutations.

## 8. Release disposition

After focused evidence is frozen, these six rows remain candidate evidence.
They may enter a later additive Alpha microbatch as `body_checked` only,
preserving the Alpha-v10 prefix exactly. Empty-context checked use and Stable
promotion are separate dependency-closed release decisions.

The next B4 client should combine rows 5 and 6 with the already proved even
and odd Primorial-interval divisibility bounds, then close
`primorial_le_four_pow`. The B5 range factorization remains a distinct front.
