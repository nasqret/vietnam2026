# Strict HA number-theory campaign — L2/L3 plan

## Objective and controlling blueprint

Build a cumulative library of elementary number theory whose public authority
is an empty-context certificate accepted by Peano Lab's intuitionistic
first-order checker.  The controlling research blueprint is frozen in
[`research/arithmetic-library/ha-number-theory-formalization-campaign-blueprint.md`](../research/arithmetic-library/ha-number-theory-formalization-campaign-blueprint.md),
dated 2026-08-03, 1,308 lines, 77,809 bytes, with SHA-256
`8fd25fc3e68259e1a16c935d35dacccefa20a473cdec35f8771cb1d5d806f205`.

The implementation baseline is commit
`d9d6e739e7c452ddf2cc9013d8772dfb185ff44f`.  Later campaign manifests must
bind their own exact source commit; this planning digest is not theorem
authority.

## Reconciled starting point

The blueprint describes K0--K6 as foundational work packages.  The repository
does not start from zero:

- the normal kernel entry point is intuitionistic and rejects `DNE`;
- at the frozen campaign baseline, 384 public theorem specifications had
  self-contained, empty-context certificates; tranche 01 raises the live
  append-only registry to 393 without changing the first-247 model-v3 prefix;
- public results already include division/remainder existence and uniqueness,
  relational gcd, balanced Bezout, Gauss cancellation, Euclid's lemma, prime
  divisors, factorization, FTA, modular-inverse existence, and binary CRT;
- a separate candidate corpus contains useful dependency-curried proof bodies,
  but body checking is not admission;
- defined notation expands hygienically to the unchanged language
  `{0,S,+,*,=}` and is checked by exact AST comparison.

Therefore the campaign reuses closed HA certificates but does not silently
identify every old representation with the new canonical interface.  The
first work is bridge construction and release packaging, not a second proof of
the same arithmetic facts.

## Status vocabulary

Every theorem uses exactly one evidence status:

| Status | Meaning |
|---|---|
| `public_checked` | Complete dependency closure checks from the empty context with the intuitionistic checker and the theorem is deliberately enrolled in the public registry. |
| `closed_checked_candidate` | A complete empty-context certificate checks, but deliberate public-registry admission has not occurred. |
| `body_checked_candidate` | The dependency-curried proof body checks; dependencies remain hypotheses. |
| `planned` | Statement and dependency location are frozen, but no accepted proof body exists. |
| `blocked_on_dependency` | Work cannot begin honestly until a named earlier layer closes. |
| `legacy_late_encoding` | Checked material may be reused later, but cannot serve as the campaign's foundational representation. |

No documentation label, theorem name, hash, host theorem, or candidate receipt
upgrades a theorem to `public_checked`.

Package-level planning is deliberately separate. A layer is
`existing_public_core`, `candidate_seed`, `new`, or
`blocked_on_dependency`. `existing_public_core` means that substantial
reusable public evidence exists; it does not mean that every target named by
the package is complete.

## Non-negotiable representation decisions

1. `Dvd(d,n)` retains the witness formula `exists k. n = d*k`.
2. Positive modular arithmetic uses balanced-natural congruence first, then a
   proved bridge to equality of canonical remainders. Totality and any theorem
   lacking a supplied remainder witness state a nonzero/positive modulus
   explicitly. A `Rem(m,n,r)` premise already contains `r<m`, which is accepted
   as strictly stronger boundary evidence and makes a duplicate `m != 0`
   premise unnecessary.
3. Existing factor-pair `Prime(p)` is retained as a legacy surface until it is
   proved equivalent to the campaign's bounded divisor characterization.
4. Existing `IsGCD` and `Coprime` remain relations.  A canonical gcd interface
   requires explicit existence, uniqueness, and compatibility theorems.
5. Signed quantities use the `HA-K3-SIGNED-1` parity-interleaved canonical
   code: `2*p` represents `+p`, while `2*k+1` represents `-(k+1)`. This has one
   zero and no negative zero. The representation is frozen before signed
   Bezout coefficients are exposed as data.
6. `BetaAt`, beta folds, and beta-coded factor lists are
   `legacy_late_encoding`.  They do not satisfy K3.  The initial pair/list/map
   substrate must be constructed independently of CRT; beta coding may later
   be recovered as a theorem and interoperability layer.
7. A convenient definition is only an elaborator macro until its expansion,
   totality/functionality where relevant, and elimination receipt have passed.

## Dependency-ordered implementation layers

```text
HA0 trust/profile + campaign manifests
  |
  +--> HA1 canonical remainder --------> HA2 canonical congruence
  |                                          |
  +--> HA3 canonical gcd/sign bridges -------+
  |                                          |
  +--> HA4 independent pair/list/map coding  |
                                             v
                                      M1 modular inverse
                                             |
                                             v
                                      M2 linear congruences
                                             |
                                             v
                                      M3 canonical binary CRT
                                             |
                              +--------------+--------------+
                              v                             v
                      M4 finite CRT              M5 generalized CRT
```

### HA0 — trust and release profile

- [x] Confirm that `check` is intuitionistic and `check_classical` is a
      separate entry point.
- [x] Confirm that candidate-body replay is not an admission receipt.
- [x] Freeze a machine-readable campaign/layer manifest.
- [x] Validate unique IDs, acyclic ordered dependencies, source paths, and
      allowed evidence statuses.
- [ ] Export a deterministic per-theorem statement/dependency/certificate
      manifest and induction footprint.
- [ ] Design a stable serialized certificate format and independent replay
      target; do not claim this gate from a second copy of the tactic engine.

### HA1 — canonical remainder relation

Use the expanded relation

```text
Rem(m,n,r) := (exists q. n=m*q+r) /\ r<m
```

with `m != 0` on totality statements.

- [x] Prove `canonical_remainder_exists` from
      `division_remainder_exists`.
- [x] Prove `canonical_remainder_functional` from
      `division_remainder_unique`.
- [x] Package `canonical_remainder_exists_unique` without adding `/` or `%`
      to the term language.
- [x] Record zero-modulus behavior separately rather than hiding it in the
      relation.

### HA2 — canonical congruence interface

- [x] Prove that two numbers with supplied canonical remainders are
      balanced-congruent iff those remainders are equal. Their bound witnesses
      rule out modulus zero, so this strongest bridge has no redundant premise.
- [x] Reuse `remainder_decomposition_to_mod_eq`,
      `mod_eq_to_remainder_decomposition`, and `mod_eq_bounded_unique` only
      through explicit checked dependencies.
- [ ] Freeze introduction, symmetry, transitivity, arithmetic transport,
      canonicalization, decision, and boundary rows in the relation API.

### HA3 — canonical gcd and signed bridges

- [x] Package relational gcd existence and `is_gcd_unique` as an
      existence-and-unique-value interface.
- [ ] Freeze gcd edge cases before exposing a computational graph.
- [x] Select a canonical sign-magnitude encoding with no negative zero in the
      reviewed `HA-K3-SIGNED-1` RFC.
- [x] Prove the division-free parity separation and the decoder constructors,
      totality, normality, functionality, zero characterization, and universal
      validity as deterministic empty-context candidates.
- [x] Prove total, extensional, functional balance normalization, its decoder
      bridge, and its exact zero characterization as deterministic
      empty-context candidates.
- [x] Prove the signed-negate decoder bridges, totality, functionality, zero,
      symmetry, and involution as deterministic empty-context candidates.
- [x] Prove the signed-add decoder/equation bridges, totality, and literal
      output functionality as deterministic empty-context candidates.
- [x] Prove the signed-add zero identities, commutativity, and both inverse
      orientations through the decoded contribution equation.
- [ ] Prove signed-add associativity through an independently reviewed
      cross-sum composition helper.
- [ ] Prove the signed multiply and natural-scale operation graph obligations
      frozen by that RFC.
- [ ] Translate four-natural balanced Bezout witnesses to and from the signed
      interface.
- [ ] Add lcm only after its zero convention and gcd compatibility statement
      are frozen.

### HA4 — independent finite-data substrate

- [ ] Write and review representation RFCs for pairs, lists, and finite maps
      that do not depend on CRT or beta coding. The independent signed-integer
      component is already selected by `HA-K3-SIGNED-1`.
- [ ] Prove pairing totality and projection functionality.
- [ ] Prove list validity, length, lookup, membership, append, restriction,
      and extension interfaces.
- [ ] Build finite sums, products, and cardinality on this substrate.
- [ ] Only after the substrate closes, prove interoperability with existing
      `BetaAt`/fold certificates.

### M1 — canonical modular inverse criterion

- [x] M1.1 reuse and admit the bounded-inverse uniqueness body only after its
      complete closure and mutation gates pass.
- [x] M1.2 canonicalize `coprime_mod_inverse` to obtain an inverse `u<m`.
- [x] M1.3 prove that an inverse implies `Coprime(a,m)` constructively.
- [x] M1.4 package the exact iff plus unique bounded witness for `m>0`.

M1.1--M1.4 and their HA1/HA2 dependencies are now `public_checked` as the
nine-entry append-only tranche-01 admission. The exact M1 root still checks at
9,512 structural nodes, depth 70, 2,538 distinct proof objects, and 126 unique
`Cut` nodes. Its content-stable DAG certificate SHA-256 is
`c3ed07e7caef52895001332d066ae9e4ce25167c7a0cd7189f8957c9aa7dc9f3`.

### M2 — linear congruences

- [ ] Prove solvability of `a*x == b (mod m)` iff `gcd(a,m)` divides `b`.
- [ ] Give a canonical base solution and exact solution-class description.
- [ ] Treat `m=0` explicitly and test all boundary cases.

### M3 — canonical binary CRT

- [ ] Canonicalize the existing `binary_crt` witness to `x<m*n`.
- [ ] Prove bounded uniqueness for coprime positive moduli.
- [ ] Publish the exact Appendix-A statement only after both directions close.

### M4/M5 — finite and generalized CRT

- [ ] Build finite CRT by induction over the independent list substrate.
- [ ] Prove the generalized compatibility criterion for non-coprime moduli.
- [ ] Supply canonical solutions and obstruction certificates.

## Per-theorem validation gates

Each new theorem advances through these gates in order:

1. **Statement:** parse a closed base-language formula; record exact AST digest.
2. **Body:** replay the tactic body with ordered dependencies introduced as
   ordinary hypotheses.
3. **Topology:** reject unknown, duplicate, cyclic, forward, and unused
   dependency declarations as required by the layer policy.
4. **Candidate closure:** close every dependency through self-contained proof
   sharing, check from the empty context with `check`, and record
   `closed_checked_candidate` without mutating the public registry.
5. **Adversarial:** reject a nearby false statement, dependency mutation, and
   every certificate containing `DNE`.
6. **Defined edition:** expand every named predicate and typed `have`/`suffices`
   proposition; require exact expanded AST identity.
7. **Public admission:** deliberately enroll the theorem, then replay it through
   the public path and recheck registry/catalog ordering.
8. **Integration:** regenerate snapshots, vault, book, and explorers from
   source; never hand-edit generated theorem pages.

Large closure, mutation, and clean-room gates run on WMI.  Statement, body,
topology, and narrow replay tests should remain fast enough to run after every
small layer on a laptop.

## First implementation tranche

- [x] Land and validate the campaign manifest and definition freeze.
- [x] Land the isolated HA1 remainder candidate module and focused tests.
- [x] Land the isolated HA2 remainder/congruence bridge and focused tests.
- [x] Record existing M1 bounded-uniqueness as a candidate seed before
      admission.
- [x] Run the narrow kernel/defined-edition/foundational admission suite.
- [x] Update memory and journal only with observed receipts.
- [x] Admit the exact nine factory specifications atomically at public tail
      positions 384--392 and retain their isolated receipt provenance.
- [x] Migrate the QR graph's one exact-compatible overlap,
      `bounded_mod_inverse_unique`, from candidate scope to public scope while
      preserving factory provenance and rejecting incompatible collisions.

The tranche ends with reviewed, empty-context-checked and deliberately public
HA1, HA2, and M1 interfaces. The runtime contains 393 public theorems. The QR
closure remains 557 nodes and 1,787 edges, now partitioned as 241 public and
316 candidates; no QR root admission follows from this migration.

## Second implementation tranche

- [x] Close `canonical_gcd_exists`, `canonical_gcd_functional`, and
      `canonical_gcd_exists_unique` from the empty context without DNE.
- [x] Pin their exact statement hashes, proof metrics, Cut counts, and
      content-stable certificate hashes in the campaign manifest.
- [x] Keep all three outside the public registry pending a separate admission
      review.
- [x] Select and freeze the parity-interleaved signed-natural representation,
      eight exact base-language graph templates, dependency prohibitions, and
      staged proof obligations in
      [`ha-canonical-signed-natural-rfc-v1.md`](../research/arithmetic-library/ha-canonical-signed-natural-rfc-v1.md).
- [x] Prove the K1-only parity-separation lemma required by the signed decoder;
      the existing `even_odd_exclusive_pointwise` is not foundationally usable
      because it depends on division uniqueness.
- [x] Prove signed decoder constructors, totality, normality, functionality,
      zero characterization, and universal validity in the RFC's dependency
      order; retain all nine parity/decoder results as closed candidates.
- [x] Prove `SignedBalance` totality and functionality, its decoder transport,
      cross-sum extensionality, and zero bridge before any signed arithmetic
      graph; retain all six normalization results as closed candidates.
- [x] Prove the three decoded-code extensionality results culminating in
      `signed_code_eq_iff_balance`; retain them as closed candidates.
- [x] Begin the signed arithmetic graph strictly with negation totality,
      functionality, decoder semantics, zero, symmetry, and involution; retain
      all eight results as closed candidates.
- [x] Build the five-row `SignedAdd` core from decoded contribution sums plus
      `SignedBalance`; retain its decoder bridges, totality, and functionality
      as closed candidates without bypassing normalization with host integers.
- [ ] Complete the `SignedAdd` algebraic-law tranche before starting
      `SignedMul`.

## Release boundary

The first named campaign release is **Euclidean and Modular Arithmetic in
HA**.  It requires HA0--HA3 and M1--M3 to be `public_checked`; M4/M5 may form a
second release if the independent list substrate is not ready.  Quadratic
reciprocity, FTA, or any beta-coded result already present in the repository
does not waive these canonical-interface gates.
