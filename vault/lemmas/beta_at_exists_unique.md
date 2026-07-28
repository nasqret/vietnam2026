---
title: "Lemma: beta_at_exists_unique"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_at_exists_unique`

Every Gödel-beta position has exactly one decoded residue.

## Closed Peano statement

```text
forall b c i. exists x. (((exists h. h + S x = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + x) /\ forall y. ((exists h. h + S y = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + y) -> x = y)
```

## Dependencies

- [[beta_at_exists]]
- [[beta_at_unique]]

## Checked dependents

- No checked theorem currently depends on this node.

## Verification record

- Independently checked from the empty context.
- Certificate: **1625 nodes**, depth **61**.
- Authored script length: **22 commands**.
- Runtime card: `pa lib beta_at_exists_unique`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
