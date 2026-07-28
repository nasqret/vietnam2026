# Natural Number Game 4 source map

## Purpose and scope

This note maps the official Lean 4 Natural Number Game curriculum to the
checked Peano Lab theorem ladder.  It is a source and gap inventory, not an
authorization to import Lean proofs as trusted Peano certificates.

The audit covers the public
[`leanprover-community/NNG4`](https://github.com/leanprover-community/NNG4)
repository at the immutable revision
[`727e4d219838eeb7f3945d2e9a0539f244d50540`](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540),
checked on 2026-07-28.  The corresponding interactive game is the
[Natural Number Game](https://adam.math.hhu.de/#/g/leanprover-community/nng4).

At that revision, NNG4's active curriculum has nine worlds and 55 named,
reusable level conclusions.  Unnamed tactic-training and numeral exercises
are outside this count.  The active-world manifest is
[`Game.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game.lean).

## Pinned provenance and license

| Field | Value |
|---|---|
| Source ID | `nng4` |
| Repository | `https://github.com/leanprover-community/NNG4` |
| Revision | `727e4d219838eeb7f3945d2e9a0539f244d50540` |
| License | [Apache License 2.0](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/LICENSE) |
| Upstream `NOTICE` | No `NOTICE` file is present at the pinned revision |
| Lean 4 provenance | The [README](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/README.md) identifies this as the Lean 4 adaptation of the classical game |
| Earlier source | [The frozen Lean 3 Natural Number Game](https://github.com/ImperialCollegeLondon/natural_number_game), also Apache-2.0 |

The pinned [`Game.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game.lean)
credits Kevin Buzzard and Jon Eugster as creators, Kevin Buzzard and Mohammad
Pedramfar for the original Lean 3 version, and Sian Carey, Ivan Farabella, and
Archie Browne for additional levels.  File history remains the authority for
more granular authorship.

## Notation and concept translation

NNG4 works with its own inductive `MyNat`; Peano Lab works in the first-order
PA language checked by its independent kernel.  The following translations
must therefore be recorded rather than silently assumed.

| NNG4 | Peano Lab | Status |
|---|---|---|
| `succ n` | `S n` | Direct term translation |
| `add_zero` | PA3, `n + 0 = n` | Kernel axiom, not a library dependency |
| `add_succ` | PA4, `n + S m = S (n + m)` | Kernel axiom |
| `mul_zero` | PA5, `n * 0 = 0` | Kernel axiom |
| `mul_succ` | PA6, `n * S m = n * m + n` | Kernel axiom |
| `succ_add` | `add_succ_left` | Same theorem after renaming `succ` to `S` |
| `zero_mul` | `mul_zero_left` | Same theorem after naming normalization |
| `succ_mul` | `mul_succ_left` | Same theorem after naming normalization |
| `succ_inj` | `succ_injective` | Same mathematical result |
| `a ≤ b` | Peano Lab's existential additive-witness order | Check equality orientation when adapting a statement |
| `a ≠ b` | `~(a = b)` | Syntax translation |
| `a ^ n` | No current Peano term | Requires a language/encoding decision before porting |

NNG4 can rely on Lean's generic congruence and rewriting machinery.  Peano Lab
already has checked `congr` and `rewrite` tactics, and M20 now exposes the
Peano-native named family `eq_symm`, `eq_trans`, `succ_congr`, `add_congr`, and
`mul_congr`. These theorems were designed directly for Peano's language rather
than attributed to NNG4.

## Curriculum inventory and checked-library mapping

"Checked" below means an existing named entry in
`peano-lab/py/peano_lab/library/theorems.py`, not merely something derivable by
a tactic.  "Gap" means a useful named result is absent from that checked
catalog at the time of this audit.

### 1. Peano constructors, equality, and negation

Pinned sources:

- [`Game/MyNat/PeanoAxioms.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/MyNat/PeanoAxioms.lean)
- [Implication World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/Implication)
- [Algorithm World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/Algorithm)

Exact reusable names are `pred_succ`, `succ_inj`, `zero_ne_succ`,
`succ_ne_zero`, `succ_ne_succ`, `zero_ne_one`, and `one_ne_zero`.

| NNG4 result | Peano checked fact | Assessment |
|---|---|---|
| `succ_inj` | `succ_injective` | Covered |
| `succ_ne_zero` | `succ_ne_zero` | Covered |
| `zero_ne_succ` | None with that equality orientation | Small symmetric wrapper gap |
| `succ_ne_succ` | None | High-value small gap |
| `zero_ne_one`, `one_ne_zero` | None | Small numeral corollary gaps |
| `pred_succ` | No predecessor term | Do not port without a language extension |

### 2. Addition and successor normalization

Pinned sources:

- [`Game/MyNat/Addition.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/MyNat/Addition.lean)
- [Tutorial World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/Tutorial)
- [Addition World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/Addition)
- [Algorithm World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/Algorithm)

Exact named conclusions are `succ_eq_add_one`, `zero_add`, `succ_add`,
`add_comm`, `add_assoc`, `add_right_comm`, and `add_left_comm`.  The primitive
equations are `add_zero` and `add_succ`.

| NNG4 result | Peano checked fact | Assessment |
|---|---|---|
| `add_zero`, `add_succ` | PA3, PA4 | Kernel-covered |
| `zero_add` | `zero_add` | Covered |
| `succ_add` | `add_succ_left` | Covered after canonical renaming |
| `add_comm` | `add_comm` | Covered |
| `add_assoc` | `add_assoc` | Covered |
| `succ_eq_add_one` | None | Useful normalization gap |
| `add_left_comm` | None | High-value rearrangement gap |
| `add_right_comm` | None | High-value rearrangement gap |

### 3. Additive cancellation and rigidity

Pinned source: [Advanced Addition World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/AdvAddition).

Exact names are `add_right_cancel`, `add_left_cancel`, `add_left_eq_self`,
`add_right_eq_self`, `add_right_eq_zero`, and `add_left_eq_zero`.

| NNG4 result | Peano checked fact | Assessment |
|---|---|---|
| `add_left_eq_zero`: `a + b = 0 -> b = 0` | `add_eq_zero_right` | Covered under a clearer Peano name |
| `add_right_eq_zero`: `a + b = 0 -> a = 0` | `add_eq_zero_left` | Covered under a clearer Peano name |
| Left/right cancellation | `add_left_cancel`, `add_right_cancel` | Covered |
| Left/right addend-equals-self results | None | Gaps |

Peano's `no_succ_add_fixed`, `drop_add_prefix_from_fixed`, and
`antisymm_from_witnesses` remain related checked infrastructure beneath this
user-facing cancellation API.

### 4. Multiplicative semiring algebra

Pinned sources:

- [`Game/MyNat/Multiplication.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/MyNat/Multiplication.lean)
- [Multiplication World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/Multiplication)

Exact named conclusions are `mul_one`, `zero_mul`, `succ_mul`, `mul_comm`,
`one_mul`, `two_mul`, `mul_add`, `add_mul`, and `mul_assoc`.  The primitive
equations are `mul_zero` and `mul_succ`.

| NNG4 result | Peano checked fact | Assessment |
|---|---|---|
| `mul_zero`, `mul_succ` | PA5, PA6 | Kernel-covered |
| `zero_mul` | `mul_zero_left` | Covered after canonical renaming |
| `succ_mul` | `mul_succ_left` | Covered after canonical renaming |
| `mul_one`, `one_mul` | Same names | Covered |
| `mul_comm`, `mul_assoc` | Same names | Covered |
| `mul_add`, `add_mul` | Same names | Covered |
| `two_mul` | None | Small useful normalization gap |

### 5. Additive-witness order

Pinned sources:

- [`Game/MyNat/LE.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/MyNat/LE.lean)
- [Less-Or-Equal World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/LessOrEqual)

Exact names are `le_refl`, `zero_le`, `le_succ_self`, `le_trans`, `le_zero`,
`le_antisymm`, `le_total`, `succ_le_succ`, `le_one`, and `le_two`.

| NNG4 result | Peano checked fact | Assessment |
|---|---|---|
| `le_refl`, `le_trans`, `le_antisymm`, `le_total` | Same names | Covered |
| `zero_le`, `le_succ_self`, `le_zero` | Same names | Covered |
| `succ_le_succ` | None | Gap; NNG4's theorem is only the cancellation direction |
| `le_one`, `le_two` | None | Useful finite-bound corollaries, lower priority |

The general library should add both successor-order directions and an iff,
not preserve NNG4's one-direction-only API.

### 6. Ordered multiplication, nonzero products, and cancellation

Pinned source: [Advanced Multiplication World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/AdvMultiplication).

Exact names are `mul_le_mul_right`, `mul_left_ne_zero`,
`eq_succ_of_ne_zero`, `one_le_of_ne_zero`, `le_mul_right`,
`mul_right_eq_one`, `mul_ne_zero`, `mul_eq_zero`, `mul_left_cancel`, and
`mul_right_eq_self`.

| NNG4 result | Peano checked fact | Assessment |
|---|---|---|
| `mul_eq_zero` | `mul_eq_zero` | Covered |
| `mul_ne_zero` | `mul_ne_zero` | Covered |
| All other named results in this family | None | Gaps |

The Peano API should not copy the asymmetry of the teaching sequence.  It
should include left and right multiplication monotonicity, both nonzero-factor
projections, both cancellation orientations, both factor conclusions from a
product equal to one, and symmetric product-equals-self lemmas.

### 7. Powers

Pinned sources:

- [`Game/MyNat/Power.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/MyNat/Power.lean)
- [Power World](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/Power)

Exact sound, named curriculum results are `zero_pow_zero`, `zero_pow_succ`,
`pow_one`, `one_pow`, `pow_two`, `pow_add`, `mul_pow`, `pow_pow`, and
`add_sq`.  NNG4 adopts the convention `0 ^ 0 = 1`.

Peano Lab currently has no exponentiation term constructor, so every item in
this family is language-blocked rather than merely an absent theorem.  A later
design must choose between extending the term language, adding a graph
predicate for exponentiation, or documenting bounded multiplication
expansions such as squares and fourth powers.

## Explicit source boundaries

### Prime-number world is empty

NNG4 is not a source for divisibility, primality, Euclid's lemma, prime
factorization, or the fundamental theorem of arithmetic at the pinned
revision.  The active
[`Game.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game.lean)
comments out Prime, Even/Odd, and Strong Induction worlds and describes them
as in development.  The entire pinned
[`WIPPrime.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/WIPPrime.lean)
is an empty titled world with no definitions, statements, or proofs.

Therefore:

- do not attach NNG4 provenance to any prime or factorization lemma;
- treat Peano's checked `prime_two` as an independent reconstruction informed
  by non-NNG4 sources;
- do not infer content from a planned world name or game description;
- source those layers independently and record their actual primary sources.

### Fermat's Last Theorem level is excluded

The final Power level,
[`L10FLT.lean`](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/Game/Levels/Power/L10FLT.lean),
deliberately closes its FLT statement with the teaching escape hatch `xyzzy`.
Its own documentation describes `xyzzy` as analogous to `sorry`.  It is not a
mathematical proof and must never be ingested as a checked result.

The arithmetic corpus must exclude the FLT statement, the `xyzzy` script, and
any derived claim of verification.  The file may be cited only as a negative
provenance record explaining the exclusion.

## Recommended dependency priority

This is a Peano-oriented build order, not NNG4's pedagogical file-import order.

1. PA axioms, induction, equality, and propositional/quantifier logic.
2. Named congruence wrappers for `S`, `+`, and `*`, built directly from the
   checked equality rules.
3. Successor and addition normal forms.
4. Additive commutative-monoid rearrangements.
5. Additive cancellation and zero/self rigidity.
6. Multiplicative commutative-semiring algebra.
7. Core additive-witness order.
8. Addition and multiplication monotonicity.
9. Nonzero products, factor rigidity, and multiplication cancellation.
10. Powers, only after an explicit representation decision.
11. Divisibility, gcd, primes, and factorization from non-NNG4 sources.

This order should be refined using Peano certificate node/depth measurements.
The best source-level dependency is not always the best checked-certificate
dependency because Peano's library replay inlines dependency certificates.

## Independent-reconstruction policy

NNG4 is a curriculum and statement source.  It is not part of Peano Lab's
trusted proof base.

1. Adapt each selected statement explicitly into Peano syntax.
2. Prove it from PA axioms and earlier checked Peano facts using only accepted
   Peano tactics.
3. Replay the resulting closed certificate and submit it to the independent
   Peano kernel.
4. Record proof nodes, proof depth, dependency order, and live-`use`
   compatibility.
5. Record the exact upstream repository, revision, source path, upstream name,
   license, statement translation, and adaptation notes.
6. Label the proof origin `independent-reconstruction`; do not imply that a
   Lean proof term was translated or trusted.
7. If any Lean source code or explanatory prose is copied or modified, retain
   the Apache-2.0 license and applicable attribution and mark the modification.
8. Keep exclusions such as empty planned worlds and admitted teaching levels
   in the source register so later audits cannot accidentally promote them.

A suitable per-lemma provenance record is:

```yaml
source_id: nng4
repository: https://github.com/leanprover-community/NNG4
revision: 727e4d219838eeb7f3945d2e9a0539f244d50540
path: Game/Levels/Addition/L03add_comm.lean
upstream_name: add_comm
license: Apache-2.0
reuse_mode: statement-adapted-proof-independently-reconstructed
statement_changes:
  - MyNat.succ renamed to S
proof_origin: peano-native
retrieved: 2026-07-28
```

This policy preserves scholarly credit and license traceability while keeping
the independent Peano checker as the sole authority for theorem acceptance.
