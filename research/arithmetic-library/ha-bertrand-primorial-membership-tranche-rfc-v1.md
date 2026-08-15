# RFC HA-R6-BERTRAND-PRIMORIAL-2: membership and monotonicity

**Status:** binding subordinate statement, dependency, evidence, trust,
capacity, and release contract; no theorem is enrolled or admitted by this
document

**Parent campaign:**
[`RFC HA-R6-BERTRAND-1`](ha-bertrand-postulate-campaign-rfc-v1.md), SHA-256
`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`

**Representation amendment:**
[`RFC HA-R6-BERTRAND-2`](ha-bertrand-postulate-campaign-rfc-v2.md), SHA-256
`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`

**Foundation contract:**
[`RFC HA-R6-BERTRAND-PRIMORIAL-1`](ha-bertrand-primorial-foundation-tranche-rfc-v1.md),
SHA-256
`c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89`

**Committed foundation parent:** commit
`dfb267391a1058679231e181f57fb52eb51fa788`

**Immutable edition parent:** Alpha v8 at commit
`06274fbe3c4e20281cd904f3e1dd1a6f36ed4544`

**Object language:** unchanged first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

This RFC freezes the eleven-row B4 microbatch immediately after the filtered
primorial foundation. It proves both directions of prime divisibility,
packages their exact equivalence, and derives one-step, additive-length, and
ordered-bound divisibility together with a positive quotient and numeric
monotonicity.

The words **must**, **must not**, **should**, and **may** are normative. In a
conflict, the campaign RFCs control the endpoint, logic, trust, and promotion
policy; the foundation RFC controls `Sel`, `FactorPrefix`, and `Primorial`;
this document controls the eleven row names, binder order, statement
association, occurrence tags, order, direct dependencies, proof topology,
and subordinate evidence gates.

## 1. Scope and non-claims

This tranche supplies:

1. equality transport for the length argument of `Primorial`;
2. a selector-level characterization of a prime divisor of one selected
   factor;
3. both directions and the exact conjunction form of
   `Prime(p) -> (p | Primorial(m)) <-> p <= m`;
4. a selected factor and a divisibility witness for one primorial step;
5. divisibility across an additive length and across an arbitrary `Le`
   bound; and
6. constructive positive quotients and numeric monotonicity.

This tranche completes the prime-divisibility characterization requested by
Section 11.1 of the foundation RFC and the basic monotonicity requested by
Section 11.2. It does **not** complete B4. It supplies no filtered interval
product, prefix/suffix split, duplicate-free external-product comparison, or
`primorial_le_four_pow`. It establishes no B5, B7, B8, BP01, or BP02 edge.

The document creates no Alpha membership, checked-use grant, Stable
membership, publication, or deployment. `Prime`, `Sel`, `FactorPrefix`,
`Primorial`, `Lt`, `Le`, and divisibility notation below are authoring
notation only and must be expanded into the unchanged first-order language
before parsing.

## 2. Bound parents and immutable authority

The committed foundation evidence is bound by all of the following:

- foundation commit:
  `dfb267391a1058679231e181f57fb52eb51fa788`;
- foundation candidate source SHA-256:
  `70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98`;
- foundation focused-test SHA-256:
  `a4b270e209f7f68652c54926e5cd3e38a44baa42b2a969d4dc602c6b08fac0e1`;
  and
- foundation RFC SHA-256:
  `c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89`.

The sole edition parent is the sealed Alpha-v8 snapshot at commit
`06274fbe3c4e20281cd904f3e1dd1a6f36ed4544`:

- theorem count: `1055`;
- declared direct-edge count: `3224`;
- dependency-layer count: `45`;
- checked-use count: `570`;
- evidence counts: `432 stable_closed`, `138 alpha_closed`,
  `484 body_checked`, and `1 pending_layered_closure`;
- ordered enrollment root:
  `a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2`;
- ordered specification root:
  `fe49d664e5a88f6637c7790b104e9b0aa3c583e48f9a4a1405d5b098f7f61df9`;
- edition identity:
  `2101b7b384ec9791c41d07d8115123d6842729615a0084ce87cead619bc8c123`;
- membership root:
  `4471bdcf06a2d3af866850b39f394a436ad608b4c0b166c0449620e5dd3c9ee3`;
- evidence root:
  `4230c17701be2c604ea413be90c26bad41889d593dcaaeff311217b4e26367b4`;
- channel-pointer root:
  `1fd2216e0448fbeb0d8da60dea3b89fca4d4f7192371fc87a8c5cd35dccf3c70`;
- Alpha catalog artifact SHA-256:
  `c06c5fde7b84b4a8524dd408a2b046d06c7a88ccb5814877b7ccfec0d20b1370`;
- Alpha metrics artifact SHA-256:
  `90c14911ef50391dd9fd99865a83a6e0886911253504096a30e497d30c1a6813`;
- Alpha graph artifact SHA-256:
  `ff194534f1efd56dd771237b6a44279a705309df21c1fa319b6669f3e1cab008`;
  and
- channel artifact SHA-256:
  `dec01b10ee9359b1f7057187725016d343bfb7f3176d8779c85da7f26983234d`.

No implementation may edit any Alpha-v1 through Alpha-v8 or Stable ledger,
artifact, root, pointer, canonical position, origin, or evidence record.
Stable v1 remains the unchanged 432-row checked edition and default channel.
Alpha membership and `body_checked` evidence are not theorem authority.

Every external dependency in Section 5 must come from Stable checked-use
authority. The ten committed foundation rows must be rebuilt from their
pinned source and closed recursively when used; their committed candidate
receipts do not grant authority. Candidate-only product-order and
prefix/suffix-splitting rows are explicitly outside this dependency graph.

## 3. Inherited representation and exact notation

The representation is inherited byte-for-byte in logical content from the
foundation RFC:

```text
Prime(q) :=
  ~(q = 1) /\
  forall a d. q = a * d -> a = 1 \/ d = 1

Sel(i,a) :=
  (Prime(S i) /\ a = S i) \/
  (~Prime(S i) /\ a = 1)

FactorPrefix(b,c,m) :=
  forall i. Lt(i,m) ->
    exists a. BetaAt(b,c,i,a) /\ Sel(i,a)

Primorial(m,z) :=
  exists b c.
    FactorPrefix(b,c,m) /\ Product(b,c,m,z)
```

For readability only, the displayed surfaces use:

```text
Dvd(p,z) := exists q. z = p * q
```

Every theorem surface in Section 5 freezes the expanded existential shown
there; `Dvd` is not a new predicate or parser symbol. `Le` and `Lt` retain
their existing expanded HA definitions. All connectives, quantifiers,
`Prime`, `Sel`, `Primorial`, `Le`, `Lt`, `BetaAt`, and `Product` must be
expanded hygienically before parsing.

Private builders must accept term syntax through an explicit variable
context, parse and pretty-print the term AST, and generate binders that avoid
all free and owned names. Unchecked substitution, implicit free names, and a
new primitive predicate are forbidden.

The dense selector is intentional. Because candidate `1` contributes a
neutral factor, a `FactorPrefix` is not an `AllPrime` prefix. Therefore the
existing `beta_prime_divisor_product_member` theorem is not applicable to
row 4. The stable `euclid_prime_dvd_product` theorem is sufficient; no new
generic Product or Euclid theorem is authorized by this RFC.

## 4. Frozen occurrence tags and pending byte seals

The following tags are binding inputs to the independent hygienic builders:

| Row | Frozen occurrence tags |
|---|---|
| `primorial_index_eq_transport` | `bpmit_source`, `bpmit_target` |
| `primorial_factor_choice_prime_divisor_eq` | `bpfcpde_prime`, |
| | `bpfcpde_choice`, `bpfcpde_divides` |
| `primorial_prime_divides_of_le` | `bppdol_prime`, `bppdol_bound`, |
| | `bppdol_source`, `bppdol_result` |
| `primorial_prime_le_of_divides` | `bpplod_prime`, `bpplod_source`, |
| | `bpplod_divides`, `bpplod_result` |
| `primorial_prime_divides_iff_le` | `bppdil_prime`, `bppdil_source`, |
| | `bppdil_divides_left`, `bppdil_bound_left`, |
| | `bppdil_bound_right`, `bppdil_divides_right` |
| `primorial_succ_factor` | `bpsf_before`, `bpsf_after`, `bpsf_factor` |
| `primorial_succ_divides` | `bpsd_before`, `bpsd_after`, `bpsd_result` |
| `primorial_add_length_divides` | `bpald_before`, `bpald_after`, |
| | `bpald_result` |
| `primorial_le_divides` | `bpld_index_bound`, `bpld_before`, |
| | `bpld_after`, `bpld_result` |
| `primorial_le_positive_quotient` | `bplpq_index_bound`, |
| | `bplpq_before`, `bplpq_after` |
| `primorial_le_monotone` | `bplm_index_bound`, `bplm_before`, |
| | `bplm_after`, `bplm_result` |

The logical contract and tags are binding now. The candidate source and
focused test are expected at:

```text
peano-lab/py/peano_lab/library/bertrand_primorial_membership_candidate.py
peano-lab/py/tests/test_bertrand_primorial_membership_candidate.py
```

Their source hashes, expanded statement hashes, tactic-script hashes,
artifact tuples, body/envelope receipts, and closure receipts are pending
the landed implementation and its fail-closed evidence run. This RFC does
not invent or pre-authorize those byte seals. Once reviewed evidence records
them, changing any name, binder order, association, tag, direct dependency,
statement, or tactic command requires a versioned successor contract.

## 5. Exact theorem order, surfaces, and direct dependencies

The order below is immutable. Each direct dependency tuple is ordered.

1. `primorial_index_eq_transport`

   ```text
   forall n m z.
     n = m -> Primorial(n,z) -> Primorial(m,z)
   ```

   Direct dependencies: none.

2. `primorial_factor_choice_prime_divisor_eq`

   ```text
   forall i a p.
     Prime(p) -> Sel(i,a) ->
     (exists q. a = p * q) -> p = S i
   ```

   Direct dependencies, in exact order:
   `divisor_one`, `prime_divisor_eq_one_or_self`.

3. `primorial_prime_divides_of_le`

   ```text
   forall p m z.
     Prime(p) -> Le(p,m) -> Primorial(m,z) ->
     exists q. z = p * q
   ```

   Direct dependencies, in exact order:
   `prime_is_succ_succ`, `beta_factor_divides_product`.

4. `primorial_prime_le_of_divides`

   ```text
   forall p m z.
     Prime(p) -> Primorial(m,z) ->
     (exists q. z = p * q) -> Le(p,m)
   ```

   Direct dependencies, in exact order:
   `divisor_one`, `le_refl`, `le_succ`,
   `euclid_prime_dvd_product`, `primorial_zero`,
   `primorial_succ_decompose`,
   `primorial_factor_choice_prime_divisor_eq`.

5. `primorial_prime_divides_iff_le`

   ```text
   forall p m z.
     Prime(p) -> Primorial(m,z) ->
     (((exists q. z = p * q) -> Le(p,m)) /\
      (Le(p,m) -> exists q. z = p * q))
   ```

   The association and orientation are binding: `Dvd -> Le` is the left
   conjunct and `Le -> Dvd` is the right conjunct.

   Direct dependencies, in exact order:
   `primorial_prime_le_of_divides`, `primorial_prime_divides_of_le`.

6. `primorial_succ_factor`

   ```text
   forall m x y.
     Primorial(m,x) -> Primorial(S m,y) ->
     exists p. Sel(m,p) /\ y = x * p
   ```

   Direct dependencies, in exact order:
   `primorial_succ_decompose`, `primorial_functional`.

7. `primorial_succ_divides`

   ```text
   forall m x y.
     Primorial(m,x) -> Primorial(S m,y) ->
     exists q. y = x * q
   ```

   Direct dependencies, in exact order:
   `primorial_succ_factor`.

8. `primorial_add_length_divides`

   ```text
   forall g m x y.
     Primorial(m,x) -> Primorial(g + m,y) ->
     exists q. y = x * q
   ```

   Direct dependencies, in exact order:
   `zero_add`, `add_succ_left`, `primorial_index_eq_transport`,
   `primorial_functional`, `multiple_refl`, `primorial_exists`,
   `primorial_succ_divides`, `multiple_trans`.

9. `primorial_le_divides`

   ```text
   forall m n x y.
     Le(m,n) -> Primorial(m,x) -> Primorial(n,y) ->
     exists q. y = x * q
   ```

   Direct dependencies, in exact order:
   `primorial_index_eq_transport`, `primorial_add_length_divides`.

10. `primorial_le_positive_quotient`

    ```text
    forall m n x y.
      Le(m,n) -> Primorial(m,x) -> Primorial(n,y) ->
      exists q. y = x * S q
    ```

    Direct dependencies, in exact order:
    `zero_or_succ`, `primorial_positive`, `primorial_le_divides`.

11. `primorial_le_monotone`

    ```text
    forall m n x y.
      Le(m,n) -> Primorial(m,x) -> Primorial(n,y) -> Le(x,y)
    ```

    Direct dependencies, in exact order:
    `primorial_le_positive_quotient`.

The exact direct-edge count is `30`. The exact direct-`Cut` vector in theorem
order is:

```text
(0, 2, 2, 7, 2, 2, 1, 8, 2, 3, 1)
```

No listed edge may be reordered or silently replaced by a transitive theorem.
Removing any listed edge must make the focused liveness gate fail.

## 6. Required proof topology

The following architecture is binding at the semantic review boundary:

1. Transport rewrites the equality on the expanded source `Primorial`
   exactly four times: once in the selected-prefix bound, twice in the
   terminal `BetaAt` modulus inside `Product`, and once in the Product bound.
   The rewrites must be scoped to the transported hypothesis.
2. The selector helper cases `Sel(i,a)`. In the prime branch it applies
   `prime_divisor_eq_one_or_self` and excludes `p = 1` from `Prime(p)`. In
   the neutral branch `divisor_one` forces `p = 1`, again contradicting
   `Prime(p)`. No Product theorem occurs in this row.
3. The forward membership row uses `prime_is_succ_succ` to write
   `p = S (S k)`, converts `Le(p,m)` to the in-range candidate index `S k`,
   and extracts the selected factor from `FactorPrefix`. It cases `Sel`
   locally, transports only the small decoded `BetaAt` fact, and applies
   `beta_factor_divides_product`. It must not assert that beta codes agree.
4. The reverse membership row inducts on `m` while generalizing `z`. At zero,
   `primorial_zero` reduces the divisibility premise to a divisor of `1`,
   and `divisor_one` contradicts primality. At `S m`,
   `primorial_succ_decompose` gives `z = r * a` and
   `euclid_prime_dvd_product` splits the divisor into the predecessor and
   terminal-factor cases. The former uses the induction hypothesis and
   `le_succ`; the latter uses row 2 and `le_refl`.
5. The equivalence row constructs the conjunction in its frozen orientation,
   applying row 4 to the left implication and row 3 to the right implication.
6. The successor-factor row decomposes the successor primorial, then uses
   `primorial_functional` to align its produced predecessor with the supplied
   `x`. Only the resulting small equality is rewritten.
7. The one-step divisibility row projects the selected factor from row 6 and
   returns it as the multiplication witness.
8. Additive-length divisibility inducts on `g`. The zero branch transports
   `Primorial(0 + m,y)` to length `m`, uses functionality, and closes with
   `multiple_refl`. The successor branch transports the target from
   `S g + m` to `S (g + m)` using `add_succ_left`, obtains an intermediate
   `Primorial(g + m,r)` from `primorial_exists`, applies the induction
   hypothesis and row 7, and composes the witnesses with `multiple_trans`.
9. Ordered-bound divisibility eliminates the `Le(m,n)` witness
   `g + m = n`, transports the target to length `g + m` with row 1, and
   applies row 8.
10. Positive quotient first obtains `y = x * q` from row 9 and cases
    `zero_or_succ q` directly. The zero case contradicts the successor witness
    supplied by `primorial_positive` for `y`; the successor case returns the
    existing predecessor of `q`. It must not build an eliminator-rooted
    existential and later case it.
11. Monotonicity obtains `y = x * S q` from row 10, uses `x * q` as the
    explicit `Le(x,y)` gap, and closes by the primitive multiplication
    successor equation.

All locally constructed values later eliminated must have an inferable proof
source. Whole-`Primorial` equality motives beyond row 1 are forbidden. The
proofs may not use DNE, choice, raw beta-code equality, a generic prime-list
membership oracle, or candidate-only Product order/split rows.

## 7. Focused evidence and authority boundary

The implementation must have one focused fail-closed test. It must rebuild
every expanded surface independently from pinned low-level helpers and must
compare exact names, order, statements, tags, tactic scripts, and direct
dependencies. Importing a production statement constant is not independent
evidence.

For each row, replay authority is exactly Stable plus the committed ten-row
foundation and the earlier local prefix from Section 5. Every foundation row
must be reconstructed from the pinned foundation source, not trusted from a
receipt or arbitrary provider scan. A row must not gain authority from:

- a later local sibling;
- Alpha membership alone;
- `body_checked` evidence;
- a statement, artifact, body, envelope, or closure receipt;
- candidate-only product-order or prefix/suffix-splitting rows; or
- any B5, B7, B8, BP01, or BP02 theorem.

Provider, Stable, Alpha, and edition-name collisions must fail closed. The
test must assert that none of the eleven names already occurs in the parent
edition or a production authority registry. It must pin every executed
provider file and the new source. The candidate module and test are evidence
providers, not theorem registries.

Before any possible enrollment, every row must have a concrete artifact:

```text
(statement_length,
 sha256(expanded_statement),
 sha256(NUL-joined tactic script),
 sha256(NUL-joined expanded statement and direct dependencies))
```

Each row must also have concrete body, proof-envelope, and independently
kernel-accepted empty-context closure receipts. A `None`, placeholder, stale
script hash, source hash substituted for a proof identity, or receipt
computed before a semantic gate is fail-closed.

## 8. Liveness, mutation, and kernel gates

All `30` direct edges must be live: removing each edge separately from its
exact row core must reject replay. Every target must reject conjunction with
`false`. Helper tests must cover invalid terms, invalid and reserved tags,
non-tuple and duplicate contexts, omitted free names, and generated-binder
capture.

At least one genuine, counterfixture-backed mutation is required per row.
The minimum boundary set includes:

1. shift the transport target from `m` to `S m`, refuted at length `1`;
2. strengthen `p = S i` to `p = S (S i)`, refuted by candidate `2`;
3. replace the divisor `p` in the result by `S p`, refuted by
   `p = m = z = 2`;
4. strengthen the result to `Le(S p,m)`, refuted by `p = m = 2`;
5. strengthen the left `Dvd -> Le` conjunct while preserving the frozen
   conjunction orientation, again refuted at the boundary prime `2`;
6. shift the selected successor factor from index `m` to `S m`, refuted by
   `Primorial(1,1)` and `Primorial(2,2)`;
7. require a double-successor quotient, refuted by the neutral step from
   `Primorial(0,1)` to `Primorial(1,1)`;
8. replace the divisibility result by `exists q. y = S x * q`, refuted in
   the equal-length zero case;
9. reverse the bound to `Le(n,m)`, refuted by `m = 2`, `n = 1`,
   `x = 2`, and `y = 1`;
10. require `y = x * S (S q)`, refuted at equal zero bounds where
    `x = y = 1`; and
11. strengthen `Le(x,y)` to `Le(S x,y)`, refuted at equal bounds.

Each replacement must identify a unique expanded substring before mutation.
Alpha renaming, equality reversal, a commutative rearrangement, or another
true theorem does not count as genuine mutation evidence.

For each empty-context closure, the gate must first enforce kernel
acceptance, current caps, and absence of DNE. It must then count the exact
outer direct-`Cut` spine from Section 5 and corrupt every direct `Cut`, in
dependency order. Every corruption must be kernel-rejected before the
closure receipt is compared.

## 9. Capacity and crash-safety contract

The current campaign limits remain unchanged:

- at most `4096` candidate proof nodes during body replay;
- at most `65536` candidate body edges;
- at most `500000` empty-context proof occurrences;
- at most `100000` distinct empty-context proof objects;
- maximum proof depth `256`; and
- at most `5000000` annotation occurrences.

The four scoped transports in row 1 and the additive induction in row 8 are
the principal capacity risks. The committed foundation's largest closure is
well below the candidate cap, but that is only a planning estimate. Exact
body, envelope, and closure receipts must be measured serially and frozen;
limits may not be raised to accept this tranche.

Run artifact, body, mutation, and closure selectors serially in fresh
processes with memory observed. A timeout does not cap resident memory.
Concurrent proof workers and a retained monolithic closure DAG are not
approved laptop gates. Formula and envelope traversal must be bounded before
unbounded diagnostics. Hashes are receipts, not semantic checks.

## 10. Evidence status and release sequencing

This RFC itself performs no enrollment. Candidate source and focused-test
seals remain pending until their exact bytes land and all gates pass. A
future body-only Alpha proposal, if separately authorized, must initially
record every row as:

```text
membership = alpha_only
evidence = body_checked
checked_use = false
proof_tag = null
empty_context_closure = null
```

Focused test success and a candidate empty-context closure do not grant
checked use, `alpha_closed`, or Stable membership. Any edition successor must
append without altering the 1055 Alpha-v8 rows, their order, provenance,
origins, evidence, roots, or artifacts. Stable promotion requires a separate
dependency-closed review and must preserve canonical Alpha positions.

The required release sequence is:

1. land this binding RFC alone or with no logical authority change;
2. land candidate source and an all-`None`, fail-closed focused test;
3. reproduce artifacts, bodies, envelopes, and independent closures in
   serial fresh processes;
4. freeze only exact measured receipts after all preceding gates pass;
5. obtain independent source, test, and release audits; and
6. propose any append-only enrollment in a separate change.

No step may infer authority from the existence of a candidate file or from a
green receipt test.

## 11. Required later B4 work

This tranche intentionally leaves the following dependency-ordered work:

1. an offset filtered-factor relation for candidates in an interval;
2. totality, functionality, and prefix/suffix splitting for that relation;
3. an explicit duplicate-free predicate for external prime-only products;
4. the theorem that every duplicate-free product of primes bounded by `m`
   divides `Primorial(m)`;
5. the resulting numeric product comparison using constructive positivity;
6. the elementary central-binomial upper support still required by B3/B4;
   and
7. `primorial_le_four_pow` with machine-rejected B7/B8/BP01/BP02 edges.

The dense selector contains neutral `1` entries, so later comparison code
must not silently substitute `AllPrime` for the required filtered semantics.
Candidate-only product order and split rows may be proposed in a later
binding tranche only with their own pinned bytes and evidence.

## 12. Acceptance checklist

The membership tranche is ready for a later body-only enrollment proposal
only when:

- [ ] every parent hash, foundation byte seal, Alpha-v8 count, and root
      matches Sections 1 and 2;
- [ ] the landed source and focused test fill every pending byte seal without
      changing Sections 3--6;
- [ ] all eleven expanded statements, scripts, tags, dependency tuples, and
      artifact identities reproduce exactly;
- [ ] all `30` dependency-removal tests, all false targets, all genuine
      mutations, and all hygiene/capture tests fail closed;
- [ ] all bodies, envelopes, and closures pass the intuitionistic kernel,
      current caps, and zero-DNE gate;
- [ ] the direct-`Cut` vector is exactly
      `(0, 2, 2, 7, 2, 2, 1, 8, 2, 3, 1)`, and every direct corruption is
      rejected before receipt comparison;
- [ ] candidate-only Product order/split rows and all B5/B7/B8/BP01/BP02
      edges are absent; and
- [ ] Alpha-v1 through Alpha-v8 and Stable artifacts remain byte-identical.

Passing this checklist establishes only the eleven-row candidate evidence.
It does not complete B4 and does not establish Bertrand's postulate.
