---
title: "Lemma: beta_value_le_code"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `beta_value_le_code`

Every decoded beta value is at most its code.

## Closed Peano statement

```text
forall b c i x. ((exists h. h + S x = S ((S i) * c)) /\ exists q. b = q * S ((S i) * c) + x) -> exists h. h + x = b
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[beta_value_lt_scaled_base]]

## Verification record

- Independently checked from the empty context.
- Certificate: **18 nodes**, depth **13**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib beta_value_le_code`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
