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
  independent empty-context closure and Alpha/Stable admission remain open.
- Stage 5: sixty-four independently checked constructive candidate bodies
  establish the **complete unconditional multidigit Lucas theorem**. They
  include both unrestricted prime-row shifts, every high-column boundary,
  the exact arbitrary-quotient one-step Lucas congruence, genuinely
  terminating beta-coded quotient/digit chains, actual digit-coefficient
  streams, and a witnessed modular product fold. The final unrestricted
  `lucas_theorem` has exact statement SHA-256
  `396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564`.
  No mathematical gap remains in its dependency-curried candidate body;
  independent empty-context closure and Alpha/Stable admission remain open.
- Aggregate checkpoint: exactly 464 checked constructive candidate proof
  bodies across stages 1–5, plus twenty-two independently constructed and
  kernel-checked empty-context certificates for existing Bertrand
  prerequisites. Five definition-aware interactive explorer families cover
  the supplementary laws, Kummer, two squares, complete all-natural Lagrange,
  and complete multidigit Lucas; `make stage-proofs` assembles them beside
  the existing
  quadratic reciprocity and Bertrand families without requiring faculty-host
  access. The complete ordered local gate passes **2,113 tests across 40
  focused suites**, each running in a separate bounded Python process.
  Stable remains at 432 rows, sealed Alpha v12 remains at 1,303 rows, and
  exactly 570 Alpha specifications permit checked theorem uses.
- Run `make ha-constructive-frontier-check` to replay the focused campaigns
  serially in bounded, independent Python processes.
