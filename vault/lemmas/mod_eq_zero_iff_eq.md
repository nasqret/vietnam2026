---
title: "Lemma: mod_eq_zero_iff_eq"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_zero_iff_eq`

Balanced congruence modulo zero is exactly equality.

## Closed Peano statement

```text
forall a b. (((exists hgcrt_mod_left_zero_source hgcrt_mod_right_zero_source. a + 0 * hgcrt_mod_left_zero_source = b + 0 * hgcrt_mod_right_zero_source) -> a = b) /\ (a = b -> (exists hgcrt_mod_left_zero_result hgcrt_mod_right_zero_result. a + 0 * hgcrt_mod_left_zero_result = b + 0 * hgcrt_mod_right_zero_result)))
```

## Dependencies

- [[mul_zero_left]]

## Checked dependents

- [[crt_solution_unique_lcm_zero]]
- [[mod_eq_decidable]]

## Verification record

- Independently checked from the empty context.
- Certificate: **55 nodes**, depth **13**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib mod_eq_zero_iff_eq`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
