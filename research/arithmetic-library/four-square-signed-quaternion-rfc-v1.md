# Constructive signed quaternion descent

Centered modular representatives have four independent sign choices. Natural
Hamilton coordinates handle the odd-parity sign patterns, while independently
checked conjugate coordinates handle the even-parity patterns. All relations
below expand into the existing first-order Heyting arithmetic language; no
signed integer, subtraction, division, or choice primitive is added.

The isolated `make_four_square_signed_quaternion_candidate_theorems` factory
contains **28 independently kernel-checked dependency-curried candidate
bodies**. They prove:

- Positive and negative centered coordinate orientations, squared congruence,
  and all-sign congruence of the original and centered four-square norms.
- The genuine witnessed centered quotient: if `p*k` is the original
  four-square norm, all four centered remainders satisfy
  `exists r. k*r = e²+f²+g²+h²`, uniformly across all sixteen sign patterns.
- Constructive same-sign crossed-product congruence, mixed-sign cancellation,
  subtraction-free vanishing-block aggregation, and positive/negative
  dot-product partition balance.
- Three complete four-coordinate canonical modular balance certificates:
  all-positive conjugate coordinates; two-negative/two-positive conjugate
  coordinates with the essential reversed second input `(h,g,f,e)`; and
  negative-first natural Hamilton coordinates.

The two complementary canonical sign patterns live in the separately checked
negative-block candidate factory. Together their five canonical patterns cover
all sixteen orientations under constructive coordinate permutations.

Pinned statement SHA-256 receipts:

```text
centered_norm_quotient_exists
  3a3cd289475188f620ddc67826f18afb20f44646d6db3ca2f849fbd473e4bab5
conjugate_positive_blocks
  6a03706d5246dd92b6b79d801db89fb44a839cc9f374c56d1eae081f8eb8671a
conjugate_mixed_blocks
  a397c4c916e5cbf73d104a5172929602adccd7a2b229b2203d35a9014e006dbd
natural_negative_first_blocks
  30f8f87ffcb55fd6256addc01195d5e190a15492af577027211bed79380f3f4f
```

Focused verification is bounded to the signed-quaternion suite; the theorem
bodies remain registry-isolated and grant neither Alpha nor Stable admission.
Any universal four-square endpoint belongs to a separately assembled and
independently kernel-checked candidate theorem.
