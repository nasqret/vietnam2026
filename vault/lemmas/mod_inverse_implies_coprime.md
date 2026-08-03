---
title: "Lemma: mod_inverse_implies_coprime"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `mod_inverse_implies_coprime`

Any natural modular inverse forces coprimality, without a nonzero-modulus side condition.

## Closed Peano statement

```text
forall a m z. (exists hmi_left_offset_converse_assumption hmi_right_offset_converse_assumption. a * z + m * hmi_left_offset_converse_assumption = 1 + m * hmi_right_offset_converse_assumption) -> (forall hmi_divisor_converse_result. (exists hmi_left_factor_converse_result. a = hmi_divisor_converse_result * hmi_left_factor_converse_result) -> (exists hmi_right_factor_converse_result. m = hmi_divisor_converse_result * hmi_right_factor_converse_result) -> hmi_divisor_converse_result = 1)
```

## Dependencies

- [[common_divisor_divides_balanced_result]]
- [[zero_add]]
- [[divisor_one]]

## Checked dependents

- [[coprime_iff_unique_bounded_mod_inverse]]

## Verification record

- Independently checked from the empty context.
- Certificate: **874 nodes**, depth **40**.
- Authored script length: **36 commands**.
- Runtime card: `pa lib mod_inverse_implies_coprime`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
