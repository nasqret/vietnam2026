---
title: "Lemma: prime_ne_two_is_odd"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `prime_ne_two_is_odd`

Every prime other than two is odd.

## Closed Peano statement

```text
forall p. (~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) -> ~(p = 2) -> exists h. p = 2 * h + 1
```

## Dependencies

- [[parity_cases]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **139 nodes**, depth **20**.
- Authored script length: **25 commands**.
- Runtime card: `pa lib prime_ne_two_is_odd`.
- Book route: *The quadratic-reciprocity campaign* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
