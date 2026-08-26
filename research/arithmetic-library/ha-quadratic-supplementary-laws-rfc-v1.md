# Constructive quadratic supplementary laws RFC v1

Status: isolated, intuitionistic proof-body candidates. No theorem in this
document has been enrolled, admitted for checked use, promoted, or presented
as an independently closed empty-context certificate.

Date: 2026-08-23.

## Mathematical contracts and representation

All predicates below are conservative abbreviations for formulas in the
unchanged first-order Peano language `{0, S, +, *, =}`. In particular, the
natural predecessor `n` in `p = S n` is the canonical representative of `-1`
modulo `p`; no negative-integer primitive or classical principle is added.

The complete first supplementary law is:

```text
p = S n -> Prime(p) -> Odd(p) ->
  ((QRes(p,n) <-> exists a. p = 4*a + 1) /\
   (~QRes(p,n) <-> exists a. p = 4*a + 3)).
```

The complete second supplementary law is:

```text
Prime(p) -> Odd(p) ->
  ((QRes(p,2) <-> (p = 1 mod 8 \/ p = 7 mod 8)) /\
   (~QRes(p,2) <-> (p = 3 mod 8 \/ p = 5 mod 8))).
```

Both complete endpoints now have independently kernel-checked,
dependency-curried intuitionistic proof bodies. Neither endpoint has yet
undergone standalone empty-context closure or Alpha/Stable admission.

## First supplementary law: complete dependency-curried proof

Implementation:
[`quadratic_supplement_minus_one_candidate.py`](../../peano-lab/py/peano_lab/library/quadratic_supplement_minus_one_candidate.py).
Focused audit:
[`test_quadratic_supplement_minus_one_candidate.py`](../../peano-lab/py/tests/test_quadratic_supplement_minus_one_candidate.py).

The exact candidate order is:

1. `prime_predecessor_nonzero`;
2. `odd_predecessor_double_half`;
3. `quadratic_supplement_minus_one_half_parity`;
4. `quadratic_supplement_minus_one_residue_iff_mod_four_one`;
5. `quadratic_supplement_minus_one_nonresidue_iff_mod_four_three`;
6. `quadratic_supplement_minus_one_complete`.

The predecessor-power parity bridge and bounded Euler criterion give the
residue/even-half and nonresidue/odd-half implications. The existing exact
half-parity/modulo-four bridges then produce both residue classes. The
positive branch contains an existential square-root witness; the negative
branch supplies an actual intuitionistic obstruction.

The six checked proof bodies have respectively `22`, `51`, `236`, `69`, `72`,
and `38` structural nodes. Their maximum proof depth is `35`. The exact
first-law endpoint statement has SHA-256
`7ea81062b843e7fff4939ffce5b6fa14a87312619f7f49e3abd5993bfa02134e`.
All bodies are `DNE`-free and are checked against their dependency-curried
targets by the unchanged kernel.

## Second supplementary law: complete constructive modulo-eight proof

Implementation:
[`quadratic_supplement_two_candidate.py`](../../peano-lab/py/peano_lab/library/quadratic_supplement_two_candidate.py).
Focused audit:
[`test_quadratic_supplement_two_candidate.py`](../../peano-lab/py/tests/test_quadratic_supplement_two_candidate.py).

The 22 completed dependency-curried candidates are:

1. `eight_mul_eq_double_four`;
2. `odd_mod_eight_cases`;
3. `doubling_gauss_count_shape_exists`;
4. `mod_eight_remainder_unique`;
5. `mod_eight_good_bad_exclusive`;
6. `doubling_gauss_even_count_implies_good_mod_eight`;
7. `doubling_gauss_odd_count_implies_bad_mod_eight`;
8. `doubling_gauss_count_parity_mod_eight_complete`;
9. `doubling_floor_below_implies_double_at_most_half`;
10. `doubling_floor_above_implies_double_above_half`;
11. `doubling_half_range_below_odd_modulus`;
12. `reflected_double_above_odd_half`;
13. `doubling_gauss_initial_segment_complement`;
14. `doubling_half_decomposition_lower_bound`;
15. `doubling_gauss_count_shape_from_initial_segment_complement`;
16. `doubling_gauss_reflection_count_shape`;
17. `quadratic_supplement_two_conditional_on_gauss_count_shape`;
18. `odd_prime_strictly_exceeds_two`;
19. `quadratic_supplement_two_half_complete`;
20. `quadratic_supplement_two_residue_iff_mod_eight_one_or_seven`;
21. `quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five`;
22. `quadratic_supplement_two_complete`.

For `p = 2*h + 1`, the explicit doubling-reflection count has the shape:

```text
DoublingCountShape(h,e) :=
  h = 2*e \/ (exists k. h = 2*k + 1 /\ e = S k).
```

The completed arithmetic proves that this count is even exactly when `p` is
`1` or `7` modulo eight, and odd exactly when it is `3` or `5` modulo eight.
An intermediate, separately checked conditional classifier proves:

```text
p = 2*h + 1 -> Prime(p) -> DoublingCountShape(h,e) ->
  ((QRes(p,2) <-> Even(e)) /\ (~QRes(p,2) <-> Odd(e))) ->
  ((QRes(p,2) <-> GoodModEight(p)) /\
   (~QRes(p,2) <-> BadModEight(p))).
```

The actual reflection-count identification is also proved. Four explicit
order/sign lemmas and `odd_signed_division_branch_exact` identify each actual
Gauss sign as the complement of its beta-coded floor-half initial-segment
indicator. The exact pointwise complement theorem has statement SHA-256
`4e82078fb10ab261cc9516669ba89357c4c4335a20f074465a5e069cc207bd5b`
and a 296-node proof body of depth 57. Existing exact initial-segment and
complementary `BitCount` identities then prove that **the same actual Gauss
count** satisfies `DoublingCountShape(h,e)`. The complete count-shape
theorem has statement SHA-256
`8681aaac3169a14ae1dae90e15bf11ed5fed927cfd16cee2b4bed91326c796bd`
and a 68-node proof body of depth 42.

The exact intermediate conditional classifier has SHA-256
`65abe8256615b1b0e6d5a71c4074c9c44d8d450957edf30cda4f59b253db2471`.
The unconditional `quadratic_supplement_two_half_complete` endpoint invokes
the existing bounded Gauss lemma at multiplier two, constructs its actual
beta-coded half-range, proves `2 < p`, extracts the genuine signed-prefix
count, applies the now-proved count-shape theorem, and discharges the
conditional classifier without any additional assumption.

The exact public-shaped residue endpoint has SHA-256
`df55b1cd3398dc6bf064dc8957ea318ad311b99ebf1b3ecffb804b463c1df532`
and a 17-node body. The complementary nonresidue endpoint has SHA-256
`dd9b0415da856a4198e7eb027d2c055549bc34588378d301a952748eaeb80877`
and a 17-node body. Their complete conjunction has SHA-256
`146a886f8f3a54d358321b54faf68a591362016e86139bd487a5496c7af74034`
and a 24-node body. Its exact prefix is
`forall p. Prime(p) -> Odd(p) -> ...`, with all predicates expanded.

## Admission and next gate

Both source factories remain absent from the public theorem registry and
sealed Alpha/Stable catalogs. Their focused audits pin exact statements,
dependency order, proof receipts, negative mutations, absence of `DNE`, and
independent numerical examples.

There is no remaining mathematical premise or reflection-count gap in either
supplementary law. Standalone closure, cold replay, mutation/provenance
gates, additive Alpha enrollment, proof-explorer publication, and possible
Stable promotion remain separate subsequent operations. In particular, the
existence of a complete dependency-curried body does not upgrade the evidence
label of any sealed ancestor or confer checked-use authority.
