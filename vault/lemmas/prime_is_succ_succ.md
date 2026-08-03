---
title: "Lemma: prime_is_succ_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_is_succ_succ`

Every prime natural is the second successor of a natural.

## Closed Peano statement

```text
forall p. ((~(p = 1) /\ forall qrbu_factor_left_prime_p qrbu_factor_right_prime_p. p = qrbu_factor_left_prime_p * qrbu_factor_right_prime_p -> qrbu_factor_left_prime_p = 1 \/ qrbu_factor_right_prime_p = 1)) -> exists k. p = S (S k)
```

## Dependencies

- [[prime_nonzero]]
- [[nonzero_is_succ]]

## Checked dependents

- [[prime_bounded_nonzero_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **98 nodes**, depth **13**.
- Authored script length: **29 commands**.
- Runtime card: `pa lib prime_is_succ_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
