# Alpha v19: complete constructive closure and four new mathematical fronts

## Immutable parent, Stable boundary, and unchanged kernel

Alpha v19 preserves all 1,673 exact Alpha-v18 theorem names, statements,
authored tactic scripts, original dependency lists, enrollment positions,
membership, and provenance. Its default public Stable edition remains the
same immutable 432-theorem checked library. Nothing in this release promotes
an Alpha-only result into Stable or changes the intuitionistic kernel, base
signature, induction principle, canonical proof codec, Lean checker, or any
existing proof/resource limit.

The immutable Alpha-v18 parent is bound by these exact SHA-256 digests:

| Parent artifact | SHA-256 |
| --- | --- |
| Alpha v18 catalog | `cfbaeaf5d89be609d09aa2b84c9d102297a45b7b6aeeea6efcd32b1b328e62b2` |
| Alpha v18 metrics | `da634d4995fa83296ec7458bd7aad0f1da40b39f3ed0be583c3dc01a3d498a77` |
| Alpha v18 dependency graph | `5729b4818862bc880f01c30ece70025e6dc25c3bf47d472ebf9dcac3de3d4f69` |
| Alpha v18 channels | `1d9c81c2d8a1ed9f1fb28af8b2e05e9cd130789daa10367f5ef2ef3a27b505d8` |

The parent edition identity is
`f694881096fd09b1002d0d49bb7be2d68d9894457749ef04128deebd92a64f66`.

## Every historical proof obligation is independently closed

Precisely 84 existing Alpha-v18 rows were previously `body_checked`: 17
cell-list infrastructure results and 67 auxiliary Bertrand results. Their
exact dependency closure has 474 theorem nodes and 1,412 real dependency
arrows. A balanced synthetic conjunction connects its 40 maximal theorem
roots, producing one independently kernel-checked self-contained proof bundle
with 475 ordinary proof bodies and 1,452 dependency edges.

The canonical residual artifact contains 38,688 structural body-proof nodes,
occupies 4,176,537 bytes, and has SHA-256
`e69112c5e3b8c21bc452ad35838474f2af2e297152ff73fbdc62bfd935ffdebb`.
The independent compiled Lean proof-bundle checker accepts every body. Its
111 previously unavailable proof bodies are reconstructed in unchanged
bounded microbatches; 363 parent bodies are preserved or obtained from
already checked immutable artifacts.

One historical auxiliary script, `pow_two_seven_exact`, has an authoring
envelope too deep for the unchanged certificate limit. The proof artifact
therefore replaces only two frozen long numeral rewrite blocks by the
existing, unchanged-kernel-checked `norm_num` tactic. Its exact historical
statement, dependency list, enrollment, and authored script remain immutable;
the replacement ordinary body has depth 142 and combined envelope depth 203,
strictly below the unchanged depth limit of 256.

The ordered 84 promotion names have SHA-256
`0fd3159925c12b2e7249edb5d536f3be600e466e5a6695350a22c38e81d4f69e`.
In particular, both exact prime-specific valuation wrappers
`prime_power_valuation_exists` and `prime_power_valuation_functional` become
independently checked, completing the previously partial shared T09
prime-valuation interface.

## Exactly 64 newly proved constructive campaign theorems

The additive frontier is fixed in strict predecessor-before-successor order:

1. **Primitive Pythagorean forward construction:** 44 exact independently
   checked theorem bodies, including
   `pythagorean_primitive_euclidean_from_order` and
   `pythagorean_primitive_normal_form`. These close the constructive forward
   anchor only. The inverse classification and unconditional Fermat
   exponent-four descent remain open.
2. **Prime two-square classification:** the exact additional theorem
   `prime_is_two_squares_iff_two_or_one_mod_four`. It packages both directions
   of Fermat's prime two-square criterion as one independently checked
   theorem and closes campaign goal G061.
3. **Complete linear congruences:** nine newly proved theorem bodies. The
   endpoint `linear_congruence_solvable_iff_gcd_divides` constructs a bounded
   least-residue solution for each nonzero modulus exactly when the supplied
   gcd divides the target. Separate exact theorems cover all moduli, zero
   modulus, constructive certified decision, and uniqueness for coprime
   coefficients. Every external prerequisite is already Stable-checked.
4. **Infinitely many primes one modulo four:** ten newly proved theorem
   bodies culminating in `infinitely_many_primes_one_mod_four`, the exact
   intuitionistic first-order statement
   `forall B. exists p. Prime(p) /\ B<p /\ exists k. p=4*k+1`.
   The constructive argument chooses a bounded common multiple `C`, extracts
   a prime divisor of `4*C*C+1`, proves it is neither two nor three modulo
   four, and excludes every prime at most `B`. It does not assume or require
   infinitude of primes three modulo four.

The ordered 64 new theorem names have SHA-256
`07b9c92ab3ef80dc609681a9b588d21b0faeb69e87448c1420b78272a54aaed1`.
All new statements are exact first-order formulas over Heyting arithmetic;
every introduced definition remains conservative and every proof is checked
by the unchanged original kernel without classical excluded middle, a search
oracle, a new axiom, or `sorry`.

## Resulting exact immutable edition

| Evidence | Immutable Alpha v18 | Constructive Alpha v19 |
| --- | ---: | ---: |
| `stable_closed` | 432 | 432 |
| `alpha_closed` | 1,157 | 1,305 |
| `body_checked` | 84 | 0 |
| Independently checked-use theorems | 1,589 | 1,737 |
| Enrolled theorem specifications | 1,673 | 1,737 |
| Direct dependency arrows | 5,615 | 5,779 |
| Dependency layers | 53 | 53 |

The exact Alpha-v19 ordered enrollment identity is
`1295d6fc3da84646cb6bc8d5070627d42a6df33d673c44a2adfcd433edc41795`.
Its full checked evidence identity is
`905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7`.
All 1,737 theorem nodes and all 5,779 prerequisite arrows belong to the
closed checked-use dependency graph; the historical whole-edition closure
gate therefore passes for the first time, without promoting Alpha to Stable.

The independent reproducibility and mutation gates are:

```text
make peano-library-alpha-v19
make peano-library-alpha-v19-check
```
