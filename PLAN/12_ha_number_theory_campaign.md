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
  self-contained, empty-context certificates; tranche 01 raised the registry
  to 393, the selective K4 gcd/LCM admission raised it to 409, and the
  selective M5 generalized-CRT admission now raises it to 432 without
  changing the first-247 model-v3 prefix;
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
- [x] Freeze and close-check the five canonical gcd zero/one/swap boundary
      rows before exposing a computational graph; keep them nonpublic.
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
- [x] Prove signed-add associativity through an independently reviewed
      cross-sum composition helper.
- [x] Prove the five-row `SignedMul` decoder/equation core, totality, and
      literal-output functionality as deterministic empty-context candidates.
- [x] Prove the complete D06 signed-multiplication graph and algebraic-law
      obligations frozen by that RFC, including associativity and both
      distributive orientations.
- [x] Prove the D07 natural-scale operation graph, its zero and one laws, and
      composition under natural multiplication as deterministic empty-context
      candidates.
- [x] Translate four-natural balanced Bezout witnesses to and from the signed
      interface.
- [x] Combine public relational-gcd and balanced-Bezout existence with the
      signed bridge as an explicitly K4, division-bearing client.
- [x] Freeze the literal-safe universal `IsLCM` relation, its forced zero
      convention, and the exact 17-row structural/edge API.
- [x] Close the nine-row constructive gcd--LCM ladder through compatible
      existence, relational LCM totality, unique LCM value, and
      `gcd_lcm_product`.
- [x] Admit exactly LCM rows L01--L07 and bridge rows A--I as the minimal
      useful K4 public surface; retain the other 19 reviewed K4 candidates
      privately.

### HA4 — independent finite-data substrate

- [x] Select the doubled-Cantor pair and successor-tagged cell representation
      in `HA-K3-PAIR-1`, independently of CRT and beta coding.
- [ ] Select an honest computation-trace representation before freezing a
      uniform variable-length `ListValid` or `ListAt`; pairing alone only
      supplies fixed-length generated schemas.
- [ ] Write and review the remaining list and finite-map RFCs. The independent
      signed-integer and pair/cell components are now selected.
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
- [x] Close the eight-row generalized-CRT congruence foundation: reuse the
      exact `mod_eq_add_cancel_left` candidate, add seven constructive rows,
      and prove both gcd-compatibility necessity and the incompatibility
      obstruction with zero DNE.
- [x] Prove the converse construction from compatibility modulo a relational
      gcd and close the necessary-and-sufficient noncoprime solvability
      criterion for two nonzero moduli in the seven-row M5a ladder.
- [x] Extend the binary criterion across zero input moduli without asserting a
      remainder below zero: the four-row M5b ladder closes the left-zero,
      right-zero, total-sufficiency, and all-modulus iff statements.
- [x] Describe the complete solution class modulo relational LCM: the four-row
      M5c ladder proves congruence modulo the LCM iff congruence modulo both
      inputs, then classifies every solution relative to one fixed solution.
- [x] Supply the three-row M5d canonical boundary: exact uniqueness at zero
      LCM, a unique bounded representative at nonzero LCM, and the honest
      all-modulus disjunction packaging both cases.
- [x] Close the two-row M5e executable boundary: decide balanced congruence at
      every modulus, then return compatibility plus a solution or certified
      incompatibility plus unsolvability.
- [x] Close the one-row M5f raw-input endpoint: construct an existential
      relational gcd from `m,n`, then return either gcd compatibility with a
      CRT solution or incompatibility with a proof that no solution exists.

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
- [x] Complete the `SignedAdd` algebraic-law tranche before starting
      `SignedMul`.
- [x] Close the five-row `SignedMul` core without using any SignedAdd law,
      host-integer multiplication, division, remainder, CRT, or beta coding.
- [x] Prove the elementary `SignedMul` zero, one, and commutative laws before
      attempting associativity or distributivity.
- [x] Prove `SignedMul` associativity and distributivity from independently
      reviewed decoded-equation composition lemmas.
- [x] Close the five-row direct `SignedNatScale` graph and its five-row
      zero/one/composition tranche without defining D07 as a D06 alias.
- [x] Close the four-row D08 balanced/signed Bezout bridge and its separate
      one-row division-bearing K4 signed-gcd client.
- [x] Freeze and close-check the five-row canonical-gcd edge tranche and the
      17-row literal-safe relational-LCM universal-property tranche.
- [x] Close rows A--I of the gcd--LCM totality bridge, including both branches
      of compatible existence, relational totality, unique value, and the
      arbitrary gcd--LCM product theorem.
- [x] Audit the independent pair/list route, freeze the pair/cell component,
      and record the missing uniform computation-history step rather than
      hiding variable iteration in a recursive macro.

The completed D06 tranche adds four associativity rows in
[`ha_signed_mul_associative_candidate.py`](../peano-lab/py/peano_lab/library/ha_signed_mul_associative_candidate.py)
and seven distributivity rows in
[`ha_signed_mul_distributive_candidate.py`](../peano-lab/py/peano_lab/library/ha_signed_mul_distributive_candidate.py).
Their focused audits are
[`test_ha_signed_mul_associative_candidate.py`](../peano-lab/py/tests/test_ha_signed_mul_associative_candidate.py)
and
[`test_ha_signed_mul_distributive_candidate.py`](../peano-lab/py/tests/test_ha_signed_mul_distributive_candidate.py).
The 11 new rows raise the isolated signed stack to 60 closed candidates and
the complete candidate corpus to 63 total candidates; together with the nine
deliberately public tranche-01 rows, the campaign now records 72 theorem
receipts. Two cold closures agree on the 60-row signed-stack digest
`7befb7ae830b866a606e47f674730959e76599ded863aadd9868b850bcb190cd`.
This changes neither the 393-entry public registry, the 45-row definition
freeze (44 distinct public theorem dependencies), nor the 394-entry catalog,
and grants no admission.

The completed D07 tranche adds five graph-core rows in
[`ha_signed_nat_scale_candidate.py`](../peano-lab/py/peano_lab/library/ha_signed_nat_scale_candidate.py)
and five laws/helpers in
[`ha_signed_nat_scale_laws_candidate.py`](../peano-lab/py/peano_lab/library/ha_signed_nat_scale_laws_candidate.py).
Their focused audits are
[`test_ha_signed_nat_scale_candidate.py`](../peano-lab/py/tests/test_ha_signed_nat_scale_candidate.py)
and
[`test_ha_signed_nat_scale_laws_candidate.py`](../peano-lab/py/tests/test_ha_signed_nat_scale_laws_candidate.py).
For decoded input `(ip,inn)` and output `(op,on)`, the exact graph is governed
by `scale * ip + on = scale * inn + op`. The law order is the generic
left-multiplication cross-sum transport, composition of two decoded scale
equations, scale zero, scale one, and finally graph composition:

```text
SignedNatScale(inner,input,middle) ->
SignedNatScale(outer,middle,output) ->
SignedNatScale(outer*inner,input,output).
```

The direct equation-composition helper keeps the proof on the D07 surface.
Defining D07 as the alias `SignedMul(2*scale,input,output)` was rejected: it
would introduce an avoidable D06/coercion dependency into the common Bezout
path and obscure the direct natural coefficient in the frozen D07 statement.
The core closes a 65-row signed stack with digest
`511aa0ba4a6dac1a22f52db740f539c675307b5b77b6b1a7d9ef2e00dd8a5331`;
all ten rows close a 70-row stack with digest
`81a18daf55e564c11dee83ce7465bc91876109a5e6bc092f75e0f31f46e27d8d`.
The campaign now has 70 signed and 73 total candidates, 82 theorem receipts,
15 K3 candidate modules, and 17 focused evidence tests. The public registry
remains 393 entries with 56 public references, the definition freeze remains
45 rows over 44 distinct public theorems, and the catalog remains 394 entries.
Nothing in D07 is admitted. The D08 `SignedBezout` bridge is the next
signed-arithmetic gate.

The completed D08 tranche adds four rows in
[`ha_signed_bezout_candidate.py`](../peano-lab/py/peano_lab/library/ha_signed_bezout_candidate.py),
audited by
[`test_ha_signed_bezout_candidate.py`](../peano-lab/py/tests/test_ha_signed_bezout_candidate.py).
The reusable transport row normalizes the raw pairs `(xp,xn)` and `(yp,yn)`
with `SignedBalance`, lifts both cross sums through natural multiplication,
and preserves the subtraction-free Bezout equation. The directional rows then
prove

```text
BalancedBezout(result,a,b) -> exists x y. SignedBezout(result,a,b,x,y)
SignedBezout(result,a,b,x,y) -> BalancedBezout(result,a,b)
```

and the endpoint packages both implications. The implementation explicitly
accounts for the legacy witness order `xp,yp,xn,yn` versus the D08 decoder
order `xp,xn,yp,yn`; canonical codes do not imply a unique Bezout coefficient
pair. Exact empty-context receipts for transport, forward conversion, reverse
conversion, and the packaged equivalence have respectively 943, 1,241, 35,
and 1,326 structural nodes. Two cold closures agree on the complete 74-row
signed-stack digest
`b7949148236ab243830a2bfebd80ddafeb31a63c5e70ace1c032de8bd2415f15`.
The campaign now has 74 signed and 77 total candidates, 86 theorem receipts,
16 K3 candidate modules, and 18 focused evidence tests. The closure reaches
no division, remainder, CRT, beta, classical, or DNE theorem. The public
registry remains 393 entries with 56 public references, the definition freeze
remains 45 rows over 44 distinct public theorems, and the catalog remains 394
entries. Nothing in D08 is admitted. A `gcd_signed_bezout_exists` client is
deliberately deferred to K4 because its public gcd dependency reaches
division; it is not part of the strict K3 closure.

The next isolated K4 row, `gcd_signed_bezout_exists`, now performs exactly
that composition in
[`ha_signed_bezout_gcd_candidate.py`](../peano-lab/py/peano_lab/library/ha_signed_bezout_gcd_candidate.py),
with a focused audit in
[`test_ha_signed_bezout_gcd_candidate.py`](../peano-lab/py/tests/test_ha_signed_bezout_gcd_candidate.py).
It produces a relational gcd `d` and canonical signed codes `x,y` satisfying
`SignedBezout(d,a,b,x,y)`. Its empty-context certificate has 3,535 nodes,
depth 48, 1,734 DAG objects, 1,824 edges, 91 reused references, and 74 Cuts,
with SHA-256
`4edeb4ffc7de0b9aa0a870d2125f7640f2447a7358ba454abba3db003f9044a3`.
The layer edge `K3 -> K4` is now explicit: the client's public gcd branch
reaches division, while the strict 74-row K3 stack and digest remain exactly
unchanged. At that intermediate checkpoint, the campaign had 78 candidates
and 87 theorem receipts: 74 strict-
K3 signed rows, three canonical-gcd rows, and this one K4 signed-gcd client,
across 18 candidate modules and 19 focused tests. Nothing in that checkpoint
was admitted.

The completed canonical gcd/LCM checkpoint is frozen in
[`ha-canonical-gcd-lcm-rfc-v1.md`](../research/arithmetic-library/ha-canonical-gcd-lcm-rfc-v1.md).
Five rows in
[`ha_canonical_gcd_edges_candidate.py`](../peano-lab/py/peano_lab/library/ha_canonical_gcd_edges_candidate.py)
close the zero, one, and cross-witness symmetry boundary. Seventeen rows in
[`ha_relational_lcm_candidate.py`](../peano-lab/py/peano_lab/library/ha_relational_lcm_candidate.py)
then close the literal-safe universal-property core, forced zero values,
divisibility specializations, self/one laws, product common-multiple bound,
and zero unique-existence packages. Their zero-right constructor is direct;
zero-left is derived from it by symmetry so the conventions cannot drift.
Both tranches have focused cold-closure and mutation audits and remain
unregistered.

The nine rows in
[`ha_lcm_totality_bridge_candidate.py`](../peano-lab/py/peano_lab/library/ha_lcm_totality_bridge_candidate.py),
audited by
[`test_ha_lcm_totality_bridge_candidate.py`](../peano-lab/py/tests/test_ha_lcm_totality_bridge_candidate.py),
now close the full constructive route. `gcd_lcm_compatible_exists` handles the
zero and nonzero gcd branches explicitly in 9,038 nodes at depth 60;
`lcm_exists_relational` projects totality, `canonical_lcm_exists_unique`
packages the unique value, and `gcd_lcm_product` closes the arbitrary
compatibility theorem in 10,441 nodes at depth 61. Every certificate has zero
`DNE` nodes. The latter route is K4 because its public gcd/Gauss closure
reaches division; it does not alter the strict 74-row K3 stack.

At the pre-admission source checkpoint there were 109 isolated candidates and
118 total evidence receipts across 21 candidate modules and 22 focused tests.
The strict K3 component remains exactly 74 rows. That checkpoint established
the complete K4 proof receipts but made no admission claim.

## Third implementation tranche — K4 admission and generalized CRT

The selective K4 admission preserves the exact candidate specifications and
receipts and appends these 16 theorems in order:

```text
is_lcm_multiple_left
is_lcm_multiple_right
is_lcm_least
is_lcm_symm
is_lcm_unique
is_lcm_zero_right
is_lcm_zero_left
balanced_bezout_one_implies_coprime
coprime_product_is_lcm
is_lcm_scale_nonzero
balanced_bezout_cancel_gcd
gcd_zero_inputs
gcd_lcm_compatible_exists
lcm_exists_relational
canonical_lcm_exists_unique
gcd_lcm_product
```

All 16 replay twice from the empty context with their frozen proof-DAG
receipts, reject false endpoint mutations, and contain zero `DNE`. At the K4
admission checkpoint the public registry had 409 entries and the synchronized
research catalog had 410 entries, with 386 at `checked_m20`. The first-247
model-v3 prefix was unchanged.

The deliberately private K4 remainder has exactly 19 rows: three canonical-gcd
package rows, five canonical-gcd edge rows, ten LCM convenience rows (L08 plus
C01--C09), and `gcd_signed_bezout_exists`. Closed candidate evidence for those
rows is retained, but none is public.

The next M5 layer is isolated in
[`ha_generalized_crt_congruence_candidate.py`](../peano-lab/py/peano_lab/library/ha_generalized_crt_congruence_candidate.py)
and specified in
[`ha-generalized-crt-rfc-v1.md`](../research/arithmetic-library/ha-generalized-crt-rfc-v1.md).
Its eight-row stack reuses the exact existing `mod_eq_add_cancel_left`
specification and adds seven rows for the zero-modulus boundary, right
cancellation, scale/unscale, comparison of two solutions, gcd-compatibility
necessity, and the incompatibility obstruction. Two cold closures agree and
all certificates check constructively with zero `DNE`. The stack remains
isolated at this initial evidence checkpoint; the selective M5 admission
described below later makes five of these rows public and retains three as
private candidates.

The next binary M5a tranche is now closed in
[`ha_generalized_crt_sufficiency_candidate.py`](../peano-lab/py/peano_lab/library/ha_generalized_crt_sufficiency_candidate.py),
with its focused audit in
[`test_ha_generalized_crt_sufficiency_candidate.py`](../peano-lab/py/tests/test_ha_generalized_crt_sufficiency_candidate.py).
Seven ordered rows prove right-factor nonzeroness, coprimality of nonzero gcd
cofactors, a packaged cofactor decomposition, a shared bounded remainder for
compatible residues, scaling/lifting of the public coprime `binary_crt`, the
actual compatible-system construction, and finally the necessary-and-
sufficient solvability criterion for two nonzero moduli. The capstone closes
from the empty context in 10,073 proof occurrences at depth 76, with 3,316
proof objects, 149 Cuts, and zero `DNE`; two cold closures have the same
certificate digest.

The four-row M5b boundary tranche is now closed in
[`ha_generalized_crt_zero_boundary_candidate.py`](../peano-lab/py/peano_lab/library/ha_generalized_crt_zero_boundary_candidate.py).
The directed zero lemmas derive `g=n` or `g=m` from public relational-gcd
uniqueness and choose the residue fixed by the zero modulus. Constructive
equality decisions then dispatch left-zero, right-zero, and both-nonzero
branches. The unrestricted capstone
`generalized_binary_crt_solvable_iff` closes in 11,825 proof occurrences at
depth 80, with 3,658 proof objects, 168 Cuts, and zero `DNE` nodes. The
`(0,0)` case is already included in the left-zero branch. No private
canonical-gcd convenience theorem is a dependency, and no proof, formula, or
kernel limit was raised.

The binary existence criterion is therefore closed for every pair of natural
moduli. The four-row M5c classification tranche is now closed in
[`ha_generalized_crt_classification_candidate.py`](../peano-lab/py/peano_lab/library/ha_generalized_crt_classification_candidate.py),
with its focused audit in
[`test_ha_generalized_crt_classification_candidate.py`](../peano-lab/py/tests/test_ha_generalized_crt_classification_candidate.py).
It proves that an ordered gap between congruent naturals is a modulus
multiple, merges two input congruences through relational-LCM leastness,
packages congruence modulo `l` iff congruence modulo both `m,n`, and finally
proves `CRTSolution(y) iff ModEq(l,y,x)` relative to a fixed solution `x`.
The exact ordered interfaces are
`mod_eq_ordered_gap_multiple`
(`k+x=y -> ModEq(d,x,y) -> Dvd(d,k)`), `mod_eq_lcm_merge`
(`IsLCM(l,m,n) -> ModEq(m,x,y) -> ModEq(n,x,y) -> ModEq(l,x,y)`),
`mod_eq_lcm_iff_pair`, and `crt_solution_class_iff_lcm`. The proof route is
directed-gap divisibility, relational-LCM leastness, the two public LCM
projections, and finally comparison with a fixed solution in the audited
`y`-to-`x` orientation.

Body receipts `(dependencies,commands,nodes,depth,objects,edges,reused)` are
`(4,31,44,21,44,43,0)`, `(6,113,127,26,127,126,0)`,
`(4,46,56,21,56,55,0)`, and `(3,62,79,27,79,78,0)`. Empty-context receipts
`(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` are
`(558,30,310,325,16,13,0,6a30012cfc1213bf167be2de794e05cdae2893ab075cfc24abf9b181bde9be67)`,
`(1315,33,653,685,33,25,0,46cd67f69ccf0c669de283fca6a74a0a85cf18d54f248f1a6f428122196a331b)`,
`(1570,37,864,908,45,32,0,855d5745c1613304fc0a5f26c70fe9f795ed3ebcff4a7276e3745681d41fc91a)`,
and
`(2208,39,1055,1104,50,40,0,305a913aaca1c3e307d8ca77bb90c063dd67f3fa9f9bdd69e28cf4064cdff7b3)`.
At `l=0`, the statement reduces to exact equality, so the proof is uniform
and does not call division.

M5c brought the isolated campaign to 116 candidate references and 141 exact
receipts. The three-row M5d boundary is now closed in
[`ha_generalized_crt_canonical_boundary_candidate.py`](../peano-lab/py/peano_lab/library/ha_generalized_crt_canonical_boundary_candidate.py),
with its focused audit in
[`test_ha_generalized_crt_canonical_boundary_candidate.py`](../peano-lab/py/tests/test_ha_generalized_crt_canonical_boundary_candidate.py):

1. `crt_solution_unique_lcm_zero` assumes `l=0`, `IsLCM(l,m,n)`, and a fixed
   CRT solution `x`, then proves every CRT solution `y` equals `x`; it depends
   on the M5c class theorem and `mod_eq_zero_iff_eq`.
2. `crt_solution_canonical_remainder_nonzero` assumes `l!=0`, `IsLCM`, and a
   fixed solution `x`, then produces the unique solution `r` with
   `Below(r,l) := exists h. h+S r=l`; it depends on division/remainder,
   `mul_comm`, remainder-to-congruence, congruence symmetry, M5c
   classification, and bounded uniqueness.
3. `generalized_binary_crt_canonical_boundary` uses `eq_decidable`, total M5b
   sufficiency, and rows 1--2 to return the correct zero-LCM exact-unique or
   nonzero-LCM bounded-unique branch from gcd/lcm data and compatibility.

Body receipts `(dependencies,commands,nodes,depth,objects,edges,reused)` are
`(2,33,37,28,37,36,0)`, `(6,83,141,39,141,140,0)`, and
`(4,66,76,33,76,75,0)`. Empty-context receipts
`(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` are
`(2300,40,1126,1176,51,43,0,2afc46ac88613c95400eb37f80b1fbda095b18a7f6a774255426b48c35aed9ac)`,
`(4086,65,1668,1746,79,64,0,091e8f2b1ba7e4665b87071fcd924ea1098880d65a97bcdd264ed544e33ff0e4)`,
and
`(17750,80,4239,4426,188,193,0,c704a17f6feed83142b160bbeafcc14764d5ae6590999187eed5455c3ad03bd7)`.
All three contain zero `DNE` and fit unchanged limits. The retained oracle
checks 4,021 compatible systems: 611 zero-LCM exact-uniqueness cases and
3,410 nonzero-LCM canonical-remainder cases. At the pre-admission M5d
checkpoint the isolated campaign had 119 candidate references and 144 exact
receipts, while the public registry and catalog remained 409 and 410.

The two-row M5e executable boundary is now closed in
[`ha_generalized_crt_decision_candidate.py`](../peano-lab/py/peano_lab/library/ha_generalized_crt_decision_candidate.py),
with its focused audit in
[`test_ha_generalized_crt_decision_candidate.py`](../peano-lab/py/tests/test_ha_generalized_crt_decision_candidate.py).
`mod_eq_decidable` combines equality decision and `mod_eq_zero_iff_eq` at
modulus zero with public `mod_eq_decidable_nonzero`. Then
`generalized_binary_crt_solution_or_obstruction` decides gcd compatibility:
the positive branch calls total M5b sufficiency, while the negative branch
uses `crt_incompatibility_obstructs_solution`. Its output carries both the
decided compatibility proposition and the corresponding existence or
unsolvability certificate.

The two body receipts are `(3,35,47,16,47,46,0)` and
`(3,36,43,22,43,42,0)`. Empty-context receipts are
`(2339,70,1217,1278,62,44,0,298e2b18fff84bcf3a2ec69dbc464454f958d4155b7afb687f0bab2fd95efe7e)`
and
`(14182,80,3909,4090,182,182,0,16e7cb1c430fa4e17ea878adc72d34c92e0bc3f135c4a3cf24cb2a296b38e525)`.
Both have zero `DNE` and fit unchanged limits. Retained semantics cover all
847 cases with `d<7`, `a,b<11` and all 5,929 CRT systems with `m,n<7`,
`a,b<11`: 4,021 return the solution branch and 1,908 return the obstruction
branch. At the pre-admission M5e checkpoint the evidence had 121 private
candidates and 146 receipts.

The one-row M5f raw-input endpoint is now closed in
[`ha_generalized_crt_total_decision_candidate.py`](../peano-lab/py/peano_lab/library/ha_generalized_crt_total_decision_candidate.py),
with its focused audit in
[`test_ha_generalized_crt_total_decision_candidate.py`](../peano-lab/py/tests/test_ha_generalized_crt_total_decision_candidate.py).
`generalized_binary_crt_total_decision` starts from arbitrary raw inputs
`m,n,a,b`, uses `gcd_exists_relational` to construct an existential
`IsGCD(g,m,n)` witness, and invokes
`generalized_binary_crt_solution_or_obstruction`. Its output retains that gcd
witness and returns either `ModEq(g,a,b)` with a common solution or
`~ModEq(g,a,b)` with a proof that no common solution exists. The theorem is
not a primitive gcd function and does not select a canonical bounded CRT
representative; the separate M5d interface supplies the zero/nonzero
canonical boundary.

The statement SHA-256 is
`42d29bf501421be60c1a2b14fa858a14abf230eee2f7669503db019d6b014151`.
Its body receipt `(dependencies,commands,nodes,depth,objects,edges,reused)` is
`(2,17,42,25,42,41,0)`. Its empty-context receipt
`(nodes,depth,objects,edges,reused,Cuts,DNE,digest)` is
`(15492,82,4052,4240,189,192,0,c2d915d2eb60ccbb2dac9f31e9e1f9c310c28264b74483ec97ae33a1a0d965ee)`.
At the pre-admission M5f checkpoint, the campaign had 122 private candidates
and 147 receipts across 27 candidate modules and 30 focused test paths. The
generalized-CRT stack has 29 rows in total: 28 new rows and one exact reused
support row.

The selective M5 admission is now complete. It appends public indices
409--431 as the exact dependency closure of
`generalized_binary_crt_solvable_iff`,
`generalized_binary_crt_canonical_boundary`, and
`generalized_binary_crt_total_decision`. This exposes 23 rows without changing
their factory specifications, scripts, receipts, or intuitionistic proof
profile. The six reviewed rows outside that closure remain private:

- `mod_eq_add_cancel_left`;
- `mod_eq_add_cancel_right`;
- `mod_eq_unscale_nonzero`;
- `factor_nonzero_right`;
- `is_gcd_nonzero_coprime_quotients`;
- `generalized_binary_crt_solvable_iff_nonzero`.

The current runtime/catalog boundary is 432/433, with 409 catalog rows at
`checked_m20`. The campaign manifest has 95 public references, 99 private
candidates, 147 exact receipts, 22 candidate modules, and 31 focused test
paths. Only the K3 finite-system fold remains for the main finite generalized-
CRT target; the six conveniences remain deliberately private and are not a
blocker. No row asserts a remainder below zero.

## Release boundary

The first named campaign release is **Euclidean and Modular Arithmetic in
HA**.  It requires HA0--HA3 and M1--M3 to be `public_checked`; M4/M5 may form a
second release if the independent list substrate is not ready.  Quadratic
reciprocity, FTA, or any beta-coded result already present in the repository
does not waive these canonical-interface gates.
