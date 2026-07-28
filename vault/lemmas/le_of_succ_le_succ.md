---
title: "Lemma: le_of_succ_le_succ"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `le_of_succ_le_succ`

Successor order reflects to the underlying naturals.

## Closed Peano statement

```text
forall a b. (exists k. k + S a = S b) -> exists r. r + a = b
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[gcd_exists_up_to]]
- [[gcd_balanced_bezout_exists_up_to]]

## Verification record

- Independently checked from the empty context.
- Certificate: **16 nodes**, depth **11**.
- Authored script length: **10 commands**.
- Runtime card: `pa lib le_of_succ_le_succ`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
