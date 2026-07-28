---
title: "Lemma: add_comm"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_comm`

Addition is commutative.

## Closed Peano statement

```text
forall n m. n + m = m + n
```

## Dependencies

- [[zero_add]]
- [[add_succ_left]]

## Checked dependents

- [[mul_succ_left]]
- [[add_left_cancel]]
- [[add_eq_zero_left]]
- [[add_residue_lift]]

## Verification record

- Independently checked from the empty context.
- Certificate: **67 nodes**, depth **17**.
- Authored script length: **4 commands**.
- Runtime card: `pa lib add_comm`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
