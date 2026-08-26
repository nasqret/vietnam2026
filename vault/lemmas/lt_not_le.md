---
title: "Lemma: lt_not_le"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `lt_not_le`

A strict inequality excludes the reverse weak inequality.

## Closed Peano statement

```text
forall a b. (exists k. k + S a = b) -> ~ (exists k. k + b = a)
```

## Dependencies

- None; the script closes directly from PA rules.

## Checked dependents

- [[le_not_lt]]
- [[prime_bounded_nonzero_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **56 nodes**, depth **23**.
- Authored script length: **34 commands**.
- Runtime card: `pa lib lt_not_le`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
