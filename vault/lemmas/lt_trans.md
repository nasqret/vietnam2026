---
title: "Lemma: lt_trans"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_trans`

Strict order is transitive.

## Closed Peano statement

```text
forall a b c. (exists k. k + S a = b) -> (exists k. k + S b = c) -> exists k. k + S a = c
```

## Dependencies

- [[add_assoc]]
- [[add_succ_left]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **89 nodes**, depth **16**.
- Authored script length: **20 commands**.
- Runtime card: `pa lib lt_trans`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
