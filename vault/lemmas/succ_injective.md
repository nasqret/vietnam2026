---
title: "Lemma: succ_injective"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `succ_injective`

Successor is injective (the reusable PA2 lemma).

## Closed Peano statement

```text
forall n m. S n = S m -> n = m
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[not_qres_mod3_two]]
- [[not_qres_mod5_two]]
- [[not_qres_mod5_three]]
- [[not_qres_mod7_three]]
- [[not_qres_mod7_five]]
- [[not_qres_mod7_six]]

## Verification record

- Independently checked from the empty context.
- Certificate: **1 nodes**, depth **1**.
- Authored script length: **1 commands**.
- Runtime card: `pa lib succ_injective`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
