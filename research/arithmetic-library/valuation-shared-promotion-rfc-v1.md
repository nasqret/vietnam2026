# Bounded shared closure of constructive power valuations

## Previously audited obstruction

The original sealed Alpha-v12 ledger contains the two body-only roots
`bounded_power_valuation_exists` and `power_valuation_exists`. Their exact
statements, scripts, enrollment positions, and dependency edges are unchanged.

The bounded root takes independently closed direct premises
`bounded_power_valuation_search` and `power_divides_zero`. Their ordinary
certificates have 64,301 and 61,118 structural nodes, respectively; composing
them separately yields an exact 125,454-node proof. The canonical successor
requires 125,470 nodes. Both exceed the unchanged 125,000-node constructive
microbatch ceiling.

The apparent obstruction is duplicated evidence, not missing mathematics:
both branches contain the same actual 59,836-node Stable `pow_exists` proof.

## Exact shared proof graph

Eleven actual Stable-closed leaves are retained in sealed dependency order:

```text
le_refl
zero_le
le_zero
le_of_succ_le_succ
le_succ
le_eq_or_lt
one_multiple
multiple_decidable
pow_exists
pow_zero
pow_functional
```

Together these genuine empty-context certificates have 65,364 structural
occurrences and 7,956 separately counted proof objects. The contextual bodies
are the exact original dependency-curried Alpha scripts:

```text
power_divides_decidable
power_divides_zero
bounded_power_valuation_search
bounded_power_valuation_exists
[power_valuation_exists]
```

Ordinary unchanged layered `Cut` nodes discharge `pow_exists` once. The bounded
graph therefore has 15 total nodes; the canonical graph has exactly 16. No
kernel axiom, proof constructor, classical principle, oracle, unchecked
theorem reference, or resource ceiling is added.

## Independently kernel-checked outcomes

| Original root | Previous structural nodes | Shared structural nodes | Distinct proof objects | Proof depth |
| --- | ---: | ---: | ---: | ---: |
| `bounded_power_valuation_exists` | 125,454 | 65,708 | 5,952 | 92 |
| `power_valuation_exists` | 125,470 | 65,727 | 5,971 | 92 |

Both resulting ordinary certificates are checked from the empty context by the
unchanged intuitionistic kernel against their exact sealed original formulas.
Both satisfy the immutable 125,000-node, 25,000-object, and 16-row bounds.

This engineering tranche **does not change** Stable membership, Alpha release
evidence, checked-use authority, or any immutable historical artifact.
Subsequent dependency-closed release promotion remains a separately audited
operation.
