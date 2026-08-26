---
title: "Lemma: drop_add_prefix_from_fixed"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `drop_add_prefix_from_fixed`

A fixed-point equation remains fixed after dropping an additive prefix.

## Closed Peano statement

```text
forall a b n. (b + a) + n = n -> a + n = n
```

## Dependencies

- [[zero_add]]
- [[add_succ_left]]
- [[no_succ_add_fixed]]

## Checked dependents

- [[antisymm_from_witnesses]]

## Verification record

- Independently checked from the empty context.
- Certificate: **120 nodes**, depth **22**.
- Authored script length: **17 commands**.
- Runtime card: `pa lib drop_add_prefix_from_fixed`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
