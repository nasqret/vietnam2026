---
title: "Lemma: add_right_cancel"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `add_right_cancel`

A common right addend can be cancelled.

## Closed Peano statement

```text
forall a b c. a + c = b + c -> a = b
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[add_left_cancel]]
- [[add_le_cancel_right]]
- [[mul_left_cancel_nonzero]]

## Verification record

- Independently checked from the empty context.
- Certificate: **41 nodes**, depth **15**.
- Authored script length: **13 commands**.
- Runtime card: `pa lib add_right_cancel`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
