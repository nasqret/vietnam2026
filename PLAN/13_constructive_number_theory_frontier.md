# Constructive number-theory frontier — execution roadmap

Approved: 2026-08-23.

This roadmap is the dependency-ordered continuation of
[`12_ha_number_theory_campaign.md`](12_ha_number_theory_campaign.md) after the
constructive Bertrand campaign. The foundational dossier remains
[`ha-number-theory-formalization-campaign-blueprint.md`](../research/arithmetic-library/ha-number-theory-formalization-campaign-blueprint.md).
Stages must be completed in the order below; independent, isolated preparation
for a later stage is permitted when it does not weaken an earlier release gate.

## Starting point and non-negotiable evidence boundary

- Stable contains 432 independently checked theorems.
- Alpha v12 contains 1,303 specifications: 432 `stable_closed`, 138
  `alpha_closed`, 732 `body_checked`, and one `pending_layered_closure`.
- Exactly 570 Alpha specifications permit checked theorem use.
- `bertrand_closed_upper` and `bertrand_strict` already have focused
  empty-context kernel certificates, but the sealed Alpha v12 release still
  records their campaign rows as `body_checked`; it grants neither checked use
  nor Stable membership.
- `quadratic_reciprocity_combined` has a checked dependency-curried body and
  its complete 557-specification dependency graph, but its standalone layered
  empty-context closure and admission gates remain open.
- The fundamental theorem of arithmetic, prime unboundedness, canonical signed
  arithmetic, modular inverses, generalized binary CRT, valuations, factorial
  and Legendre sums, binomial coefficients, primorials, and floor square roots
  provide reusable foundations at their individually documented evidence
  levels.

For every stage:

1. The trusted target is an exact first-order formula over
   `{0, S, +, *, =}` checked from the empty context by the unchanged
   intuitionistic kernel.
2. Conservative definitions must expand hygienically to the exact target AST.
3. Double-negation elimination, host-language computation, a theorem name, a
   tactic-body receipt, and a browser rendering are never theorem authority.
4. Sealed Alpha and Stable editions remain immutable. Evidence transition and
   promotion require new versioned artifacts, independently checked cold
   receipts, dependency closure, and explicit release membership.
5. A completed theorem includes its ordered dependencies, constructive
   witness or obstruction semantics, focused positive and mutation tests,
   human-readable definitions, and an interactive proof-explorer route.
6. Large closure and release gates run under bounded WMI resource envelopes;
   local work uses narrow tests and does not expand the 557-node QR closure
   recursively.

## Stage 1 — close reciprocity and release existing Bertrand evidence

### 1A. Independently close quadratic reciprocity

- [x] Audit the 557-specification QR closure, remove redundant dependency
      imports where they are proven unnecessary, and preserve each exact
      statement and proof dependency.
- [ ] Compile `quadratic_reciprocity_combined` into a layered, self-contained
      `Cut` certificate instead of recursively expanding repeated ancestors.
- [ ] Check the root from the empty context with no `DNE`.
- [ ] Record structural nodes, distinct proof objects, depth, cuts,
      proof-envelope depth, annotation occurrences, peak memory, and elapsed
      time against the existing resource policy.
- [ ] Run independent cold replay and formula/body/dependency mutation gates.
- [ ] Move the root beyond `pending_layered_closure` only in a newly sealed
      evidence edition justified by the completed receipts.

### 1B. Complete the quadratic-residue interface

- [ ] Prove the first supplementary law: for odd prime `p`, `-1` is a square
      modulo `p` exactly when `p` is congruent to `1` modulo `4`.
- [ ] Prove the second supplementary law: `2` is a square modulo odd prime
      `p` exactly when `p` is congruent to `1` or `7` modulo `8`.
- [ ] Package the constructive positive witness and negative obstruction
      separately; never replace decidability by classical excluded middle.
- [ ] Plan the Jacobi-symbol extension after both supplementary laws have
      genuine proof evidence.

### 1C. Promote Bertrand without rewriting history

- [x] Audit the focused BP01/BP02 certificates and identify their exact
      dependency-closed release slices.
- [ ] Build deterministic cold closure, mutation, capacity, and
      provenance-bound receipts for any slice selected for checked use.
- [ ] Preserve Alpha v1–v12 and Stable v1 byte-for-byte; represent changed
      evidence or membership only in a new sealed edition.
- [ ] Promote only dependency-closed entries with independently checked
      receipts; do not relabel 401 body-only campaign rows as closed by
      inference from a final theorem.
- [ ] Synchronize the exact and definition-aware proof explorers only after
      their evidence metadata is justified.

**Exit gate:** independently closed QR, supplementary laws with honest
evidence labels, and an explicitly versioned Bertrand promotion supported by
the required receipts.

## Stage 2 — full Kummer theorem

Canonical subtraction-free target:

```text
Prime(p) -> Choose(a + b, a, c) -> PowerValuation(p, c, e)
         -> CarryCount(p, a, b, k) -> e = k
```

`CarryCount` must be a conservative, total, functional first-order relation.
The existing Bertrand theorem `central_binom_carry_bit_count` supplies the
special case `a = b`; it is a proof seed, not the general theorem.

- [ ] Freeze the exact hygienic `CarryAt`, `CarryPrefix`, and `CarryCount`
      formulas, including the prime/nonzero-base and finite-prefix boundaries.
- [ ] Generalize the quotient carry law to
      `floor((a+b)/p^j) = floor(a/p^j) + floor(b/p^j) + carry_j`, with
      `carry_j` equal to `0` or `1`.
- [ ] Construct and count the coded carry prefix without importing a
      polynomial or primitive finite-sequence axiom.
- [ ] Generalize the existing central-binomial factorial-valuation balance to
      `Choose(a+b,a,c)`.
- [ ] Combine the three finite Legendre sums to prove the exact valuation
      equals the carry count.
- [ ] Prove equivalence with the usual base-`p` digit-carry interpretation and
      derive the no-carry/nondivisibility corollary.
- [ ] Supply exact, defined, and executable-example proof-explorer views.

**Exit gate:** a standalone intuitionistic Kummer certificate for all primes
and natural `a,b`, with an independently checked carry-count example suite.

## Stage 3 — Fermat two squares and the complete classification

Prime target:

```text
Prime(p) -> ModEq(4, p, 1) -> exists x y. p = x*x + y*y
```

Complete target:

```text
(exists x y. n = x*x + y*y)
  <-> n = 0, or n != 0 and every prime q congruent to 3 modulo 4
      has even valuation in n
```

- [ ] Derive a constructive square root of `-1` modulo a prime congruent to
      `1` modulo `4`, using the first supplementary law and existing residue
      decisions.
- [ ] Use the existing floor-square-root and finite-pigeonhole layers to find
      bounded signed `x,y` with `p | x*x + y*y` and
      `0 < x*x + y*y < p+p`.
- [ ] Conclude the prime representation and expose its explicit pair witness.
- [ ] Prove the Brahmagupta–Fibonacci two-square multiplication identity
      through the existing canonical signed-natural interface.
- [ ] Prove that a prime congruent to `3` modulo `4` dividing a two-square sum
      divides both coordinates, then derive even valuation.
- [ ] Combine prime representations, even valuations, and strictly decreasing
      constructive factor removal to prove the complete iff.
- [ ] Return either an explicit representing pair or a named prime with odd
      valuation as an obstruction.

**Exit gate:** separately closed prime and full-classification roots, complete
definition-aware proof explorers, and an example constructor.

## Stage 4 — four squares and constructive Fermat descent

Primary flagship:

```text
forall n. exists a b c d. n = a*a + b*b + c*c + d*d
```

Companion descent track:

```text
PrimitivePythagorean(x,y,z)
  -> exists m k. canonical Euclidean parametrization of (x,y,z)

Positive(x) -> Positive(y) -> Positive(z)
  -> ~(x*x*x*x + y*y*y*y = z*z)
```

- [ ] Prove Euler's four-square multiplication identity with signed
      coordinate witnesses.
- [ ] Construct a bounded four-square multiple for each prime and implement
      a strictly decreasing, constructive finite descent to the prime itself.
- [ ] Extend the prime result to all naturals using factorization and the
      four-square identity.
- [ ] When the shared square-factor lemmas are ready, classify primitive
      Pythagorean triples and prove Fermat's exponent-four theorem by explicit
      natural-number descent.
- [ ] Distinguish positive four-square witnesses from the negative Fermat
      obstruction in both documentation and browser examples.

**Exit gate:** a closed four-square theorem; the exponent-four companion may
follow as its own separately documented release.

## Stage 5 — primitive roots, Lucas, Pell, and cyclotomic campaigns

- [ ] Complete the independent finite list/map substrate, canonical finite
      CRT, and arithmetic-function prerequisites needed by later campaigns.
- [ ] Formalize finite polynomial coding, evaluation, and the root bound over
      a prime field.
- [ ] Construct a primitive root for every prime modulus; later classify all
      moduli admitting primitive roots.
- [ ] Prove Lucas's digitwise binomial congruence and connect its zero-carry
      case to Kummer's theorem.
- [ ] Encode finite continued fractions constructively and solve Pell's
      equation for every positive nonsquare parameter.
- [ ] Develop cyclotomic values and constructive prime-generation theorems,
      beginning with arbitrarily large primes congruent to `1` modulo a given
      positive modulus.
- [ ] Consider finite Hensel lifting, Wolstenholme's theorem, integer-form
      Chebyshev bounds, and Bang–Zsigmondy only after their named dependency
      layers close.

**Exit gate:** independently reviewed, dependency-ordered campaigns rather
than a single unsupported omnibus theorem.

## Progress reporting

No checkbox may be marked complete solely because a statement, proof sketch,
generated page, or dependency-curried body exists. Every status transition
must identify the accepted certificate or explicitly say which validation gate
remains open.

### Checkpoint — 2026-08-23

- Stage 1A audit: the exact QR graph has 557 specifications, 1,787 edges,
  and 45 layers; the redundant `add_succ_left` import is absent, and focused
  regression proofs confirm all six retained reflection dependencies are live.
  The root remains `pending_layered_closure`. The required bounded WMI
  replay cannot yet start because the cluster SSH endpoint times out.
- Stage 1B: six isolated, kernel-checked proof bodies establish the complete
  first supplementary law; twenty-two establish the complete unconditional
  second supplementary law, including its beta-coded Gauss-sign threshold
  identification, reflection-count shape, and separate positive/negative
  endpoints. No mathematical gap remains in either proof body. None of these
  body-only candidates is admitted or independently closed.
- Stage 1C audit: the strict Bertrand slice contains 544 dependencies and
  1,917 edges: 202 Stable rows, one already-closed Alpha row, and 341
  body-only rows. The bounded microbatch constructor has independently
  produced and kernel-checked empty-context certificates for twenty-two
  noncontiguous rows: all eight QR-origin prerequisites, the first eight
  Bertrand-native interval/power rows, and six safe valuation rows. The
  next valuation-existence theorem's direct premises alone contain 125,419
  proof nodes, exceeding the unchanged 125,000-node local microbatch cap;
  that row and its successor remain explicitly blocked on bounded
  proof-sharing improvements or WMI. Their sealed Alpha-v12 evidence is
  unchanged. Independent cold replay and versioned admission remain open.
- Stage 2 preparation: fifteen checked constructive proof bodies establish
  the full arbitrary-input Kummer endpoint: a beta-coded three-prefix carry
  sequence has bit count exactly equal to the prime valuation of
  `Choose(a+b,a)`. They also establish the exact carry-free iff
  nondivisibility corollary. This is complete dependency-curried
  mathematical proof evidence; independent empty-context closure,
  admission, and publication remain open.
- Stage 3: one hundred forty checked constructive proof bodies establish the
  **complete all-natural two-square iff classification**, with an explicit
  zero boundary. The preceding foundations construct the root of `-1`, the
  genuinely beta-coded affine residue grid and its witnessed collision,
  signed collision-to-norm transport, and the complete prime theorem
  `Prime(p) -> p = 1 mod 4 -> exists x y. p = x*x+y*y`, with statement
  SHA-256
  `41ee377098bb3cc2156a1c8c5ff724d4c2bdbbd72eafa64edd141011291e5ee4`.
  The Brahmagupta--Fibonacci identity supplies multiplicative composition.
  A three-modulo-four prime dividing a represented number divides both
  coordinates; constructive prime-square extraction and strictly decreasing
  descent prove every such prime valuation even. Conversely, bounded
  induction directly on the represented value removes good primes singly
  and bad primes in square pairs while preserving the full even-valuation
  invariant. Thus the final theorem
  `two_square_iff_zero_or_even_three_mod_four_prime_valuations` has exact
  statement SHA-256
  `4c39da833a313bab5ae810215dae5bbc9cc78ea951fe97fb177c36a5347cecd5`.
  No mathematical gap remains in the constructive candidate-body theorem;
  independent empty-context closure and Alpha/Stable admission remain open.
- Stage 4: two hundred seventeen independently checked constructive
  candidate proof bodies establish the complete unconditional eight-variable
  Euler quaternion
  identity, its global subtraction-free compensation lemma, explicit
  multiplication witnesses, and multiplicative closure are independently
  kernel-checked candidate bodies. The all-natural Lagrange theorem reduces
  constructively to represented primes. Actual beta-coded interleaving,
  odd-prime half-square residue injectivity, and complementary residue
  streams now prove the unconditional seed
  `Prime(p) -> exists a b k. a*a+b*b+1=p*k` for every prime, with statement
  SHA-256
  `41b3138912bebce6b45a92e266f018ae7d5cae16d20c817ed20a8decbf14c833`.
  The strictly bounded refinement additionally retains `k < p`, with exact
  statement SHA-256
  `664f15010c001437b0d990b4e1f81f845a0bc734a8fb5a3b31633ed463774077`.
  Exact quaternion quotients, centered signed remainders, unconditional
  even-multiplier halving, sharp odd centered-norm bounds, and strong
  multiplier induction preserving the necessary `k < p` invariant are
  checked. The genuinely distinct signed-conjugate Euler identity is also
  independently checked, with exact statement SHA-256
  `94bd014681b8c5d3e9505fed47fae5cd591da1fc2428217d55d590062880d7a3`.
  Five canonical modular quaternion block configurations cover all sixteen
  actual centered sign patterns. Their complete checked dispatcher
  `four_square_signed_centered_representation` has statement SHA-256
  `58bb112b380e2d614fb63e33d1cd2184abec50bbf6152278105c0796fe539da6`.
  Constructive parity splitting then closes both multiplier-descent branches,
  and the exact unconditional flagship
  `four_square_lagrange`,
  `forall n. exists a b c d. n = a*a + b*b + c*c + d*d`, has statement
  SHA-256
  `fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5`.
  No mathematical gap remains in its dependency-curried candidate body;
  its exact 196-row dependency closure is enrolled in Alpha v13 with
  `body_checked` evidence only. Independent empty-context closure,
  checked-use admission, and Stable admission remain open.
- Stage 5: sixty-four independently checked constructive candidate bodies
  establish the **complete unconditional multidigit Lucas theorem**. They
  include both unrestricted prime-row shifts, every high-column boundary,
  the exact arbitrary-quotient one-step Lucas congruence, genuinely
  terminating beta-coded quotient/digit chains, actual digit-coefficient
  streams, and a witnessed modular product fold. The final unrestricted
  `lucas_theorem` has exact statement SHA-256
  `396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564`.
  No mathematical gap remains in its dependency-curried candidate body;
  its exact 44-row dependency closure is enrolled in Alpha v13 with
  `body_checked` evidence only. Independent empty-context closure,
  checked-use admission, and Stable admission remain open.
- Aggregate checkpoint: exactly 464 checked constructive candidate proof
  bodies across stages 1–5, plus twenty-two independently constructed and
  kernel-checked empty-context certificates for existing Bertrand
  prerequisites. Five definition-aware interactive explorer families cover
  the supplementary laws, Kummer, two squares, complete all-natural Lagrange,
  and complete multidigit Lucas; `make stage-proofs` assembles them beside
  the existing
  quadratic reciprocity and Bertrand families without requiring faculty-host
  access. Before additive Alpha-v13 admission, the complete ordered local gate
  passed **2,113 tests across 40 focused suites**, each running in a separate
  bounded Python process; dedicated Alpha-v13 admission and explorer-evidence
  audits now provide additional focused release coverage.
  Stable remains at 432 rows, the historical sealed Alpha v12 remains
  byte-for-byte at 1,303 rows, and exactly 570 Alpha specifications permit
  checked theorem uses in both the historical v12 and current v13 views.
- Run `make ha-constructive-frontier-check` to replay the focused campaigns
  serially in bounded, independent Python processes.

### Additive Alpha v13 release — evidence and membership boundary

The sealed
[`Alpha v13 frontier admission RFC`](../research/arithmetic-library/alpha-v13-frontier-admission-rfc-v1.md)
adds exactly the missing dependency closures of the completed four-square
and multidigit Lucas roots while preserving Alpha v12 as an object-identical
prefix:

- The 240 new `body_checked` Alpha-only rows comprise precisely 196 rows in
  the four-square campaign closure and 44 rows in the Lucas campaign closure.
  Eighteen of the four-square dependencies also appear in the two-square
  browser family; this does not enroll the final two-square classification.
- Of the 464 frontier candidate rows, exactly 240 enter Alpha v13 and the
  remaining 224 stay unenrolled. The supplementary laws, Kummer theorem, and
  complete two-square classification endpoints receive no inferred membership.
- Alpha v13 contains 1,543 entries: 432 `stable_closed`, 138 `alpha_closed`,
  972 `body_checked`, and one `pending_layered_closure`; its dependency graph
  has 5,189 edges and 45 layers. Stable remains exactly 432 entries, and the
  checked-use surface remains exactly 570 entries.
- Fifty-three unchecked parent ancestors still prevent either new flagship
  from becoming an empty-context theorem or granting checked theorem use.
  Enrollment, mathematical completion of a dependency-curried body,
  independent empty-context closure, and Stable promotion remain four
  separate claims.
- `four_square_lagrange` retains exact statement SHA-256
  `fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5`;
  `lucas_theorem` retains exact statement SHA-256
  `396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564`.
- The Alpha v13 ordered enrollment SHA-256 is
  `6b223edfe6a2e02dc09576671f4fc5f5a41aaf4156f829164222dd3e494da22f`,
  and its complete edition identity SHA-256 is
  `a010e0ee5dece0d3325e8ec084c1f8769ef8e9ca47e2de891d344e54c1b439d1`.

Run `make peano-library-alpha-v13` to regenerate only the additive versioned
release artifacts. Run `make peano-library-alpha-v13-check` to check those
artifacts deterministically, invoke the independent verifier, reject forged
authority and tampered release evidence, and execute the dedicated admission
suite in separate bounded Python processes. The
`peano-library-channels-v13` and `peano-library-channels-v13-check` targets
are equivalent compatibility aliases. Historical v1–v12 targets and sealed
Stable artifacts remain unchanged.

### Additive Alpha v14 — complete Kummer theorem and carry-free criterion

The sealed
[`Alpha v14 Kummer admission RFC`](../research/arithmetic-library/alpha-v14-kummer-admission-rfc-v1.md)
preserves every Alpha-v13 row and appends the exact **13-body** union of the
Kummer binomial-carry theorem and its carry-free divisibility corollary.
The main theorem requires eleven new rows; its corollary requires two more.

- Alpha v14 contains **1,556 entries**, with 5,251 dependency edges and
  45 layers. Stable remains at 432 rows and checked use stays at 570.
- Every appended body has an authentic independently kernel-checked proof
  receipt and exactly `body_checked` evidence; neither flagship obtains
  checked-use authority or Stable membership.
- The ordered-enrollment SHA-256 is
  `d7758c5cfcce4fbe2b48b6b213b134acf9126b84a58a0016c523055be952024e`;
  the complete edition identity is
  `06274ac80612403f6851266fa00f8b543d904072434d5717ca95ae7d40588c16`.

Run `make peano-library-alpha-v14` and
`make peano-library-alpha-v14-check` to generate and independently validate
the additive release in bounded isolated processes.

### Additive Alpha v15 — supplementary laws and complete two-square iff

The sealed
[`Alpha v15 frontier admission RFC`](../research/arithmetic-library/alpha-v15-frontier-admission-rfc-v1.md)
preserves every Alpha-v14 row and admits exactly **117 additional checked
candidate bodies**: 28 for the two supplementary quadratic laws and 89
additional bodies for the complete all-natural two-square classification.
The missing prerequisites were authentic existing proofs of the bounded
Euler criterion and Gauss lemma, not axioms or fabricated placeholders.

- Both `quadratic_supplement_minus_one_complete` and
  `quadratic_supplement_two_complete` are enrolled with their exact
  prerequisites.
- `two_square_iff_zero_or_even_three_mod_four_prime_valuations` is enrolled
  with its complete zero-inclusive classification closure; its statement
  SHA-256 remains
  `4c39da833a313bab5ae810215dae5bbc9cc78ea951fe97fb177c36a5347cecd5`.
- Alpha v15 contains **1,673 entries**, with 5,615 edges and 53 layers:
  432 `stable_closed`, 138 `alpha_closed`, 1,102 `body_checked`, and one
  `pending_layered_closure`. Stable remains at 432 rows and exactly 570
  Alpha specifications permit checked theorem use.
- The ordered-enrollment SHA-256 is
  `44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175`;
  the complete edition identity is
  `2f1a097ac0b6821c74cd4da088c396d3b9960ffd43e169f22b4778d5871adc66`.

Run `make peano-library-alpha-v15` and
`make peano-library-alpha-v15-check` to generate and independently validate
the additive release. Its fourteen proof-factory groups replay serially in
fresh subprocesses rather than accumulating global proof caches.

### Genuine bounded closure progress and the unchanged authority boundary

The constructive Lucas flagship has a 213-row exact dependency slice,
including 74 rows without release-authorized checked use. The four-square
flagship has a 390-row slice with 219 such rows; their union contains 481
rows, including 293 body-only rows. A generic bounded promotion planner
constructs and independently checks actual empty-context certificates
without changing any sealed release, trusted kernel, or authority surface.

Naïvely cutting independently closed prerequisites into
`choose_factorial_bridge` duplicates their shared `choose_exists` proof and
already requires 194,629 structural nodes, exceeding the frozen 125,000-node
limit. The reviewed layered-Cut constructor derives the dependent weighted
lemma contextually and cuts the common prerequisite only once, yielding a
genuine empty-context certificate with **109,841 structural nodes, 9,535
proof objects, and depth 104**. This respects the unchanged 125,000-node and
25,000-object caps. Such a certificate is real proof evidence, but does not
itself modify release evidence or grant checked theorem use.

The final older Lucas prerequisite, `choose_prime_divides_between`, initially
defeats the maximum permitted pending-only sixteen-body shared package: its
29 already-closed Stable leaves total **76,923** structural nodes and its
three body-only leaves total **89,900**, producing a **166,823-node lower
bound** before any theorem body is counted. In particular, `choose_exists`
and the already-closed `factorial_exists` alone require 149,333 nodes.

The separately reviewed
[`mixed Stable/Lucas promotion RFC`](../research/arithmetic-library/lucas-mixed-promotion-rfc-v1.md)
resolves the obstruction without changing any limit. Its contextual proof
contains exactly **eleven pending bodies plus five already-closed Stable
bodies**, counting all sixteen against the unchanged maximum. The shared
`beta_prefix_extend` certificate appears only once, reducing actual Stable
leaves to **42,391 structural nodes and 10,413 proof objects**. Its final
ordinary empty-context proof is genuinely accepted by the unchanged kernel
under the original 125,000-node/25,000-object envelope. Thus **all 30 older
Lucas prerequisites** now have actual independently checked closure
candidates. A follow-up dependency-ordered microbatch genuinely constructs
and independently kernel-checks **16 of the 44 Lucas campaign rows** under
the same unchanged aggregate caps. Three additional dependency-ready
microbatches then independently close fourteen more:

- **7 proofs / 78,442 nodes / 12,147 objects**.
- **6 proofs / 75,700 nodes / 10,698 objects**.
- **1 proof / 62,671 nodes / 5,546 objects**.

The next two formerly blocked entrances also now have genuine independently
checked closure certificates. Contextualizing the shared older Choose
infrastructure reduces the **119,156-node** direct-prefix lower bound to
actual empty-context proofs of **30,854 nodes / 5,615 objects** for
`lucas_choose_prefix_extend` and **30,916 nodes / 5,677 objects** for
`lucas_choose_prefix_exists`. A separate exact sixteen-body mixed package
then closes `lucas_prime_row_interior_divisible` in **70,258 nodes / 11,011
objects**. These are actual unchanged-kernel proofs, not inferred evidence,
and every package respects all original resource limits. Thus **33 of 44
Lucas campaign rows** now have actual closed certificates. The remaining
eleven campaign rows, full flagship closure, and checked-use promotion
remain separate open gates.

The dedicated
[`bounded four-square promotion RFC`](../research/arithmetic-library/four-square-frontier-promotion-rfc-v1.md)
separately freezes the Lagrange flagship's complete **390-row** slice:
166 Stable-closed rows, five Alpha-closed rows, **23** older body-only
prerequisites, and **196** body-only four-square campaign rows. Its 219
unchecked obligations occupy fifteen exact dependency-ready layers; the
23 parent obligations form layers of size 17, 5, and 1. Eighteen non-beta
parents form one dependency-closed subgraph; the remaining five are exact
beta-prefix construction obligations. One actual sixteen-row parent
microbatch has **18,008 structural proof nodes and 8,869 proof objects**;
together with two separately checked parent certificates, this genuinely
closes eighteen older Lagrange prerequisites. The five remaining beta-prefix
obligations now have independently kernel-checked singleton certificates:

- `beta_pointwise_mul_prefix_extend`: **30,906 nodes / 4,643 objects**.
- `beta_pointwise_mul_prefix_exists`: **31,467 nodes / 4,705 objects**.
- `beta_prefix_append_two_exists`: **29,185 nodes / 4,571 objects**.
- `beta_division_prefix_extend`: **29,317 nodes / 4,654 objects**.
- `beta_division_prefix_exists`: **30,106 nodes / 4,725 objects**.

Thus **all 23 older Lagrange prerequisites** now have actual independent
empty-context closure candidates. The first **52 of 196 four-square campaign
rows** also have genuine independently checked empty-context certificates,
constructed in four separate dependency-ordered batches:

- **16 proofs / 1,232 nodes / 1,125 objects**.
- **16 proofs / 4,552 nodes / 3,664 objects**.
- **16 proofs / 10,261 nodes / 5,964 objects**.
- **4 proofs / 77,161 nodes / 12,811 objects**.

Every individual batch respects all original 16-row/125,000-node/25,000-object
limits. A subsequent second-layer batch first reconstructs ten genuinely
closed prerequisites in **2,973 nodes / 2,114 objects**, then independently
kernel-checks sixteen additional campaign bodies in **10,229 nodes / 6,322
objects**. A further sealed continuation first reconstructs sixteen genuine
predecessor certificates in **11,374 nodes / 7,149 objects**, then
independently kernel-checks twelve new four-square campaign bodies in
**14,263 nodes / 7,471 objects**. Consequently, **80 of 196 four-square
campaign rows** now have genuine empty-context closure certificates. The
remaining 116 campaign certificates, complete flagship closure, and
checked-use promotion remain open. Planning and actual bounded candidate
certificates never alter the sealed release or checked-use authority.

Consequently, the combined **53 previously unchecked older prerequisites**
for the two flagship families have all been genuinely closed in bounded
independent proof experiments. The remaining frontier is the exact **240-row
Alpha-v13 campaign append** itself: 44 Lucas bodies and 196 four-square bodies;
the first **33 Lucas and 80 four-square** campaign rows also already have
genuine independent closure certificates. The precise combined result is
**166 genuinely closed body-only obligations out of 293**, with **127 still
open** (11 Lucas and 116 Lagrange).

### Sixth campaign — Pythagorean triples and Fermat exponent four

The
[`Pythagorean/Fermat-four foundations RFC`](../research/arithmetic-library/pythagorean-fermat-four-rfc-v1.md)
starts a sixth constructive proof family. Its initial **17 independently
kernel-checked candidate bodies** establish Euclid's subtraction-free
forward parametrization, ordered square-difference witnesses, parity,
primitive-leg symmetry, and bounded induction bridges to Fermat's
fourth-power statement.

The additional
[`primitive Pythagorean constructor RFC`](../research/arithmetic-library/pythagorean-primitive-rfc-v1.md)
adds **27 independently kernel-checked candidate bodies**, bringing this
campaign to **44**. These prove the complete forward primitive Euclidean
constructor from ordered coprime opposite-parity parameters. They also prove
that every primitive Pythagorean triple has opposite-parity legs, an odd
hypotenuse, pairwise coprime coordinates, and a constructive normal form;
no Pythagorean triple can have two odd legs.

The reverse classification of primitive triples and the strictly decreasing
Fermat counterexample constructor are explicitly still open. Consequently,
the Fermat-four prohibition is conditional on the exact displayed descent
premise and must never be described as an unconditional theorem.

All six definition-aware explorers display their original Alpha admission
version separately from active Alpha-v15 membership and retain their
body-only/checked-use boundary. `make stage-proofs` stages the sixth
`pythagorean-fermat-four/` family beside the existing maps without performing
any remote deployment.
