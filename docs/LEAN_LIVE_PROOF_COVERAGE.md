# Independently readable Lean proof coverage

Hydra translates each original Peano tactic into ordinary Lean proof code and
requires the unchanged Lean kernel to compile the exact theorem. The generated
standalone Lean Live proof includes its actual named prerequisite proofs and no
certificate fallback, private companion, invented axiom, or unfinished term.

Five exact proof-state correspondences materially extend this coverage:

- Unary successor congruence uses the real Lean-core theorem `congrArg`.
  Binary addition and multiplication use the genuine core combination
  `refine congr (congrArg Nat.add ?_) ?_` or its `Nat.mul` counterpart.
  The nonexistent `congrArg₂` is never emitted. Explicit placeholders preserve
  both authenticated original Peano obligations, including reflexive ones.
- An authored Peano rewrite changes one occurrence and leaves its proof goal
  open. Lean's shorthand `rw` changes multiple occurrences and may close a
  reflexive goal. The exact translation is consequently
  `rewrite (occs := .pos [1]) [h]`; reverse rewrites and hypothesis targets
  retain their original direction, location, and preserved prior evidence.
- Lean treats the successor-addition law `PA4` as a definitional reduction,
  so even a restricted Lean rewrite can simplify more occurrences than the
  authenticated Peano proof step. Hydra emits `change <next proof state>`
  instead, including `change ... at h` for hypotheses. The unchanged Lean
  kernel checks that exact successor state before the original proof proceeds.
- Human-readable declarations expose conservative aliases such as `DivRem`,
  `InversePrefix`, `InverseIndex`, and `IsGCD`. A reconstructed tactic body can
  legitimately use a smaller alias set or the fully expanded formula. Hydra
  preserves the compact public declaration and inserts an exact `change` to
  its independently reconstructed statement. Lean checks their definitional
  equivalence; no alias is assumed as an extra axiom.
- Repeated rewrites inside compact local hypotheses can otherwise make Lean
  select a different hidden occurrence from the original Peano proof. When a
  conservative alias is actually present, Hydra first exposes the exact
  authenticated pre-rewrite state, applies the original one-occurrence
  rewrite, and restores the exact authenticated successor state. Ordinary
  unaliased arithmetic stays compact; the originally reported 66-node source
  grows by only about 2.3%.

Actual bounded independent Lean compilation confirmed the historical Alpha-v19
theorem, still present in the current Alpha-v21 edition,
`pythagorean_double_product` as nine named readable proofs, nine dependency
edges, and 44 original tactic decisions, with zero certificate fallbacks.
The complete generated standalone sources for that theorem, Stable `add_comm`,
and Stable `mul_comm` also compiled with **no explicit imports whatsoever**
under Lean's implicit core prelude and a 1,024 MiB compiler allowance. Real
browser-service acceptance checks authenticated all three corresponding
compressed Lean Live links against their exact locally compiled source bytes.
The links use the unpadded standard-Base64 LZ-string codec actually consumed by
Lean Live; the visually similar URI-safe codec is incompatible and can silently
corrupt otherwise valid theorem text.

Six previously repaired prime-theorem prerequisites were individually
recompiled successfully as fully readable, fallback-free proof strands:

1. `divisor_le_nonzero` (2 proof nodes).
2. `multiple_has_zero_remainder` (2 proof nodes).
3. `prime_nonzero` (3 proof nodes).
4. `mul_eq_one_components` (4 proof nodes).
5. `factor_difference` (7 proof nodes).
6. `divides_remainder` (10 proof nodes).

The small Stable theorem `multiple_zero` also now compiles without a fallback;
previously Lean's `rw` had silently closed the goal before the original `refl`.

Five more previously certificate-backed campaign prerequisites were each
compiled independently as complete, import-free, fallback-free Lean proofs:

1. `lt_not_le` (1 proof node).
2. `lt_not_eq_add_middle` (2 proof nodes).
3. `division_remainder_exists` (5 proof nodes).
4. `inverse_prefix_entry_sound` (17 proof nodes).
5. `gcd_balanced_bezout_exists_up_to` (29 proof nodes).

The newly introduced Alpha-v21 theorem `euclidean_division_step_exists` also
compiles as a complete six-theorem standalone proof. Its 6,575-byte Lean
source and 3,792-byte verified Lean Live link include the repaired
`division_remainder_exists` dependency and no certificate fallback.

The originally blocked current Alpha-v21 campaign theorem
`prime_inverse_prefix_fixed_cases` now passes the complete browser-service
acceptance test with **66 named theorem nodes, 130 dependency edges, 1,483
original tactic decisions, and zero certificate fallbacks**. Its exact
import-free standalone source is **90,110 bytes**; its authenticated official
Lean Live link is **35,565 bytes**. The same source was accepted by the real
local Lean compiler under the existing single-worker, 1,024 MiB policy.

The substantially larger Alpha-v21 theorem
`prime_choose_unused_nonendpoint_orbit` also passes the complete real
browser-service acceptance test with **159 named theorem nodes, 423 dependency
edges, 5,584 original tactic decisions, and zero certificate fallbacks**. Its
standalone Lean source is **398,596 bytes**, has no imports, and compresses to
an exact **129,151-byte official Lean Live link**. This single genuinely
compiled strand includes all eight previously failing deep prerequisites:
`binary_crt`, `beta_exclusive_recode_congruence_step`,
`finite_contains_decidable`, `finite_inverse_choice_injective`,
`beta_prefix_replace_exists`, `beta_prefix_swap_last_reflect`,
`finite_last_is_top_from_prefix_surjective`, and
`prime_inverse_prefix_nonendpoint_mate`.

Both real campaign links were additionally decoded with upstream JavaScript
`lz-string` 1.5.0; each decoded source matched its locally compiled standalone
file and authenticated SHA-256 exactly.

The current sealed Alpha-v21 catalog contains **1,830 checked theorems** and
**5,986 checked dependency edges**. All
current transitive dependency trees fit the browser's default 1,024-theorem
node budget; the largest has 557 nodes. Eighty-two roots exceed the former
256-node limit and nine exceed 512 nodes. These are graph-coverage counts,
**not** a claim that every root has a completely reconstructed standalone Lean
proof: deeper campaign strands can still contain explicit certificate-backed
nodes, and very large sources can exceed their separate reviewed byte limit.
For example, an independently checked 148-node four-square strand still has
three honest certificate fallbacks (`odd_add_odd`,
`two_square_absolute_difference_square_balance`, and
`four_square_descent_double_pair_identity`). Lean Live remains unavailable
whenever such a node or a source-limit failure prevents a genuinely
self-contained, independently compiled proof.
