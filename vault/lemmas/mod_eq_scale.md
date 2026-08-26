---
title: "Lemma: mod_eq_scale"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_eq_scale`

Scaling values and their modulus preserves balanced congruence.

## Closed Peano statement

```text
forall k m a b. (exists hgcrt_mod_left_scale_source hgcrt_mod_right_scale_source. a + m * hgcrt_mod_left_scale_source = b + m * hgcrt_mod_right_scale_source) -> (exists hgcrt_mod_left_scale_result hgcrt_mod_right_scale_result. (k * a) + (k * m) * hgcrt_mod_left_scale_result = (k * b) + (k * m) * hgcrt_mod_right_scale_result)
```

## Dependencies

- [[mul_add]]
- [[mul_assoc]]

## Checked dependents

- [[crt_scaled_common_remainder_lift]]

## Verification record

- Independently checked from the empty context.
- Certificate: **235 nodes**, depth **21**.
- Authored script length: **26 commands**.
- Runtime card: `pa lib mod_eq_scale`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
