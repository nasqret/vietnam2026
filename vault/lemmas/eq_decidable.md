---
title: "Lemma: eq_decidable"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `eq_decidable`

Equality of natural numbers is constructively decidable.

## Closed Peano statement

```text
forall a b. a = b \/ ~(a = b)
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[multiple_decidable_nonzero]]
- [[multiple_decidable]]
- [[factor_search_up_to]]
- [[prime_decidable]]
- [[prime_factorization_exists_up_to]]
- [[mod_eq_decidable_from_remainders]]
- [[beta_prefix_swap_last_reflect]]
- [[finite_swap_last_bounded]]
- [[finite_contains_decidable]]
- [[beta_prefix_replace_reflect]]

## Verification record

- Independently checked from the empty context.
- Certificate: **48 nodes**, depth **20**.
- Authored script length: **27 commands**.
- Runtime card: `pa lib eq_decidable`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
