---
title: "Lemma: gcd_zero_inputs"
tags: [peano-arithmetic, checked-lemma, dependency-dag]
---

# `gcd_zero_inputs`

A zero relational gcd can divide only the zero input pair.

## Closed Peano statement

```text
forall g a b. g = 0 -> ((((exists hag_left_factor_zero_inputs. a = g * hag_left_factor_zero_inputs) /\ (exists hag_right_factor_zero_inputs. b = g * hag_right_factor_zero_inputs)) /\ forall hag_divisor_zero_inputs. (exists hag_common_left_zero_inputs. a = hag_divisor_zero_inputs * hag_common_left_zero_inputs) -> (exists hag_common_right_zero_inputs. b = hag_divisor_zero_inputs * hag_common_right_zero_inputs) -> exists hag_greatest_factor_zero_inputs. g = hag_divisor_zero_inputs * hag_greatest_factor_zero_inputs)) -> (a = 0 /\ b = 0)
```

## Dependencies

- [[mul_zero_left]]

## Checked dependents

- [[gcd_lcm_compatible_exists]]

## Verification record

- Independently checked from the empty context.
- Certificate: **62 nodes**, depth **21**.
- Authored script length: **18 commands**.
- Runtime card: `pa lib gcd_zero_inputs`.
- Book route: *The dependency ladder* in the foundational arithmetic part.

## Related

[[arithmetic-library-moc]] · [[theorem-ladder]] · [[proof-certificate]] ·
[[checked-theorem-reuse]]
