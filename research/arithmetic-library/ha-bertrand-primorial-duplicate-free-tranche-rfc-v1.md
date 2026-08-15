# RFC HA-R6-BERTRAND-PRIMORIAL-4: duplicate-free product comparison

**Status:** binding subordinate statement, dependency, evidence, trust,
capacity, and release contract; no theorem is enrolled or admitted by this
document

**Parent campaign:**
[`RFC HA-R6-BERTRAND-1`](ha-bertrand-postulate-campaign-rfc-v1.md), SHA-256
`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`

**Representation amendment:**
[`RFC HA-R6-BERTRAND-2`](ha-bertrand-postulate-campaign-rfc-v2.md), SHA-256
`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`

**Primorial foundation contract:**
[`RFC HA-R6-BERTRAND-PRIMORIAL-1`](ha-bertrand-primorial-foundation-tranche-rfc-v1.md),
SHA-256
`c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89`

**Primorial membership contract:**
[`RFC HA-R6-BERTRAND-PRIMORIAL-2`](ha-bertrand-primorial-membership-tranche-rfc-v1.md),
SHA-256
`4f569e76c68aa486fd1f1415491a5a3d678a75c239aa72ebd707d67fedde0df5`

**Immutable edition parent:** Alpha v10 at commit
`1888aef98eb8cb6e421122e165ed938f7d5e03ef`

**Object language:** unchanged first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

This RFC freezes the ten-row B4 microbatch required by Section 11.4 of the
Primorial foundation contract. It introduces explicit pairwise value
distinctness for beta-coded prefixes, proves that a distinct prime product
divides any common multiple of its factors, and specializes the result to
the dense `Primorial` relation.

The words **must**, **must not**, **should**, and **may** are normative. The
campaign RFCs control endpoint, trust, and release policy. This document
controls the ten names, order, surfaces, tags, dependencies, proof topology,
and focused evidence gates below.

## 1. Scope and non-claims

This tranche supplies:

1. empty, successor, restriction, last-entry, and recoding laws for an
   explicit pairwise-distinct beta prefix;
2. coprimality of the last distinct prime with the preceding product;
3. divisibility of a distinct prime product into a common multiple;
4. pointwise and aggregate specialization to bounded Primorial factors; and
5. the required numeric comparison with Primorial.

It completes the duplicate-free comparison deliverable of B4. It does
**not** prove the elementary central-binomial upper bounds,
`primorial_le_four_pow`, any B5 five-range inequality, B7, B8, BP01, or BP02.
It creates no Alpha membership, checked-use grant, Stable membership, or
publication by itself.

## 2. Bound parent edition and provider bytes

The sole edition parent is the sealed Alpha-v10 snapshot at commit
`1888aef98eb8cb6e421122e165ed938f7d5e03ef`:

- theorem count: `1085`;
- declared direct-edge count: `3306`;
- dependency-layer count: `45`;
- Stable count: `432`;
- Alpha-only count: `653`;
- checked-use count: `570`;
- evidence counts: `432 stable_closed`, `138 alpha_closed`,
  `514 body_checked`, and `1 pending_layered_closure`;
- ordered enrollment root:
  `c016d13d555f31c0fabf61e236f9012ac60bf50e2e66210d398d7bc049672b4f`;
- ordered specification root:
  `6ab70321b61bea288df325ffa433c992d0559e9546324583066b4f767249df46`;
- edition identity:
  `1e4376021508ac6913770ac18eca8c1406c7b298d7e381f994510c6854baa98d`;
- membership root:
  `01ec76832d511806302056f2f823b2d8c45c477cf92d826bfae28197f1656013`;
- evidence root:
  `a00e426172d93e9c9254d97ec2295031873dd02fc97a003eb4824cc22b64e81a`;
- channel-pointer root:
  `f2c2760dd275b94572e0ab5a5cc4837fc1e884ea26ea00a55074caa84a4d8f6e`;
- catalog SHA-256:
  `46bd50c19b694470542f53f1ef7f61d1ee8fab1f08ad5573ca3534da29053dc3`;
- metrics SHA-256:
  `63044f59aeb6fd84fbe57e26f8358676e679e15ef7456f1823db68bc255703de`;
- dependency-graph SHA-256:
  `92e1519ae42a80b0755df32cb6fcc6e74887bb09f99a8908129a829a6d461ac3`;
  and
- channels SHA-256:
  `644fb72833d66f30b2194a5d493935f31bae716edb4c76afcb8c6e272399eca2`.

The exact providers are pinned at:

```text
peano-lab/py/peano_lab/library/theorems.py
05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919

peano-lab/py/peano_lab/library/finite_fold_surface.py
95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30

peano-lab/py/peano_lab/library/fermat_residue_product_candidate.py
b43a6fa9be64b806d9973abfb0d566533910c8a841fba16777b8a9498b98d59d

peano-lab/py/peano_lab/library/bertrand_primorial_foundation_candidate.py
70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98

peano-lab/py/peano_lab/library/bertrand_primorial_membership_candidate.py
edf14adde5edbbc6b7836003a174ee9a4b84f708fdcd0f3c3af45fc5013ac817
```

Only `beta_product_pointwise_coprime`, the second row of the Fermat provider,
is permitted from that candidate module. It must be recursively rebuilt from
its exact source and Stable dependencies. Its Alpha membership and any prior
receipt are not authority.

The new source is frozen at:

```text
peano-lab/py/peano_lab/library/bertrand_primorial_duplicate_free_candidate.py
2367c77427d86fb9cd99f3335d383b655580b29822bcfd161f76c023f71446fc
```

The focused-test byte seal remains pending until all fail-closed receipts are
measured. Any source change requires this RFC and every pin to be updated.

## 3. Exact representation

The inherited `Prime`, `BetaAt`, `Product`, and `Primorial` surfaces retain
their earlier fully expanded meanings. New authoring abbreviations are:

```text
AllPrime(b,c,l) :=
  forall i. Lt(i,l) ->
    exists p. BetaAt(b,c,i,p) /\ Prime(p)

Distinct(b,c,l) :=
  forall i j p q.
    Lt(i,l) -> Lt(j,l) ->
    BetaAt(b,c,i,p) -> BetaAt(b,c,j,q) ->
    ~(i=j) -> ~(p=q)

PointwiseLe(b,c,l,m) :=
  forall i p. Lt(i,l) -> BetaAt(b,c,i,p) -> Le(p,m)

PointwiseDivides(b,c,l,z) :=
  forall i p. Lt(i,l) -> BetaAt(b,c,i,p) -> Dvd(p,z)
```

`Distinct` is pairwise value distinctness, not weak adjacent `Sorted`.
No list, set, filter, Product, Prime, or Primorial primitive is added to the
parser or kernel.

## 4. Frozen occurrence tags

| Row | Public occurrence tags |
|---|---|
| `beta_distinct_empty` | `bpdf_empty` |
| `beta_distinct_succ_intro` | `bpdfsi_prefix`, `bpdfsi_last`, |
| | `bpdfsi_prior`, `bpdfsi_result` |
| `beta_distinct_succ_elim_prefix` | `bpdfsep_source`, |
| | `bpdfsep_result` |
| `beta_distinct_succ_last_ne` | `bpdfsln_distinct`, |
| | `bpdfsln_bound`, `bpdfsln_left`, `bpdfsln_right` |
| `beta_distinct_transport` | `bpdft_source`, `bpdft_source_entry`, |
| | `bpdft_target_entry`, `bpdft_result` |
| `beta_distinct_prime_product_coprime_last` | `bpdfcp_primes`, |
| | `bpdfcp_distinct`, `bpdfcp_product`, `bpdfcp_last`, |
| | `bpdfcp_result` |
| `beta_distinct_prime_product_divides_common_multiple` | `bpdfdcm_primes`, |
| | `bpdfdcm_distinct`, `bpdfdcm_pointwise`, `bpdfdcm_product`, |
| | `bpdfdcm_result` |
| `beta_bounded_prime_prefix_divides_primorial_pointwise` | |
| | `bpbpdp_primorial`, `bpbpdp_primes`, `bpbpdp_bounds`, |
| | `bpbpdp_result` |
| `beta_distinct_bounded_prime_product_divides_primorial` | |
| | `bpdfbdp_primorial`, `bpdfbdp_primes`, `bpdfbdp_distinct`, |
| | `bpdfbdp_bounds`, `bpdfbdp_product`, `bpdfbdp_result` |
| `beta_distinct_bounded_prime_product_le_primorial` | |
| | `bpdfblp_primorial`, `bpdfblp_primes`, `bpdfblp_distinct`, |
| | `bpdfblp_bounds`, `bpdfblp_product`, `bpdfblp_result` |

Private proof tags may extend these stems but must be collision-safe.

## 5. Exact theorem order, surfaces, and dependencies

Every dependency tuple below is ordered and immutable.

1. `beta_distinct_empty`

   ```text
   forall b c. Distinct(b,c,0)
   ```

   Dependencies: `add_eq_zero_right`, `succ_ne_zero`.

2. `beta_distinct_succ_intro`

   ```text
   forall b c l p.
     Distinct(b,c,l) -> BetaAt(b,c,l,p) ->
     (forall i q. Lt(i,l) -> BetaAt(b,c,i,q) -> ~(q=p)) ->
     Distinct(b,c,S l)
   ```

   Dependencies: `le_of_succ_le_succ`, `le_eq_or_lt`, `beta_at_unique`.

3. `beta_distinct_succ_elim_prefix`

   ```text
   forall b c l. Distinct(b,c,S l) -> Distinct(b,c,l)
   ```

   Dependency: `le_succ`.

4. `beta_distinct_succ_last_ne`

   ```text
   forall b c l i p q.
     Distinct(b,c,S l) -> Lt(i,l) ->
     BetaAt(b,c,i,p) -> BetaAt(b,c,l,q) -> ~(p=q)
   ```

   Dependencies: `le_succ`, `le_refl`, `lt_irrefl_expanded`.

5. `beta_distinct_transport`

   ```text
   forall b c d e l.
     Distinct(b,c,l) ->
     (forall i p. Lt(i,l) ->
       BetaAt(b,c,i,p) -> BetaAt(d,e,i,p)) ->
     Distinct(d,e,l)
   ```

   Dependencies: `beta_at_exists`, `beta_at_unique`.

6. `beta_distinct_prime_product_coprime_last`

   ```text
   forall b c l r p.
     AllPrime(b,c,S l) -> Distinct(b,c,S l) ->
     Product(b,c,l,r) -> BetaAt(b,c,l,p) -> Coprime(r,p)
   ```

   Dependencies: `le_succ`, `le_refl`, `beta_at_unique`,
   `distinct_primes_coprime`, `beta_product_pointwise_coprime`,
   `beta_distinct_succ_last_ne`.

7. `beta_distinct_prime_product_divides_common_multiple`

   ```text
   forall b c l n z.
     AllPrime(b,c,l) -> Distinct(b,c,l) ->
     PointwiseDivides(b,c,l,z) -> Product(b,c,l,n) -> Dvd(n,z)
   ```

   Dependencies: `beta_product_zero`, `beta_product_succ_decompose`,
   `le_succ`, `le_refl`, `one_multiple`, `coprime_product_is_lcm`,
   `beta_distinct_succ_elim_prefix`,
   `beta_distinct_prime_product_coprime_last`.

8. `beta_bounded_prime_prefix_divides_primorial_pointwise`

   ```text
   forall m z b c l.
     Primorial(m,z) -> AllPrime(b,c,l) -> PointwiseLe(b,c,l,m) ->
     PointwiseDivides(b,c,l,z)
   ```

   Dependencies: `beta_at_unique`, `primorial_prime_divides_of_le`.

9. `beta_distinct_bounded_prime_product_divides_primorial`

   ```text
   forall m z b c l n.
     Primorial(m,z) -> AllPrime(b,c,l) -> Distinct(b,c,l) ->
     PointwiseLe(b,c,l,m) -> Product(b,c,l,n) -> Dvd(n,z)
   ```

   Dependencies:
   `beta_bounded_prime_prefix_divides_primorial_pointwise`,
   `beta_distinct_prime_product_divides_common_multiple`.

10. `beta_distinct_bounded_prime_product_le_primorial`

    ```text
    forall m z b c l n.
      Primorial(m,z) -> AllPrime(b,c,l) -> Distinct(b,c,l) ->
      PointwiseLe(b,c,l,m) -> Product(b,c,l,n) -> Le(n,z)
    ```

    Dependencies: `divisor_le_nonzero`, `primorial_positive`,
    `beta_distinct_bounded_prime_product_divides_primorial`.

The exact direct-edge count is `32`. The direct-`Cut` vector is:

```text
(2, 3, 1, 3, 2, 6, 8, 2, 2, 3)
```

Every edge must be independently live.

## 6. Required proof topology

1. Row 1 closes the impossible empty-prefix bound constructively.
2. Row 2 splits each successor-bounded index into terminal or prior form,
   uses beta uniqueness only in mixed branches, and invokes the supplied
   freshness premise or old distinctness as appropriate.
3. Row 3 weakens both index bounds with `le_succ` and otherwise preserves
   the source proof.
4. Row 4 specializes the distinctness premise at `i,l`, proves `i!=l` from
   strict irreflexivity, and consumes the resulting value inequality.
5. Row 5 obtains source entries with `beta_at_exists`, maps them forward,
   aligns values with target beta uniqueness, and reflects source
   distinctness. No beta-code equality is asserted.
6. Row 6 derives primality of the last and each prefix factor from
   `AllPrime`, aligns decoded values with beta uniqueness, obtains factorwise
   coprimality from distinct primes, and invokes the recursively rebuilt
   `beta_product_pointwise_coprime` exactly once.
7. Row 7 inducts on product length. The step decomposes Product once, applies
   the induction hypothesis to the prefix, gets the last-factor divisor,
   proves prefix/last coprimality with row 6, and uses the least-common-
   multiple property of a coprime product.
8. Row 8 aligns the `AllPrime` witness with the requested decoded factor and
   applies the checked Primorial membership direction.
9. Row 9 constructs the pointwise premise with row 8 and applies row 7.
10. Row 10 combines row 9 with Primorial positivity and the checked nonzero
    divisor bound.

Every eliminated existential must come from an inferable theorem or
hypothesis application. DNE, classical choice, weak `Sorted` as a substitute
for distinctness, raw beta-code equality, and any B5/B7/B8/BP01/BP02 theorem
are forbidden.

## 7. Focused evidence and authority boundary

One focused fail-closed test must independently reconstruct all public and
proof-local formulas and compare exact names, order, statements, tags,
scripts, summaries, and dependencies.

For each row, authority is exactly:

1. Stable checked-use theorems;
2. the recursively rebuilt pinned Primorial foundation and membership rows;
3. the recursively rebuilt pinned `beta_product_pointwise_coprime`; and
4. the earlier local prefix of this tranche.

Alpha-v10 membership, prior body or closure receipts, later siblings,
arbitrary provider scans, and all excluded campaign endpoints are not
authority.

Each row requires concrete artifact, body, bounded-envelope, and independent
empty-context closure receipts. The closure gates must kernel-check, enforce
the current caps, reject DNE, verify the exact Cut count, and corrupt every
direct Cut before receipt comparison.

## 8. Liveness and semantic mutations

All `32` edges must be live and every target must reject conjunction with
`false`. One unique-substring, counterfixture-backed mutation is required per
row. The minimum semantic set is:

1. strengthen empty distinctness to claim two decoded values at index zero
   are unequal;
2. remove the terminal freshness premise at a one-element prefix with a
   repeated value;
3. strengthen the restricted length from `l` to `S l`;
4. replace the last index `l` by a prior index `i`;
5. shift the transported target value from `p` to `S p`;
6. drop distinctness, using the repeated prime list `[2,2]`;
7. drop distinctness, with product `4` and common multiple `2`;
8. strengthen the pointwise result divisor from `p` to `S p` at `p=2`;
9. reverse the final divisibility at the bounded product `2` and Primorial
   value `6`; and
10. strengthen `Le(n,z)` to `Le(S n,z)` at equality.

Alpha-equivalent binder changes, commuted products, or other true statements
do not count.

## 9. Capacity and release policy

The unchanged campaign limits are:

- `4096` candidate-body proof nodes;
- `65536` candidate-body edges;
- `500000` empty-context proof occurrences;
- `100000` distinct empty-context proof objects;
- proof and envelope depth `256`; and
- `5000000` annotation occurrences.

The recursive `beta_product_pointwise_coprime`, row 7, and the Primorial
membership closure are the principal risks. Receipts must be measured
serially in fresh processes; limits may not be raised.

After all gates and an independent audit pass, an additive Alpha successor
may enroll the ten rows only as:

```text
membership = alpha_only
evidence = body_checked
checked_use = false
proof_tag = null
empty_context_closure = null
```

Stable remains unchanged. Focused closure evidence does not itself grant
checked use or Stable membership.

## 10. Acceptance checklist

- [ ] parent roots, RFC hashes, provider hashes, source hash, and test hash
      reproduce exactly;
- [ ] all ten surfaces, tags, scripts, descriptions, and ordered dependency
      tuples reproduce exactly;
- [ ] all `32` edge removals, ten false targets, and ten genuine mutations
      fail closed;
- [ ] bodies, envelopes, and closures pass kernel, caps, and no-DNE gates;
- [ ] Cuts are exactly `(2, 3, 1, 3, 2, 6, 8, 2, 2, 3)` and every Cut
      corruption is rejected before receipt comparison;
- [ ] only `beta_product_pointwise_coprime` is admitted from the pinned
      candidate provider;
- [ ] there is no Alpha/Stable/provider authority leakage; and
- [ ] Alpha-v1 through Alpha-v10 and Stable remain byte-identical.

Passing this checklist establishes only the duplicate-free product
comparison tranche. It does not prove `primorial_le_four_pow` or Bertrand's
postulate.
